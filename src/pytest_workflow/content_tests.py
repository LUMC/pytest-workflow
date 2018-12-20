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
from typing import Iterable, List, Set, Tuple

import pytest

from .schema import ContentTest


def check_content(strings: List[str],
                  text_lines: Iterable[str]) -> Tuple[Set[str], Set[str]]:
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
    # Make a copy of the list here to prevent aliasing.
    # This should not be refactored back to strings.
    not_found_strings = set(strings)

    # By default all strings are not found.
    found_strings = set()

    for line in text_lines:
        # Break the loop if the list of not found strings is empty.
        if len(not_found_strings) == 0:
            break
        for string in not_found_strings:
            if string in line:
                found_strings.add(string)
        # Difference update removes all that is in found_strings from
        # not_found_strings
        not_found_strings.difference_update(found_strings)

    # Set conversion has to be after the loop. Set is not allowed to change
    # size during iteration.
    common_strings = found_strings.intersection(not_found_strings)
    if common_strings != set():
        raise ValueError(
            "Keys can not be simultaneously be found and not found. "
            "Offending keys: {0}".format(common_strings))

    return found_strings, not_found_strings


def file_to_string_generator(filepath: Path) -> Iterable[str]:
    """
    Turns a file into a line generator.
    :param filepath: the file path
    :return: yields lines of the file
    """
    with filepath.open("r") as f:  # Use 'r' here explicitly as opposed to 'rb'
        for line in f:
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
    found_strings, not_found_strings = check_content(
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
            result=string in not_found_strings
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
