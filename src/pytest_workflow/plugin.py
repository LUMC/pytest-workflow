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

from typing import List

import pytest
import yaml

from pathlib import Path
from .schema import validate_schema
from .workflow import Workflow
from .workflow_file_tests import WorkflowFilesTestCollector


def pytest_collect_file(path, parent):
    """Collection hook
    This collects the yaml files where the tests are defined."""
    if path.ext in [".yml", ".yaml"] and path.basename.startswith("test"):
        return YamlFile(path, parent)


class YamlFile(pytest.File):
    """This class collects YAML files and turns them into test items."""

    def collect(self):
        with self.fspath.open() as yaml_file:
            yaml_content = yaml.load(yaml_file)
        yield WorkflowTestsCollector(self.fspath.basename, yaml_content)


class WorkflowTestsCollector(pytest.Collector):
    """This class defines a pytest item. That has methods for running tests."""

    def __init__(self, name, yaml_content: dict):
        validate_schema(yaml_content)
        self.yaml_content = yaml_content
        self.name = name

    def collect(self):
        '''Run the workflow and start the tests'''
        workflow = Workflow(
            executable=self.yaml_content.get("executable"),
            arguments=self.yaml_content.get("arguments"))
        self.workflow.run()
        workflow_tests=[WorkflowFilesTestCollector(self.name,self.yaml_content.get("results",{}).get("files",[]))]
        return workflow_tests

    def reportinfo(self):
        return self.fspath, None, self.name
