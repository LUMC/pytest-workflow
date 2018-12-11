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

import pytest
import tempfile
import yaml
import os
from .schema import validate_schema
from .workflow import Workflow
from .workflow_file_tests import WorkflowFilesTestCollector
from distutils.dir_util import copy_tree
from pathlib import Path

def pytest_collect_file(path, parent):
    """Collection hook
    This collects the yaml files where the tests are defined."""
    if path.ext in [".yml", ".yaml"] and path.basename.startswith("test"):
        return YamlFile(path, parent)


class YamlFile(pytest.File):
    """This class collects YAML files and turns them into test items."""

    def __init__(self, path, parent):
        super(YamlFile, self).__init__(path, parent=parent)

    def collect(self):
        with self.fspath.open() as yaml_file:
            yaml_content = yaml.load(yaml_file)
        yield WorkflowTestsCollector(self.fspath.basename, self, yaml_content)


class WorkflowTestsCollector(pytest.Collector):
    """This class defines a pytest item. That has methods for running tests."""

    def __init__(self, name, parent, yaml_content: dict):
        validate_schema(yaml_content)
        self.yaml_content = yaml_content
        self.name = name
        super(WorkflowTestsCollector, self).__init__(name, parent=parent)

    def collect(self):
        """Run the workflow and start the tests"""
        # Make sure workflow is run in a temporary directory
        tempdir = tempfile.mkdtemp(prefix="pytest_wf", dir= tempfile.gettempdir())
        copy_tree(os.getcwd(), tempdir)
        print(tempdir)
        workflow = Workflow(
            executable=self.yaml_content.get("executable"),
            arguments=self.yaml_content.get("arguments"),
            cwd=tempdir)
        workflow.run()
        workflow_tests = [
            WorkflowFilesTestCollector(self.name, self, self.yaml_content.get("results", {}).get("files", []), tempdir)]
        for test in workflow_tests:
            yield test

    def reportinfo(self):
        return self.fspath, None, self.name
