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

"""Tests the schema validation"""


import os
from pathlib import Path

import jsonschema

import pytest

from pytest_workflow.schema import ContentTest, FileTest, WorkflowTest, \
        validate_schema, workflow_tests_from_schema

import yaml

VALID_YAML_DIR = Path(__file__).parent / "yamls" / "valid"
VALID_YAMLS = os.listdir(VALID_YAML_DIR)


@pytest.mark.parametrize("yaml_path", VALID_YAMLS)
def test_validate_schema(yaml_path):
    with Path(VALID_YAML_DIR, yaml_path).open() as yaml_fh:
        validate_schema(yaml.safe_load(yaml_fh))


def test_workflowtest():
    with Path(VALID_YAML_DIR, "dream_file.yaml").open() as yaml_fh:
        test_yaml = yaml.safe_load(yaml_fh)
        tests = [WorkflowTest.from_schema(x) for x in test_yaml]
        assert tests[0].name == "simple echo"
        assert tests[0].files[0].path == Path("log.file")
        assert len(tests[0].files[0].contains) == 3
        assert len(tests[0].files[0].must_not_contain) == 1
        assert len(tests[0].files) == 1
        assert tests[0].stdout.contains == ["bla"]
        assert tests[0].exit_code == 127
        assert tests[0].tags == ["simple", "use_echo"]


def test_workflowtest_regex():
    with Path(VALID_YAML_DIR, "regex_file.yaml").open() as yaml_fh:
        test_yaml = yaml.safe_load(yaml_fh)
        tests = [WorkflowTest.from_schema(x) for x in test_yaml]
        assert tests[0].name == "simple echo"
        assert tests[0].files[0].path == Path("log.file")
        assert tests[0].files[0].contains_regex == ["bla"]
        assert tests[0].files[0].must_not_contain_regex == ["stuff"]
        assert len(tests[0].files) == 1
        assert tests[0].stdout.contains_regex == ["bla"]
        assert tests[0].stdout.must_not_contain_regex == ["stuff"]
        assert tests[0].stderr.contains_regex == ["bla"]
        assert tests[0].stderr.must_not_contain_regex == ["stuff"]


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


def test_validate_schema_colliding_names():
    with pytest.raises(jsonschema.ValidationError) as error:
        validate_schema([
            dict(name="name collision", command="echo moo"),
            dict(name="name    collision", command="echo moo"),
            dict(name="name        collision", command="echo moo")
        ])
    assert error.match("Some names were not unique when whitespace was "
                       "removed. Defined names:")
    assert error.match("name collision")


def test_no_empty_command():
    with pytest.raises(jsonschema.ValidationError) as error:
        validate_schema([dict(name="empty", command="")])
    assert error.match("command must not be empty")


def test_no_empty_name():
    with pytest.raises(jsonschema.ValidationError) as error:
        validate_schema([dict(name="", command="echo nothing")])
    assert error.match("name must not be empty")


CONTAINS_LIST = [
    """
    - name: bla
      command: bla
      stdout:
        contains: ["bla"]
        must_not_contain: ["bla"]
    """,
    """
    - name: bla
      command: bla
      stderr:
        contains: ["bla"]
        must_not_contain: ["bla"]
    """,
    """
    - name: bla
      command: bla
      files:
        - path: bla
          contains: ["bla"]
          must_not_contain: ["bla"]
    """
]


@pytest.mark.parametrize("instance",
                         [yaml.safe_load(workflow) for workflow in
                          CONTAINS_LIST])
def test_validate_schema_contains_conflict(instance):
    with pytest.raises(jsonschema.ValidationError) as errormsg:
        validate_schema(instance)
    assert errormsg.match(
        "contains and must_not_contain are not allowed to have "
        "the same members for the same object.")
    assert errormsg.match(" Common members: {'bla'}")


def test_workflow_tests_from_schema():
    with Path(VALID_YAML_DIR, "dream_file.yaml").open() as yaml_fh:
        test_yaml = yaml.safe_load(yaml_fh)
        workflow_tests = workflow_tests_from_schema(test_yaml)
        assert len(workflow_tests) == 2


def test_workflow_test_defaults():
    workflow_test = WorkflowTest.from_schema(
        dict(name="minimal", command="cowsay minimal"))
    assert workflow_test.files == []
    assert workflow_test.stdout.contains == []
    assert workflow_test.stdout.must_not_contain == []
    assert workflow_test.stdout.contains_regex == []
    assert workflow_test.stdout.must_not_contain_regex == []
    assert workflow_test.stderr.contains == []
    assert workflow_test.stderr.must_not_contain == []
    assert workflow_test.exit_code == 0


def test_filetest_defaults():
    file_test = FileTest(path="bla")
    assert file_test.contains == []
    assert file_test.must_not_contain == []
    assert file_test.contains_regex == []
    assert file_test.must_not_contain_regex == []
    assert file_test.md5sum is None
    assert file_test.extract_md5sum is None
    assert file_test.should_exist


def test_contenttest_with_contains():
    """ Test if we can make a ContentTest object without regex to match """
    ContentTest(contains=["Should contain"],
                must_not_contain=["Should not contain"])


def test_contenttest_with_regex():
    """ Test if we can make a ContentTest object with regex to match """
    ContentTest(contains_regex=["Should contain"],
                must_not_contain_regex=["Should not contain"])


def test_filetest_with_contains():
    """ Test if we can make a FileTest object without regex to match """
    file_test = FileTest(path="bla", md5sum="checksum", should_exist=False,
                         contains=["Should contain"],
                         must_not_contain=["Should not contain"])
    assert file_test.contains == ["Should contain"]
    assert file_test.must_not_contain == ["Should not contain"]


def test_filetest_with_regex():
    """ Test if we can make a FileTest object with a regex to match """
    file_test = FileTest(path="bla", md5sum="checksum", should_exist=False,
                         contains_regex=["Should contain"],
                         must_not_contain_regex=["Should not contain"])
    assert file_test.contains_regex == ["Should contain"]
    assert file_test.must_not_contain_regex == ["Should not contain"]
