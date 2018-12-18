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

import os
import tempfile
from distutils.dir_util import copy_tree

import pytest

import yaml

from .schema import WorkflowTest, workflow_tests_from_schema
from .workflow import Workflow
from .workflow_file_tests import WorkflowFilesTestCollector


def pytest_collect_file(path, parent):
    """Collection hook
    This collects the yaml files called r'test.*\.ya?ml'"""  # noqa: W605
    # noqa ignores invalid escape sequence in the regex.
    if path.ext in [".yml", ".yaml"] and path.basename.startswith("test"):
        return YamlFile(path, parent)


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
        workflow_tests = workflow_tests_from_schema(schema)
        for test in workflow_tests:
            yield WorkflowTestsCollector(test, self)


class WorkflowTestsCollector(pytest.Collector):
    """This class starts all the tests collectors per workflow"""

    def __init__(self, test: WorkflowTest, parent: pytest.Collector):
        self.test = test
        super().__init__(test.name, parent=parent)

    def collect(self):
        """This runs the workflow and starts all the associated tests
        The idea is that isolated parts of the yaml get their own collector.
        So in the results key in hte yaml there is a key called `files` this
        generates the WorkflowFilesTestCollector. When we add a key `stdout
        we add a new class WorkflowStdoutTestCollector etc."""

        # Create a temporary directory where the workflow is run.
        # This will prevent the project repository from getting filled up with
        # test workflow output.
        tempdir = tempfile.mkdtemp(prefix="pytest_wf")

        # Copy the project directory to the temporary directory. os.getcwd()
        # is used here because it is assumed pytest is run from project root.
        # Using the python git plugin was considered, as it can also give the
        # project root. But this assumes git. So this choice is debatable.
        copy_tree(os.getcwd(), tempdir)

        # Create a workflow and make sure it runs in the tempdir
        workflow = Workflow(self.test.command, tempdir)
        workflow.run()

        # Add new testcollectors to this list if new types of tests are
        # defined.
        workflow_tests = [
            WorkflowFilesTestCollector(
                self.test.name, self, self.test.files, tempdir)
        ]
        for test in workflow_tests:
            yield test
        # TODO: Figure out proper cleanup.
        # If tempdir is removed here, all tests will fail.
        # After yielding the tests this object is no longer needed, so
        # deleting the tempdir here does not work.
        # There is probably some fixture that can handle this.

    def reportinfo(self):
        # TODO: Figure out what reportinfo does
        # This was copied from code example.
        return self.fspath, None, self.name
