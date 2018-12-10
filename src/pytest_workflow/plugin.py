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


def pytest_collect_file(path, parent):
    """Collection hook
    This collects the yaml files where the tests are defined."""
    if path.ext in [".yml", ".yaml"] and path.basename.startswith("test"):
        return YamlFile(path, parent)


class YamlFile(pytest.File):
    """This class collects YAML files and turns them into test items."""

    def collect(self):
        yaml_content = yaml.load(self.fspath.open())
        yield WorkflowTestsCollector(self.fspath.basename, self, yaml_content)


class WorkflowTestsCollector(pytest.Collector):
    """This class defines a pytest item. That has methods for running tests."""

    def __init__(self, yaml_content: dict):
        validate_schema(yaml_content)
        self.yaml_content = yaml_content
        self.workflow = Workflow(
            executable=self.config.getoption("workflow_executable"),
            arguments=self.yaml_content.get("arguments"))
        # Run the workflow on initialization
        self.workflow.run()

    def collect(self):
        workflow_tests=[]
        return workflow_tests

    def reportinfo(self):
        return self.fspath, None, self.name

def pytest_addoption(parser):
    """This adds extra options to the pytest executable"""
    parser.addoption(
        "--workflow-executable",
        dest="workflow_executable",
        help="The executable used to run the workflow. This argument is required for running workflows."
    )
