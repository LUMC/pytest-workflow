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
import functools
import gzip
import threading
from pathlib import Path
from typing import Iterable, List, Optional, Set

import pytest

from .schema import ContentTest
from .workflow import Workflow


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
    found_strings = set()  # type: Set[str]

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
    Turns a file into a line generator. Files ending with .gz are automatically
    decompressed.
    :param filepath: the file path
    :return: yields lines of the file
    """
    file_open = (functools.partial(gzip.open, str(filepath))
                 if filepath.suffix == ".gz" else
                 filepath.open)
    # Use 'rt' here explicitly as opposed to 'rb'
    with file_open(mode='rt') as file_handler:  # type: ignore  # mypy goes crazy here otherwise  # noqa: E501
        for line in file_handler:
            yield line


class ContentTestCollector(pytest.Collector):
    def __init__(self, name: str, parent: pytest.Collector,
                 filepath: Path,
                 content_test: ContentTest,
                 workflow: Workflow,
                 content_name: Optional[str] = None):
        """
        Creates a content test collector
        :param name: Name of the thing which contents are tested
        :param parent: a pytest.Collector object
        :param filepath: the file that contains the content
        :param content_test: a ContentTest object.
        :param workflow: the workflow is running.
        :param content_name: The name of the content that will be displayed if
        the test fails. Defaults to filepath.
        """
        # pylint: disable=too-many-arguments
        # Cannot think of a better way to do this.
        super().__init__(name, parent=parent)
        self.filepath = filepath
        self.content_test = content_test
        self.workflow = workflow
        self.found_strings = None
        self.thread = None
        # We check the contents of files. Sometimes files are not there. Then
        # content can not be checked. We save FileNotFoundErrors in this
        # boolean.
        self.file_not_found = False
        self.content_name = content_name or str(filepath)

    def find_strings(self):
        """Find the strings that are looked for in the given file

        When a file we test is not produced, we save the FileNotFoundError so
        we can give an accurate repr_failure."""
        self.workflow.wait()
        strings_to_check = (self.content_test.contains +
                            self.content_test.must_not_contain)
        try:
            self.found_strings = check_content(
                strings=strings_to_check,
                text_lines=file_to_string_generator(self.filepath))
        except FileNotFoundError:
            self.file_not_found = True

    def collect(self):
        # A thread is started that looks for the strings and collection can go
        # on without hindrance. The thread is passed to the items, so they can
        # wait on the thread to complete.
        self.thread = threading.Thread(target=self.find_strings)
        self.thread.start()
        test_items = []

        test_items += [
            ContentTestItem(
                parent=self,
                string=string,
                should_contain=True,
                content_name=self.content_name
            )
            for string in self.content_test.contains]

        test_items += [
            ContentTestItem(
                parent=self,
                string=string,
                should_contain=False,
                content_name=self.content_name
            )
            for string in self.content_test.must_not_contain]

        return test_items


class ContentTestItem(pytest.Item):
    """Item that reports if a string has been found in content."""

    def __init__(self, parent: ContentTestCollector, string: str,
                 should_contain: bool, content_name: str):
        """
        Create a ContentTestItem
        :param parent: A ContentTestCollector. We use a ContentTestCollector
        here and not just any pytest collector because we now can wait on the
        thread in the parent, and get its found strings when its thread is
        finished.
        :param string: The string that was searched for.
        :param should_contain: Whether the string should have been there
        :param content_name: the name of the content which allows for easier
        debugging if the test fails
        """
        contain = "contains" if should_contain else "does not contain"
        name = "{0} '{1}'".format(contain, string)
        super().__init__(name, parent=parent)
        self.should_contain = should_contain
        self.string = string
        self.content_name = content_name

    def runtest(self):
        """Only after a workflow is finished the contents of files and logs are
        read. The ContentTestCollector parent reads each file once. This is
        done in its thread. We wait for this thread to complete. Then we check
        all the found strings in the parent.
        This way we do not have to read each file one time per ContentTestItem
        this makes content checking much faster on big files (NGS > 1 GB files)
        were we are looking for multiple words (variants / sequences). """
        # Wait for thread to complete.
        self.parent.thread.join()
        assert not self.parent.file_not_found
        assert ((self.string in self.parent.found_strings) ==
                self.should_contain)

    def repr_failure(self, excinfo):
        # pylint: disable=unused-argument
        # excinfo needed for pytest.
        if self.parent.file_not_found:
            return (
                "'{content}' does not exist and cannot be searched "
                "for {containing} '{string}'."
            ).format(
                content=self.content_name,
                containing="containing" if self.should_contain
                else "not containing",
                string=self.string)

        else:
            return (
                "'{string}' was {found} in {content} "
                "while it {should} be there."
            ).format(
                string=self.string,
                found="not found" if self.should_contain else "found",
                content=self.content_name,
                should="should" if self.should_contain else "should not"
            )
