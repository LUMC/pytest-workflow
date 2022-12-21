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

"""Schema for the YAML files used by pytest-workflow"""

import json
from pathlib import Path
from typing import List, Optional

import jsonschema

from .util import replace_whitespace

SCHEMA = Path(__file__).parent / "schema" / "schema.json"
DEFAULT_EXIT_CODE = 0
DEFAULT_FILE_SHOULD_EXIST = True

JSON_SCHEMA = json.loads(SCHEMA.read_text())


def workflow_tests_from_schema(schema):
    """Returns workflow test objects from a schema"""
    validate_schema(schema)
    return [WorkflowTest.from_schema(x) for x in schema]


def validate_schema(instance):
    """
    Validates the pytest-workflow schema
    :param instance: an object that is validated against the schema
    :return: This function rasises a ValidationError
    when the schema is not correct.
    """
    jsonschema.validate(instance, JSON_SCHEMA)

    # Some extra tests here below that can not be captured in jsonschema

    # Test if there are name collisions when whitespace is removed. This will
    # cause errors in pytest (collectors not having unique names) so has to
    # be avoided.
    test_names = [replace_whitespace(test['name'], ' ') for test in instance]
    if len(test_names) != len(set(test_names)):
        raise jsonschema.ValidationError(
            f"Some names were not unique when whitespace was removed. "
            f"Defined names: {test_names}")

    def test_contains_concordance(dictionary: dict, name: str):
        """
        Test whether contains and must not contain have the same members.
        :param dictionary: part of the schema dictionary.
        :param name: The name of the object the dictionary originates from.
        This makes the error easier to comprehend for the user.
        :return: An error if the test fails.
        """
        contains = dictionary.get("contains", [])
        must_not_contain = dictionary.get("must_not_contain", [])
        if len(contains) > 0 and len(must_not_contain) > 0:
            common_members = set(contains).intersection(set(must_not_contain))
            if common_members != set():
                raise jsonschema.ValidationError(
                    f"contains and must_not_contain are not allowed to have "
                    f"the same members for the same object. "
                    f"Object: {name}. Common members: {common_members}"
                )

    for test in instance:
        test_contains_concordance(test.get('stdout', {}),
                                  test['name'] + "/stdout")
        test_contains_concordance(test.get('stderr', {}),
                                  test['name'] + "/stderr")
        for test_file in test.get("files", []):
            keys = test_file.keys()
            test_contains_concordance(test_file, test_file['path'])
            file_should_exist = test_file.get("should_exist",
                                              DEFAULT_FILE_SHOULD_EXIST)

            if not file_should_exist:
                for check in ["md5sum", "contains", "must_not_contain"]:
                    if check in keys:
                        raise jsonschema.ValidationError(
                            f"Content checking not allowed on non existing "
                            f"file: {test_file['path']}. Key = {check}")


# Schema classes below
# These classes are created so that the test yaml does not have to be passed
# around between test objects. But instead these objects which have self-
# documenting members
# TODO: Rewrite these into @Dataclass classes when python 3.7 becomes the
# TODO: minimum required version.


class ContentTest(object):
    """
    A class that holds four lists of strings. Everything in `contains` and
    `contains_regex` should be present in the file/text
    Everything in `must_not_contain` and `must_not_contain_regex` should
    not be present.
    """
    def __init__(self, contains: Optional[List[str]] = None,
                 must_not_contain: Optional[List[str]] = None,
                 contains_regex: Optional[List[str]] = None,
                 must_not_contain_regex: Optional[List[str]] = None,
                 encoding: Optional[str] = None):
        self.contains: List[str] = contains or []
        self.must_not_contain: List[str] = must_not_contain or []
        self.contains_regex: List[str] = contains_regex or []
        self.must_not_contain_regex: List[str] = must_not_contain_regex or []
        self.encoding: Optional[str] = encoding


class FileTest(ContentTest):
    """A class that contains all the properties of a to be tested file."""
    def __init__(self, path: str, md5sum: Optional[str] = None,
                 should_exist: bool = DEFAULT_FILE_SHOULD_EXIST,
                 contains: Optional[List[str]] = None,
                 must_not_contain: Optional[List[str]] = None,
                 contains_regex: Optional[List[str]] = None,
                 must_not_contain_regex: Optional[List[str]] = None,
                 encoding: Optional[str] = None):
        """
        A container object
        :param path: the path to the file
        :param md5sum: md5sum of the file contents
        :param should_exist: whether the file should exist or not
        :param contains: a list of strings that should be present in the file
        :param must_not_contain: a list of strings that should not be present
        in the file
        :param contains_regex: a list of regular expression patterns that
        should be present in the file
        :param must_not_contain_regex: a list of regular expression pattersn
        that should not be present in the file
        """
        super().__init__(contains=contains, must_not_contain=must_not_contain,
                         contains_regex=contains_regex,
                         must_not_contain_regex=must_not_contain_regex,
                         encoding=encoding)
        self.path = Path(path)
        self.md5sum = md5sum
        self.should_exist = should_exist


class WorkflowTest(object):
    """A class that contains all properties of a to be tested workflow"""

    def __init__(self, name: str, command: str,
                 tags: Optional[List[str]],
                 exit_code: int = DEFAULT_EXIT_CODE,
                 stdout: ContentTest = ContentTest(),
                 stderr: ContentTest = ContentTest(),
                 files: Optional[List[FileTest]] = None):
        """
        Create a WorkflowTest object.
        :param name: The name of the test
        :param command: The command to start the workflow
        :param exit_code: The expected exit code of the workflow
        :param stdout: a ContentTest object
        :param stderr: a ContentTest object
        :param files: a list of FileTest objects
        """
        self.name = name
        self.command = command
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.files = files or []
        self.tags = tags or []

    @classmethod
    def from_schema(cls, schema: dict):
        """Generate a WorkflowTest object from schema objects"""
        test_file_dicts = schema.get("files", [])
        test_files = [FileTest(**d) for d in test_file_dicts]

        return cls(
            name=schema["name"],
            command=schema["command"],
            tags=schema.get("tags"),
            exit_code=schema.get("exit_code", DEFAULT_EXIT_CODE),
            stdout=ContentTest(**schema.get("stdout", {})),
            stderr=ContentTest(**schema.get("stderr", {})),
            files=test_files
        )
