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


class ContentTestCollector(pytest.Collector):
    def __init__(self, name: str, parent: pytest.Collector,
                 content: Iterable[str], content_test: ContentTest):
        super().__init__(name, parent=parent)
        self.content = content
        self.content_test = content_test

    def collect(self):
        found_strings = check_content(
            self.content_test.contains + self.content_test.must_not_contain,
            self.content)

        test_items = []

        test_items += [
            ContentTestItem(
                parent=self,
                string=string,
                should_contain=True,
                contains=string in found_strings
            )
            for string in self.content_test.contains]

        test_items += [
            ContentTestItem(
                parent=self,
                string=string,
                should_contain=False,
                contains=string in found_strings
            )
            for string in self.content_test.must_not_contain]

        return test_items


class ContentTestItem(pytest.Item):
    """Item that reports if a string has been found in content."""

    def __init__(self, parent: pytest.Collector, string: str,
                 should_contain: bool, contains: bool):
        """
        Create a ContentTestItem
        :param parent: A pytest collector
        :param string: The string that was searched for.
        :param should_contain: Whether the string should have been there
        :param result:
        """
        contain = "contains" if should_contain else "does not contain"
        name = "{0} '{1}'".format(contain, string)
        super().__init__(name, parent=parent)
        self.should_contain = should_contain
        self.string = string
        self.contains = contains

    def runtest(self):
        assert self.contains == self.should_contain

    def repr_failure(self, excinfo):
        # pylint: disable=unused-argument
        # excinfo needed for pytest.
        message = (
            "'{string}' was {found} in {content} "
            "while it {should} be there."
        ).format(
            string=self.string,
            found="not found" if self.should_contain else "found",
            content=self.parent.name,
            should="should" if self.should_contain else "should not"
        )
        return message
