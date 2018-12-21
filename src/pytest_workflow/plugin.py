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

import tempfile
# Disable pylint here because of false positive
from distutils.dir_util import copy_tree  # pylint: disable=E0611,E0401

import pytest

import yaml

from .content_tests import generate_log_tests
from .file_tests import FileTestCollector
from .schema import WorkflowTest, workflow_tests_from_schema
from .workflow import Workflow


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
        """This function now only returns one WorkflowTestsCollector,
            but this might be increased later when we decide to put multiple
            tests in one yaml. """
        with self.fspath.open() as yaml_file:
            schema = yaml.safe_load(yaml_file)

        return [WorkflowTestsCollector(test, self)
                for test in workflow_tests_from_schema(schema)]


class WorkflowTestsCollector(pytest.Collector):
    """This class starts all the tests collectors per workflow"""

    def __init__(self, workflow_test: WorkflowTest, parent: pytest.Collector):
        self.workflow_test = workflow_test
        super().__init__(workflow_test.name, parent=parent)

    def collect(self):
        """This runs the workflow and starts all the associated tests
        The idea is that isolated parts of the yaml get their own collector or
        item."""

        # Create a temporary directory where the workflow is run.
        # This will prevent the project repository from getting filled up with
        # test workflow output.
        tempdir = tempfile.mkdtemp(prefix="pytest_wf")

        # Copy the project directory to the temporary directory using pytest's
        # rootdir.
        copy_tree(str(self.config.rootdir), tempdir)

        # Create a workflow and make sure it runs in the tempdir
        workflow = Workflow(self.workflow_test.command, tempdir)
        workflow.run()

        # Below structure makes it easy to append tests
        tests = []

        tests += [FileTestCollector(self, filetest, tempdir) for filetest in
                  self.workflow_test.files]

        tests += [ExitCodeTest(self, workflow.exit_code,
                               self.workflow_test.exit_code)]

        tests += generate_log_tests(parent=self, log=workflow.stdout,
                                    log_test=self.workflow_test.stdout,
                                    prefix="stdout ")

        tests += generate_log_tests(parent=self, log=workflow.stderr,
                                    log_test=self.workflow_test.stderr,
                                    prefix="stderr ")

        return tests
        # TODO: Figure out proper cleanup.
        # If tempdir is removed here, all tests will fail.
        # After yielding the tests this object is no longer needed, so
        # deleting the tempdir here does not work.
        # There is probably some fixture that can handle this.

    def reportinfo(self):
        # TODO: Figure out what reportinfo does
        # This was copied from code example.
        return self.fspath, None, self.name


class ExitCodeTest(pytest.Item):
    def __init__(self, parent: pytest.Collector, exit_code: int,
                 desired_exit_code: int):
        name = "exit code should be {0}".format(desired_exit_code)
        super().__init__(name, parent=parent)
        self.exit_code = exit_code
        self.desired_exit_code = desired_exit_code

    def runtest(self):
        assert self.exit_code == self.desired_exit_code
