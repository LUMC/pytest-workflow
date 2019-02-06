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
from typing import Optional  # noqa: F401 needed for typing.

import pytest

import yaml

from . import replace_whitespace
from .content_tests import ContentTestCollector
from .file_tests import FileTestCollector
from .schema import WorkflowTest, workflow_tests_from_schema
from .workflow import Workflow, WorkflowQueue


def pytest_addoption(parser):
    parser.addoption(
        "--keep-workflow-wd",
        action="store_true",
        help="Keep temporary directories where workflows are run for "
             "debugging purposes. This also triggers saving of stdout and "
             "stderr in the workflow directory",
        dest="keep_workflow_wd")
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


def pytest_configure(config):
    """This runs before tests start and adds values to the config."""
    # We need to add a workflow queue to some central variable. Instead of
    # using a global variable we add a value to the config.
    # Using setattr is not the nicest way of doing things, but having something
    # in the globally used config is the easiest and least hackish way to get
    # this going.
    workflow_queue = WorkflowQueue()
    setattr(config, "workflow_queue", workflow_queue)

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
    workflow_dir = (
        Path(basetemp) if basetemp is not None
        else Path(tempfile.mkdtemp(prefix="pytest_workflow_")))
    setattr(config, "workflow_dir", workflow_dir)


def pytest_collection(session):
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


def pytest_runtestloop(session):
    """This runs after collection, but before the tests."""
    session.config.workflow_queue.process(
        session.config.getoption("workflow_threads")
    )


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
        # Tempdir is stored for cleanup with teardown().
        self.tempdir = None  # type: Optional[Path]

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

        self.tempdir = (self.config.workflow_dir /
                        Path(replace_whitespace(self.name, '_')))

        # Remove the tempdir if it exists. This is needed for shutil.copytree
        # to work properly.
        if self.tempdir.exists():
            warnings.warn(
                "'{0}' already exists. Deleting ...".format(self.tempdir))
            shutil.rmtree(str(self.tempdir))

        # Copy the project directory to the temporary directory using pytest's
        # rootdir.
        shutil.copytree(str(self.config.rootdir), str(self.tempdir))

        # Create a workflow and make sure it runs in the tempdir
        workflow = Workflow(command=self.workflow_test.command,
                            cwd=self.tempdir,
                            name=self.workflow_test.name)

        # Add the workflow to the workflow queue.
        self.config.workflow_queue.put(workflow)

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

    def teardown(self):
        """This function is executed after all tests from this collector have
        finished. It is used to cleanup the tempdir."""
        if (not self.config.getoption("keep_workflow_wd")
                and self.tempdir is not None):
            shutil.rmtree(str(self.tempdir))


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
