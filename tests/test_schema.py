#!/usr/bin/env python3

# Copyright (C) 2018 Leiden University Medical Center
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/

# This file contains tests for the schema for the yaml file


import os
from pathlib import Path

import jsonschema

import pytest

from pytest_workflow.schema import WorkflowTest, validate_schema, \
    workflow_tests_from_schema

import yaml


valid_yaml_dir = Path(__file__).parent / Path("yamls") / Path("valid")
valid_yamls = os.listdir(valid_yaml_dir.__str__())


@pytest.mark.parametrize("yaml_path", valid_yamls)
def test_validate_schema(yaml_path):
    with Path(valid_yaml_dir / Path(yaml_path)).open() as yaml_fh:
        validate_schema(yaml.safe_load(yaml_fh))


def test_WorkflowTest():
    with (valid_yaml_dir / Path("dream_file.yaml")).open() as yaml_fh:
        test_yaml = yaml.load(yaml_fh)
        tests = [WorkflowTest.from_schema(x) for x in test_yaml]
        assert tests[0].name == "simple echo"
        assert tests[0].files[0].path == Path("log.file")
        assert len(tests[0].files[0].contains) == 3
        assert len(tests[0].files[0].must_not_contain) == 1
        assert len(tests[0].files) == 1
        assert tests[0].stdout.contains == ["bla"]
        assert tests[0].exit_code == 127


def test_validate_schema_conflicting_keys():
    with pytest.raises(jsonschema.ValidationError) as error:
        validate_schema([
            dict(name="bla",
                 command="cowsay moo",
                 files=[dict(
                     path="/some/path",
                     should_exist=False,
                     must_not_contain=["bla"]
                 )])
        ])
    assert error.match("Content checking not allowed on non existing" +
                       " file: /some/path. Key = must_not_contain")


def test_workflow_tests_from_schema():
    with (valid_yaml_dir / Path("dream_file.yaml")).open() as yaml_fh:
        test_yaml = yaml.load(yaml_fh)
        workflow_tests = workflow_tests_from_schema(test_yaml)
        assert len(workflow_tests) == 2
