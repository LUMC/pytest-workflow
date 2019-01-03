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
import re

from _pytest.config import argparsing
from _pytest.tmpdir import TempdirFactory  # noqa: E501,F401 # used for type annotation

from py._path.local import LocalPath  # noqa: F401 # used for type annotation

import pytest

import yaml

from .content_tests import ContentTestCollector
from .file_tests import FileTestCollector
from .schema import WorkflowTest, workflow_tests_from_schema
from .workflow import Workflow


def pytest_addoption(parser: argparsing.Parser):
    parser.addoption(
        "--keep-workflow-wd",
        action="store_true",
        help="Keep temporary directories where workflows are run for "
             "debugging purposes. This also triggers saving of stdout and "
             "stderr in the workflow directory",
        dest="keep_workflow_wd"
    )


def pytest_collect_file(path, parent):
    """Collection hook
    This collects the yaml files that start with "test" and end with
    .yaml or .yml"""
    if path.ext in [".yml", ".yaml"] and path.basename.startswith("test"):
        return YamlFile(path, parent)
    return None


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

    def run_workflow(self):
        """Runs the workflow in a temporary directory

        Running in a temporary directory will prevent the project repository
        from getting filled up with test workflow output.
        The temporary directory is produced from self.config._tmpdirhandler
        which  does the same as using a `tmpdir` fixture.

        The temporary directory name is constructed from the test name by
        replacing all whitespaces with '_'. Directory paths with whitespace in
        them are very annoying to inspect.
        Additionally the temporary directories are numbered. This prevents
        name collisions if tests have the same name (when whitespace is
        replaced). This is because pytest does not use the stdlib's tempfile
        and instead uses its own solution. So directories with the same name
        can have collisions unless numbered is used.
        The alternative is overengineering some name collision
        prevention stuff in schema.py. But that will be a lot of work to create
        and maintain. So using numbers as a solution was preferred.

        Print statements are used to provide information to the user.  Using
        pytests internal logwriter has no added value. If there are wishes to
        do so in the future, the pytest terminal writer can be acquired with:
        self.config.pluginmanager.get_plugin("terminalreporter")
        Test name is included explicitly in each print command to avoid
        confusion between workflows
        """
        # pylint: disable=protected-access
        # Protected access needed to integrate tmpdir fixture functionality.

        tmpdirhandler = self.config._tmpdirhandler  # type: TempdirFactory
        tempdir = tmpdirhandler.mktemp(
            re.sub(r'\s+', '_', self.name),
            numbered=True
        )  # type: LocalPath

        # Copy the project directory to the temporary directory using pytest's
        # rootdir.
        rootdir = self.config.rootdir  # type: LocalPath
        rootdir.copy(tempdir)

        # Create a workflow and make sure it runs in the tempdir
        workflow = Workflow(self.workflow_test.command, str(tempdir))

        print("run '{name}' with command '{command}' in '{dir}'".format(
            name=self.name,
            command=self.workflow_test.command,
            dir=tempdir))
        workflow.run()
        print("run '{name}': done".format(name=self.name))

        if self.config.getoption("keep_workflow_wd", False):
            log_err = workflow.stderr_to_file()
            log_out = workflow.stdout_to_file()
            print("'{0}' stdout saved in: {1}".format(self.name, str(log_out)))
            print("'{0}' stderr saved in: {1}".format(self.name, str(log_err)))
        else:
            # addfinalizer adds a function that is run when the node tests are
            # completed
            self.addfinalizer(tempdir.remove)

        return workflow

    def collect(self):
        """This runs the workflow and starts all the associated tests
        The idea is that isolated parts of the yaml get their own collector or
        item."""

        workflow = self.run_workflow()

        # Below structure makes it easy to append tests
        tests = []

        tests += [FileTestCollector(self, filetest, workflow.cwd) for filetest
                  in self.workflow_test.files]

        tests += [ExitCodeTest(self, workflow.exit_code,
                               self.workflow_test.exit_code)]

        tests += [ContentTestCollector(
            name="stdout", parent=self,
            content=workflow.stdout.decode().splitlines(),
            content_test=self.workflow_test.stdout)]

        tests += [ContentTestCollector(
            name="stderr", parent=self,
            content=workflow.stderr.decode().splitlines(),
            content_test=self.workflow_test.stderr)]

        return tests


class ExitCodeTest(pytest.Item):
    def __init__(self, parent: pytest.Collector, exit_code: int,
                 desired_exit_code: int):
        name = "exit code should be {0}".format(desired_exit_code)
        super().__init__(name, parent=parent)
        self.exit_code = exit_code
        self.desired_exit_code = desired_exit_code

    def runtest(self):
        assert self.exit_code == self.desired_exit_code

    def repr_failure(self, excinfo):
        # pylint: disable=unused-argument
        # excinfo needed for pytest.
        message = ("The workflow exited with exit code " +
                   "'{0}' instead of '{1}'.".format(self.exit_code,
                                                    self.desired_exit_code))
        return message
