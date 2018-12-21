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

"""This contains all the classes and methods for content testing of files
and logs.

The design philosophy here was that each piece of text should only be read
once."""

from pathlib import Path
from typing import Iterable, List, Set

import pytest

from .schema import ContentTest


def check_content(strings: List[str],
                  text_lines: Iterable[str]) -> Set[str]:
    """
    Checks whether any of the strings is present in the text lines
    It only reads the lines once and it stops reading when
    everything is found. This makes searching for strings in large bodies of
    text more efficient.
    :param strings: A list of strings for which the present is checked
    :param text_lines: The lines of text that need to be searched.
    :return: A tuple with a set of found strings, and a set of not found
    strings
    """

    # Create two sets. By default all strings are not found.
    strings_to_check = set(strings)
    found_strings = set()

    for line in text_lines:
        # Break the loop if all strings are found
        # First do length check for speed as this runs every loop.
        if len(found_strings) == len(strings_to_check):
            # Then true check
            if found_strings == strings_to_check:
                break
            else:
                raise ValueError(
                    "The number of strings found is equal to the "
                    "number of strings to be checked. But the"
                    " sets are not equal. Please contact the "
                    "developers to fix this issue.")

        for string in strings_to_check:
            if string not in found_strings and string in line:
                found_strings.add(string)

    if not found_strings.issubset(strings_to_check):
        raise ValueError(
            "Strings where found that were not searched for. Please contact"
            " the developers to fix this issue. \n" +
            "Searched for strings: {0}\n".format(strings_to_check) +
            "Found strings: {0}\n".format(found_strings)
        )

    return found_strings


def file_to_string_generator(filepath: Path) -> Iterable[str]:
    """
    Turns a file into a line generator.
    :param filepath: the file path
    :return: yields lines of the file
    """
    # Use 'r' here explicitly as opposed to 'rb'
    with filepath.open("r") as file_handler:
        for line in file_handler:
            yield line


# Technically the function below does the same as a pytest Collector. It
# returns a list of pytest Items. The reason that a pytest Collector was not
# chosen here is that this function performs only one test on a file. It reads
# the file and checks the contents. Also a pytest Collector is a node that
# needs to have parents and itself becomes a parent. This hierarchy was not
# considered necessary, as it performs only one test.
def generate_content_tests(
        parent: pytest.Collector,
        text_lines: Iterable[str],
        contains: List[str],
        must_not_contain: List[str],
        test_name_prefix: str = "") -> List[pytest.Item]:
    """
    Checks text lines for content. Spawns test items that indicate whether
    certain strings have been found or not.
    :param parent: The parent for the test items.
    :param text_lines: The lines of text to search.
    :param contains: The strings that should be in the text lines
    :param must_not_contain: The strings that should not be in the text lines
    :param test_name_prefix: a text prefix for the test name.
    :return: A list of pytest Items
    """
    found_strings = check_content(
        contains + must_not_contain, text_lines)

    test_items = []

    test_items += [
        GenericTest(
            name="{0}contains '{1}'".format(test_name_prefix, string),
            parent=parent,
            result=string in found_strings
        )
        for string in contains]

    test_items += [
        GenericTest(
            name="{0}does not contain '{1}".format(test_name_prefix, string),
            parent=parent,
            result=string not in found_strings
        )
        for string in must_not_contain]

    return test_items


def generate_log_tests(
        parent: pytest.Collector,
        log: bytes,
        log_test: ContentTest,
        prefix: str) -> List[pytest.Item]:
    """A helper function that calls generate_content_tests and does
    the necessary conversions for workflow log testing."""
    return generate_content_tests(
        parent=parent,
        # Convert log bytestring to unicode strings
        text_lines=log.decode().splitlines(),
        contains=log_test.contains,
        must_not_contain=log_test.must_not_contain,
        test_name_prefix=prefix)


class GenericTest(pytest.Item):
    """Test that can be used to report a failing or succeeding test
    in the log"""

    def __init__(self, name: str, parent: pytest.Collector, result: bool):
        """
        Create a GenericTest item
        :param name: The name of the test
        :param parent: A pytest Collector from which the test originates
        :param result: Whether the test has succeeded.
        """
        super().__init__(name, parent=parent)
        self.result = result

    def runtest(self):
        assert self.result
