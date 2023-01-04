# Copyright (C) 2018 Leiden University Medical Center
# This file is part of pytest-workflow
#
# pytest-workflow is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# pytest-workflow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with pytest-workflow.  If not, see <https://www.gnu.org/licenses/

"""core functionality of pytest-workflow plugin"""
import argparse
import os
import shutil
import tempfile
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest

import yaml

from .content_tests import ContentTestCollector
from .file_tests import FileTestCollector
from .schema import WorkflowTest, workflow_tests_from_schema
from .util import duplicate_tree, is_in_dir, replace_whitespace
from .workflow import Workflow, WorkflowQueue


def pytest_addoption(parser: pytest.Parser):
    parser.addoption(
        "--kwd", "--keep-workflow-wd",
        action="store_true",
        help="Keep temporary directories where workflows are run for "
             "debugging purposes. This also triggers saving of stdout and "
             "stderr in the workflow directory.",
        dest="keep_workflow_wd")
    parser.addoption(
        "--kwdof", "--keep-workflow-wd-on-fail",
        action="store_true",
        help="Similar to --keep-workflow-wd, but only keeps the temporary "
             "directories if there are test failures. On success all "
             "directories are deleted.",
        dest="keep_workflow_wd_on_fail")
    parser.addoption(
        "--wt", "--workflow-threads",
        dest="workflow_threads",
        default=1,
        type=int,
        help="The number of workflows to run simultaneously.")
    parser.addoption(
        "--symlink", action="store_true",
        help="Instead of copying the current working directory, create a "
             "similar directory structure where all files are replaced with "
             "symbolic links. This saves disk space, but should only be used "
             "for tests that do use these files read-only."
    )
    parser.addoption(
        "--ga", "--git-aware", action="store_true", dest="git_aware",
        help="Only copy files that are listed by the 'git ls-files' command. "
             "This ignores the .git directory, any untracked files and any "
             "files listed by .gitignore. "
             "Highly recommended when working in a git project.")
    parser.addoption(
        "--sb", "--stderr-bytes",
        dest="stderr_bytes",
        default=1000,
        type=int,
        help="The number of bytes to display from the stderr and "
             "stdout on exitcode.")
    # Why `--tag <tag>` and not simply use `pytest -m <tag>`?
    # `-m` uses a "mark expression". So you have to type a piece of python
    # code instead of just supplying the tags you want. This is fine for the
    # user interface. But this is not fine for the plugin implementation. If
    # `-m` is used we need to evaluate the mark expression and make sure it
    # applies to the marks of the workflow. This requires reusing of the pytest
    # code, which is a hell to implement.
    # Additionally, markers can not have whitespace. So using the name of a
    # workflow as a default tag is not possible. Unless you first replace
    # whitespace for both command line and the test_.yml to make sure the marks
    # are correct. This is non-trivial. Alternatively, the schema could not
    # allow whitespace in names. That is just being plain annoying to the user
    # for no good reason. Maybe the user does not want to use tags, and then it
    # is extra hassle for a feature that is not even used.
    # So using pytest `-m` to select workflows is an implementation nightmare.
    # `--tag` is an easier solution.
    parser.addoption(
        "--tag",
        dest="workflow_tags",
        action="append",
        type=str,
        # Otherwise default is None and this does not work with list operations
        default=[],
        help="Run workflows with this name or tag."
    )


def __pytest_workflow_cli():  # pragma: no cover
    """Helper function for showing all pytest-workflow specific options in the
    documentation with sphinx argparse. The ArgParser class bypasses any
    pytest specific implementation of the PytestParser to use a common
    argparse.ArgumentParser instead."""
    class ArgParser(argparse.ArgumentParser):
        def addoption(self, *args, **kwargs):
            self.add_argument(*args, **kwargs)

    parser = ArgParser()
    pytest_addoption(parser)
    return parser


def pytest_collect_file(file_path, path, parent):
    """Collection hook
    This collects the yaml files that start with "test" and end with
    .yaml or .yml"""
    if path.ext in [".yml", ".yaml"] and path.basename.startswith("test"):
        return YamlFile.from_parent(parent, path=file_path)
    return None


def pytest_configure(config: pytest.Config):
    """This runs before tests start and adds values to the config."""

    #  Add marker to the config to prevent issues caused by:
    #  https://github.com/pytest-dev/pytest/issues/4826
    # Errors are now emitted when unknown marks are included
    config.addinivalue_line(
        "markers",
        "workflow('name', 'name2', ...): mark test to run only with the given "
        "workflow name or names. Also provides access to the workflow_dir "
        "fixture."
    )
    # We need to add a workflow queue to some central variable. Instead of
    # using a global variable we add a value to the config.
    # Using setattr is not the nicest way of doing things, but having something
    # in the globally used config is the easiest and least hackish way to get
    # this going.
    workflow_queue = WorkflowQueue()
    setattr(config, "workflow_queue", workflow_queue)

    # Save which workflows are run and which are not.
    executed_workflows: Dict[str, str] = {}
    setattr(config, "executed_workflows", executed_workflows)

    # Save workflow for cleanup in this var.
    workflow_cleanup_dirs: List[str] = []
    setattr(config, "workflow_cleanup_dirs", workflow_cleanup_dirs)

    # When multiple workflows are started they should all be set in the same
    # temporary directory
    # Running in a temporary directory will prevent the project repository
    # from getting filled up with test workflow output.
    # The temporary directory is produced using the tempfile stdlib.
    # If a basetemp is set by the user this is used as the temporary
    # directory.
    # Alternatively self.config._tmp_path_factory.getbasetemp() could be used
    # to create temporary dirs. But the comments in the pytest code
    # discourage this. Furthermore this creates directories in the following
    # form: `/tmp/pytest-of-$USER/pytest-<number>`. The number is generated
    # by pytest itself and increments each run. A maximum of 3 folders can
    # coexist. When more are detected, pytest will delete the oldest folders.
    # This can create problems when more than three instances of pytest with
    # pytest-workflow run under the same user. This is not uncommon in CI.
    # So this is why the native pytest `tmpdir` fixture is not used.

    basetemp = config.getoption("basetemp")
    workflow_temp_dir = (
        Path(basetemp) if basetemp is not None
        else Path(tempfile.mkdtemp(prefix="pytest_workflow_")))

    # Raise an error if the workflow temporary directory of the rootpath
    # (pytest's CWD). This will lead to infinite looping and copying.
    if is_in_dir(workflow_temp_dir, config.rootpath):
        raise ValueError(f"'{workflow_temp_dir}' is a subdirectory of "
                         f"'{config.rootpath}'. Please select a --basetemp "
                         f"that is not in pytest's current working directory.")

    setattr(config, "workflow_temp_dir", workflow_temp_dir)


def pytest_collection():
    """This function is started at the beginning of collection"""
    # We print an empty line here to make the report look slightly better.
    # Without it pytest will output "Collecting ... " and the workflow commands
    # will be immediately after this: "Collecting ... queue (etc.) "
    # the prevent provides a newline. So it will look like:
    # Collecting ...
    # queue (etc.)
    print()


def get_workflow_names_from_workflow_marker(marker: pytest.Mark
                                            ) -> Tuple[Any, ...]:
    if 'name' in marker.kwargs:
        raise DeprecationWarning(
            "Using pytest.mark.workflow(name='workflow name') is "
            "deprecated. Use pytest.mark.workflow('workflow_name') "
            "instead.")
    return marker.args


def pytest_generate_tests(metafunc: pytest.Metafunc):
    """
    This runs at the end of the collection phase. We use this hook to generate
    the workflow_dir fixtures for custom test functions.
    :param metafunc: A function before it is fully parametrized.
    :return: None
    """
    # If workflow_dir is not present we do not need to parametrize it.
    if "workflow_dir" not in metafunc.fixturenames:
        return

    # Technically definition is of type FunctionDefinition, but that is a
    # subclass of Function and FunctionDefinition cannot be accessed through
    # the API.
    definition: pytest.Function = metafunc.definition
    marker: Optional[pytest.Mark] = definition.get_closest_marker("workflow")
    if marker is None:
        raise ValueError("workflow_dir can only be requested in tests marked"
                         " with the workflow mark.")

    workflow_names = get_workflow_names_from_workflow_marker(marker)
    if not workflow_names:
        raise ValueError(f"A workflow name or names should be defined in "
                         f"the workflow marker of {definition.nodeid}")

    workflow_temp_dir = metafunc.config.workflow_temp_dir  # type: ignore
    workflow_dirs = [Path(workflow_temp_dir, replace_whitespace(name))
                     for name in workflow_names]
    metafunc.parametrize("workflow_dir", workflow_dirs,
                         ids=workflow_names)


def pytest_collection_modifyitems(config: pytest.Config,
                                  items: List[pytest.Function]):
    """Here we skip all tests related to workflows that are not executed"""

    for item in items:
        marker: Optional[pytest.Mark] = item.get_closest_marker("workflow")

        if marker is None:
            continue

        workflow_names = get_workflow_names_from_workflow_marker(marker)
        if len(workflow_names) == 1:
            workflow_name = workflow_names[0]
        elif "workflow_dir" in item.fixturenames:
            # nodeid looks like test_bla.py::test_bla[parametrizedvalue]
            # this parametrizedvalue should be the workflow name.
            workflow_name = item.nodeid.split('[')[-1].strip(']')
        else:
            raise NotImplementedError(f"Cannot determine workflow name for "
                                      f"{item.nodeid}")

        if workflow_name not in config.executed_workflows.keys():  # type: ignore  # noqa: E501
            skip_marker = pytest.mark.skip(
                reason=f"'{workflow_name}' has not run.")
            item.add_marker(skip_marker)


def pytest_runtestloop(session: pytest.Session):
    """This runs after collection, but before the tests."""
    session.config.workflow_queue.process(  # type: ignore
        session.config.getoption("workflow_threads")
    )


def pytest_collectstart(collector: pytest.Collector):
    """This runs before the collector runs its collect attribute"""

    if isinstance(collector, WorkflowTestsCollector):
        name: str = collector.workflow_test.name

        # Executed workflows contains workflow name as key and nodeid as value.
        executed_workflows: Dict[str, str] = (
            collector.config.executed_workflows)  # type: ignore

        if name in executed_workflows.keys():
            raise ValueError(
                f"Workflow name '{name}' used more than once. Conflicting "
                f"tests: {collector.nodeid}, {executed_workflows[name]}. "
            )


def pytest_sessionfinish(session: pytest.Session, exitstatus: int):
    directories: List[Path] = session.config.workflow_cleanup_dirs  # type: ignore # noqa: E501
    # No cleanup needed if there are no directories to cleanup. (I.e.
    # pytest-workflow plugin was not used.)
    if len(directories) == 0:
        return

    keep_workflow_wd: bool = session.config.getoption("keep_workflow_wd")
    keep_workflow_wd_on_fail: bool = session.config.getoption(
        "keep_workflow_wd_on_fail")
    no_flags = not (keep_workflow_wd_on_fail and keep_workflow_wd)
    success: bool = exitstatus == 0
    removal: bool = not (keep_workflow_wd or (keep_workflow_wd_on_fail
                                              and not success))

    remove_msg = (f"{'Removing' if removal else 'Keeping'} "
                  f"temporary directories and logs.")
    # Only print success message if removal was dependent on success.
    success_msg = (("All tests succeeded." if success else
                   "One or more tests failed.")
                   if keep_workflow_wd_on_fail else '')
    # Only print message about flags if user did not use any flags.
    no_flag_msg = ("Use '--kwd' or '--keep-workflow-wd' to disable this "
                   "behaviour." if no_flags else "")
    print(" ".join([success_msg, remove_msg, no_flag_msg]))

    if removal:
        unremovable_dirs: List[Path] = []
        for directory in directories:
            try:
                shutil.rmtree(str(directory))
            except PermissionError:
                unremovable_dirs.append(directory)
        if unremovable_dirs:
            print(f"Unable to remove the following directories due to "
                  f"permission errors: "
                  f"{' ,'.join(str(path) for path in unremovable_dirs)}.")


class YamlFile(pytest.File):
    """
    This class collects YAML files and turns them into test items.
    """
    def collect(self):
        """This function collects all the workflow tests from a single
        YAML file."""
        with self.fspath.open() as yaml_file:
            schema = yaml.safe_load(yaml_file)

        # from_parent calls the __init__ constructor indirectly. It is
        # important to name the arguments in from_parent so the __init__
        # constructor is called correctly.
        return [WorkflowTestsCollector.from_parent(parent=self,
                                                   workflow_test=test)
                for test in workflow_tests_from_schema(schema)]


class WorkflowTestsCollector(pytest.Collector):
    """This class starts all the tests collectors per workflow"""

    # The __init___ constructor is called indirectly by the `from_parent`
    # method which is builtin in any pytest Node. In order to set custom
    # attributes it is therefore still required to set up an __init__ method.
    def __init__(self, workflow_test: WorkflowTest, parent: pytest.Collector):
        self.workflow_test = workflow_test
        super().__init__(workflow_test.name, parent=parent)

        # Attach tags to this node for easier workflow selection
        self.tags = [self.workflow_test.name] + self.workflow_test.tags

    def queue_workflow(self):
        """Creates a temporary directory and add the workflow to the workflow
        queue.

        The temporary directory name is constructed from the test name by
        replacing all whitespaces with '_'. Directory paths with whitespace in
        them are very annoying to inspect.
        Tests should not have colliding names. This will lead to
        WorkflowTestCollectors with the same internal names into pytest. This
        causes pytest to crash during collection. Hence no action was taken
        to prevent name collision in temporary paths. This is handled in the
        schema instead.

        Print statements are used to provide information to the user.
        This is shorter than using pytest's terminal reporter.
        """

        tempdir = (self.config.workflow_temp_dir /
                   Path(replace_whitespace(self.name, '_')))

        # Remove the tempdir if it exists. This is needed for shutil.copytree
        # to work properly.
        if tempdir.exists():
            warnings.warn(
                f"'{tempdir}' already exists. Deleting ...")
            shutil.rmtree(str(tempdir))

        # Warn users of git that they should use the --git-aware option.
        # The .git directory contains all files ever checked in, and all diffs
        # in the entire history.
        root_dir = Path(self.config.rootdir)
        git_aware = self.config.getoption("git_aware")
        git_dir = root_dir / ".git"
        if git_dir.exists() and not git_aware:
            warnings.warn(
                f".git dir detected: {str(git_dir)}. pytest-workflow "
                f"will copy the entire .git directory and all files ignored "
                f"by git. It is recommended to use the --git-aware option.")
        # Copy the project directory to the temporary directory using pytest's
        # rootdir.
        duplicate_tree(root_dir, tempdir,
                       symlink=self.config.getoption("symlink"),
                       git_aware=git_aware)

        # Create a workflow and make sure it runs in the tempdir
        workflow = Workflow(command=self.workflow_test.command,
                            cwd=tempdir,
                            name=self.workflow_test.name,
                            desired_exit_code=self.workflow_test.exit_code)

        # Add the workflow to the workflow queue.
        self.config.workflow_queue.put(workflow)

        # Add the tempdir to the removal queue. We do not use a teardown method
        # because this will remove the tempdir right after all the tests from
        # this node have finished. If custom tests are defined this should not
        # happen. The removal queue is processed just before pytest finishes
        # and all tests have run.
        self.config.workflow_cleanup_dirs.append(tempdir)
        return workflow

    def collect(self):
        """This runs the workflow and starts all the associated tests
        The idea is that isolated parts of the yaml get their own collector or
        item."""

        # If tags specified on the command line are not a subset of the tags on
        # this node, do not collect tests and do not queue the workflow.
        # NOTE: an empty set is always a subset of any other set. So if no tags
        # are given on the command line all workflow tests are run. (This is
        # the least unexpected behaviour.)
        if not (set(self.config.getoption("workflow_tags")
                    ).issubset(set(self.tags))):
            return []
        else:
            # If we run the workflow, save this for reference later.
            # Save the nodeid because it also contains the originating file.
            # This is useful for error messages later.
            self.config.executed_workflows[self.workflow_test.name] = (
                self.nodeid)

        # This creates a workflow that is queued for processing after the
        # collection phase.
        workflow = self.queue_workflow()

        # Below structure makes it easy to append tests
        tests = []

        tests += [ExitCodeTest.from_parent(
            parent=self,
            workflow=workflow,
            stderr_bytes=self.config.getoption("stderr_bytes"))]

        tests += [
            FileTestCollector.from_parent(
                parent=self, filetest=filetest, workflow=workflow)
            for filetest in self.workflow_test.files]

        tests += [ContentTestCollector.from_parent(
            name="stdout", parent=self,
            filepath=workflow.stdout_file,
            content_test=self.workflow_test.stdout,
            workflow=workflow,
            content_name=f"'{self.workflow_test.name}': stdout")]

        tests += [ContentTestCollector.from_parent(
            name="stderr", parent=self,
            filepath=workflow.stderr_file,
            content_test=self.workflow_test.stderr,
            workflow=workflow,
            content_name=f"'{self.workflow_test.name}': stderr")]

        return tests


class ExitCodeTest(pytest.Item):
    def __init__(self, parent: pytest.Collector,
                 workflow: Workflow, stderr_bytes: int):
        name = f"exit code should be {workflow.desired_exit_code}"
        super().__init__(name, parent=parent)
        self.stderr_bytes = stderr_bytes
        self.workflow = workflow

    def runtest(self):
        # workflow.exit_code waits for workflow to finish.
        assert self.workflow.matching_exitcode()

    def repr_failure(self, excinfo, style=None):
        standerr = self.workflow.stderr_file
        standout = self.workflow.stdout_file
        with open(standout, "rb") as standout_file, \
             open(standerr, "rb") as standerr_file:
            if os.path.getsize(standerr) >= self.stderr_bytes:
                standerr_file.seek(-self.stderr_bytes, os.SEEK_END)
            if os.path.getsize(standout) >= self.stderr_bytes:
                standout_file.seek(-self.stderr_bytes, os.SEEK_END)
            message = (f"'{self.workflow.name}' exited with exit code " +
                       f"'{self.workflow.exit_code}' instead of "
                       f"'{self.workflow.desired_exit_code}'.\nstderr: "
                       f"{standerr_file.read().strip().decode('utf-8')}"
                       f"\nstdout: "
                       f"{standout_file.read().strip().decode('utf-8')}")
        return message
