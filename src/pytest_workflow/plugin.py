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
import shutil
import tempfile
import warnings
from pathlib import Path
from typing import List, Optional  # noqa: F401 needed for typing.

from _pytest.config import Config as PytestConfig
from _pytest.config.argparsing import Parser as PytestParser
from _pytest.fixtures import SubRequest
from _pytest.mark import MarkDecorator  # noqa: F401 used for typing

import pytest

import yaml

from . import replace_whitespace, rm_dirs
from .content_tests import ContentTestCollector
from .file_tests import FileTestCollector
from .schema import WorkflowTest, workflow_tests_from_schema
from .workflow import Workflow, WorkflowQueue


def pytest_addoption(parser: PytestParser):
    parser.addoption(
        "--kwd", "--keep-workflow-wd",
        action="store_true",
        help="Keep temporary directories where workflows are run for "
             "debugging purposes. This also triggers saving of stdout and "
             "stderr in the workflow directory",
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
        default=[]
    )


def pytest_collect_file(path, parent):
    """Collection hook
    This collects the yaml files that start with "test" and end with
    .yaml or .yml"""
    if path.ext in [".yml", ".yaml"] and path.basename.startswith("test"):
        return YamlFile(path, parent)
    return None


def pytest_configure(config: PytestConfig):
    """This runs before tests start and adds values to the config."""

    #  Add marker to the config to prevent issues caused by:
    #  https://github.com/pytest-dev/pytest/issues/4826
    # Errors are now emitted when unknown marks are included
    config.addinivalue_line(
        "markers",
        "workflow(name): mark test to run only with the given "
        "workflow name. Also provides access to the workflow_dir "
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
    executed_workflows = []  # type: List[str]
    setattr(config, "executed_workflows", executed_workflows)

    # Save workflow for cleanup in this var.
    workflow_cleanup_dirs = []  # type: List[str]
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

    rootdir = Path(str(config.rootdir))
    # Raise an error if the workflow temporary directory of the rootdir
    # (pytest's CWD). This will lead to infinite looping and copying.
    if str(workflow_temp_dir.absolute()).startswith(str(rootdir.absolute())):
        raise ValueError("'{0}' is a subdirectory of '{1}'. Please select a "
                         "--basetemp that is not in pytest's current working "
                         "directory.".format(workflow_temp_dir, rootdir))

    setattr(config, "workflow_temp_dir", workflow_temp_dir)


def pytest_collection(session: pytest.Session):
    """This function is started at the beginning of collection"""
    # pylint: disable=unused-argument
    # needed for pytest
    # We print an empty line here to make the report look slightly better.
    # Without it pytest will output "Collecting ... " and the workflow commands
    # will be immediately after this: "Collecting ... queue (etc.) "
    # the prevent provides a newline. So it will look like:
    # Collecting ...
    # queue (etc.)
    print()


def pytest_collection_modifyitems(config: PytestConfig,
                                  items: List[pytest.Item]):
    """Here we skip all tests related to workflows that are not executed"""

    for item in items:
        marker = item.get_closest_marker(
            name="workflow")  # type: Optional[MarkDecorator] # noqa: E501

        if marker is None:
            continue

        if 'name' in marker.kwargs:
            workflow_name = marker.kwargs['name']
        # If name key is not defined use the first arg.
        elif 'name' not in marker.kwargs and len(marker.args) >= 1:
            workflow_name = marker.args[0]
            # Make sure a name attribute is added anyway for the
            # fixture lookup.
            marker.kwargs['name'] = workflow_name
        else:
            raise TypeError("A workflow name should be defined in the "
                            "workflow marker of {0}".format(item.nodeid))

        if workflow_name not in config.executed_workflows:
            skip_marker = pytest.mark.skip(
                reason="'{0}' has not run.".format(workflow_name))
            item.add_marker(skip_marker)


def pytest_runtestloop(session: pytest.Session):
    """This runs after collection, but before the tests."""
    session.config.workflow_queue.process(
        session.config.getoption("workflow_threads")
    )


def pytest_sessionfinish(session: pytest.Session, exitstatus: int):
    # No cleanup needed if we keep workflow directories
    # Or if there are no directories to cleanup. (I.e. pytest-workflow plugin
    # was not used.)
    if (session.config.getoption("keep_workflow_wd") or
            len(session.config.workflow_cleanup_dirs) == 0):
        pass
    elif session.config.getoption("keep_workflow_wd_on_fail"):
        # Ony cleanup if there are cleanup_dirs.
        if exitstatus == 0:
            print("All tests succeeded. Removing temporary directories and "
                  "logs.")
            rm_dirs(session.config.workflow_cleanup_dirs)
        else:
            print("One or more tests failed. Keeping temporary directories "
                  "and logs.")
    else:  # When no flags are set. Remove temporary directories and logs.
        print("Removing temporary directories and logs. Use '--kwd' or "
              "'--keep-workflow-wd' to disable this behaviour.")
        rm_dirs(session.config.workflow_cleanup_dirs)


@pytest.fixture()
def workflow_dir(request: SubRequest):
    """Returns the workflow_dir of the workflow named in the mark. This fixture
    is only provided for tests that are marked with the workflow mark."""

    # request.node refers to the node that has the mark. This is a pytest.Node
    marker = request.node.get_closest_marker(name="workflow")

    if marker is not None:
        workflow_temp_dir = request.config.workflow_temp_dir
        try:
            workflow_name = marker.kwargs['name']
        except KeyError:
            raise TypeError(
                "A workflow name should be defined in the "
                "workflow marker of {0}".format(request.node.nodeid))
        return workflow_temp_dir / Path(replace_whitespace(workflow_name))
    else:
        raise ValueError("workflow_dir can only be requested in tests marked"
                         " with the workflow mark.")


class YamlFile(pytest.File):
    """
    This class collects YAML files and turns them into test items.
    """

    def __init__(self, path: str, parent: pytest.Collector):
        # This super statement is important for pytest reasons. It should
        # be in any collector!
        super().__init__(path, parent=parent)

    def collect(self):
        """This function collects all the workflow tests from a single
        YAML file."""
        with self.fspath.open() as yaml_file:
            schema = yaml.safe_load(yaml_file)

        return [WorkflowTestsCollector(test, self)
                for test in workflow_tests_from_schema(schema)]


class WorkflowTestsCollector(pytest.Collector):
    """This class starts all the tests collectors per workflow"""

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
                "'{0}' already exists. Deleting ...".format(tempdir))
            shutil.rmtree(str(tempdir))

        # Copy the project directory to the temporary directory using pytest's
        # rootdir.
        shutil.copytree(str(self.config.rootdir), str(tempdir))

        # Create a workflow and make sure it runs in the tempdir
        workflow = Workflow(command=self.workflow_test.command,
                            cwd=tempdir,
                            name=self.workflow_test.name)

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
            self.config.executed_workflows.append(self.workflow_test.name)

        # This creates a workflow that is queued for processing after the
        # collection phase.
        workflow = self.queue_workflow()

        # Below structure makes it easy to append tests
        tests = []

        tests += [FileTestCollector(self, filetest, workflow) for filetest
                  in self.workflow_test.files]

        tests += [ExitCodeTest(parent=self,
                               desired_exit_code=self.workflow_test.exit_code,
                               workflow=workflow)]

        tests += [ContentTestCollector(
            name="stdout", parent=self,
            filepath=workflow.stdout_file,
            content_test=self.workflow_test.stdout,
            workflow=workflow,
            content_name="'{0}': stdout".format(self.workflow_test.name))]

        tests += [ContentTestCollector(
            name="stderr", parent=self,
            filepath=workflow.stderr_file,
            content_test=self.workflow_test.stderr,
            workflow=workflow,
            content_name="'{0}': stderr".format(self.workflow_test.name))]

        return tests


class ExitCodeTest(pytest.Item):
    def __init__(self, parent: pytest.Collector,
                 desired_exit_code: int,
                 workflow: Workflow):
        name = "exit code should be {0}".format(desired_exit_code)
        super().__init__(name, parent=parent)
        self.workflow = workflow
        self.desired_exit_code = desired_exit_code

    def runtest(self):
        # workflow.exit_code waits for workflow to finish.
        assert self.workflow.exit_code == self.desired_exit_code

    def repr_failure(self, excinfo):
        # pylint: disable=unused-argument
        # excinfo needed for pytest.
        message = ("'{workflow_name}' exited with exit code " +
                   "'{exit_code}' instead of '{desired_exit_code}'."
                   ).format(workflow_name=self.workflow.name,
                            exit_code=self.workflow.exit_code,
                            desired_exit_code=self.desired_exit_code)
        return message
