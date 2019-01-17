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
from pathlib import Path
from typing import Optional  # noqa: F401 needed for typing.

import _pytest
# Also do the from imports. Otherwise the IDE does not understand the types.
from _pytest.config import Config, argparsing  # noqa: F401

import pytest

import yaml

from . import replace_whitespace
from .content_tests import ContentTestCollector
from .file_tests import FileTestCollector
from .schema import WorkflowTest, workflow_tests_from_schema
from .workflow import Workflow, WorkflowQueue


def pytest_addoption(parser: _pytest.config.argparsing.Parser):
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


def pytest_collect_file(path, parent):
    """Collection hook
    This collects the yaml files that start with "test" and end with
    .yaml or .yml"""
    if path.ext in [".yml", ".yaml"] and path.basename.startswith("test"):
        return YamlFile(path, parent)
    return None


def pytest_configure(config: _pytest.config.Config):
    """This runs before tests start and adds values to the config."""
    # We need to add a workflow queue to some central variable. Instead of
    # using a global variable we add a value to the config.
    # Using setattr is not the nicest way of doing things, but having something
    # in the globally used config is the easiest and least hackish way to get
    # this going.
    workflow_queue = WorkflowQueue()
    setattr(config, "workflow_queue", workflow_queue)


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
        number_of_threads=session.config.getoption("workflow_threads"),
        save_logs=session.config.getoption("keep_workflow_wd")
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
        # These below variables store values for cleanup with teardown().
        self.tempdir = None  # type: Optional[Path]
        self.workflow = None  # type: Optional[Workflow]

    def queue_workflow(self):
        """Creates a temporary directory and add the workflow to the workflow
        queue.

        Running in a temporary directory will prevent the project repository
        from getting filled up with test workflow output.
        The temporary directory is produced from
        self.config._tmp_path_factory.getbasetemp()
        On linux this takes the form: /tmp/pytest-of-$USER/pytest-<number>
        The number is generated by pytest itself and increments each run.

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
        # pylint: disable=protected-access
        # Protected access needed to get the basetemp value.

        basetemp = Path(str(self.config._tmp_path_factory.getbasetemp()))
        self.tempdir = basetemp / Path(replace_whitespace(self.name, '_'))

        # Copy the project directory to the temporary directory using pytest's
        # rootdir.
        shutil.copytree(str(self.config.rootdir), str(self.tempdir))
        # Create a workflow and make sure it runs in the tempdir
        self.workflow = Workflow(command=self.workflow_test.command,
                                 cwd=self.tempdir,
                                 name=self.workflow_test.name)

        print("queue '{name}' with command '{command}' in '{dir}'".format(
            name=self.name,
            command=self.workflow_test.command,
            dir=str(self.tempdir)))
        # Add the workflow to the workflow queue.
        self.config.workflow_queue.put(self.workflow)

    def collect(self):
        """This runs the workflow and starts all the associated tests
        The idea is that isolated parts of the yaml get their own collector or
        item."""

        # This creates a workflow that is queued for processing after the
        # collection phase.
        self.queue_workflow()

        # Below structure makes it easy to append tests
        tests = []

        tests += [FileTestCollector(self, filetest, self.workflow) for filetest
                  in self.workflow_test.files]

        tests += [ExitCodeTest(parent=self,
                               desired_exit_code=self.workflow_test.exit_code,
                               workflow=self.workflow)]

        tests += [ContentTestCollector(
            name="stdout", parent=self,
            content_generator=self.workflow.stdout_lines,
            content_test=self.workflow_test.stdout,
            workflow=self.workflow)]

        tests += [ContentTestCollector(
            name="stderr", parent=self,
            content_generator=self.workflow.stderr_lines,
            content_test=self.workflow_test.stderr,
            workflow=self.workflow)]

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
        message = ("The workflow exited with exit code " +
                   "'{0}' instead of '{1}'.".format(self.workflow.exit_code,
                                                    self.desired_exit_code))
        return message
