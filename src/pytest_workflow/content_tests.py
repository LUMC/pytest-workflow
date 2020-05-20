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
import re
import threading
from pathlib import Path
from typing import Iterable, Optional, Set

import pytest

from .schema import ContentTest
from .workflow import Workflow


def check_content(strings: Iterable[str],
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
    found_strings: Set[str] = set()

    for line in text_lines:
        # Break the loop if all strings are found
        # Python implements fast set equality checking by checking length first
        if found_strings == strings_to_check:
            break

        for string in strings_to_check:
            if string in line:
                found_strings.add(string)
        # Remove found strings for faster searching. This should be done
        # outside of the loop above.
        strings_to_check -= found_strings
    return found_strings


def check_regex_content(patterns: Iterable[str],
                        text_lines: Iterable[str]) -> Set[str]:
    """
    Checks whether any of the patterns is present in the text lines
    It only reads the lines once and it stops reading when
    everything is found. This makes searching for patterns in large bodies of
    text more efficient.
    :param patterns: A list of regexes which is matched
    :param text_lines: The lines of text that need to be searched.
    :return: A tuple with a set of found regexes, and a set of not found
    regexes
    """

    # Create two sets. By default all strings are not found.
    regex_to_match = {re.compile(pattern) for pattern in patterns}
    found_patterns: Set[str] = set()

    for line in text_lines:
        # Break the loop if all regexes have been matched
        if not regex_to_match:
            break

        # Regexes we don't have to check anymore
        to_remove = list()
        for regex in regex_to_match:
            if re.search(regex, line):
                found_patterns.add(regex.pattern)
                to_remove.append(regex)

        # Remove found patterns for faster searching. This should be done
        # outside of the loop above.
        for regex in to_remove:
            regex_to_match.remove(regex)

    return found_patterns


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
        super().__init__(name, parent=parent)
        self.filepath = filepath
        self.content_test = content_test
        self.workflow = workflow
        self.found_strings = None
        self.found_patterns = None
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
        patterns_to_check = (self.content_test.contains_regex +
                             self.content_test.must_not_contain_regex)
        file_open = (functools.partial(gzip.open, str(self.filepath))
                     if self.filepath.suffix == ".gz" else
                     self.filepath.open)
        try:
            # Use 'rt' here explicitly as opposed to 'rb'
            with file_open(mode='rt') as file_handler:  # type: ignore  # mypy goes crazy here otherwise  # noqa: E501
                self.found_strings = check_content(
                    strings=strings_to_check,
                    text_lines=file_handler)
            # Read the file again for the regex
            with file_open(mode='rt') as file_handler:  # type: ignore  # mypy goes crazy here otherwise  # noqa: E501
                self.found_patterns = check_regex_content(
                    patterns=patterns_to_check,
                    text_lines=file_handler)
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
            ContentTestItem.from_parent(
                parent=self,
                string=string,
                should_contain=True,
                regex=False,
                content_name=self.content_name
            )
            for string in self.content_test.contains]

        test_items += [
            ContentTestItem.from_parent(
                parent=self,
                string=string,
                should_contain=False,
                regex=False,
                content_name=self.content_name
            )
            for string in self.content_test.must_not_contain]

        test_items += [
            ContentTestItem.from_parent(
                parent=self,
                string=pattern,
                should_contain=True,
                regex=True,
                content_name=self.content_name
            )
            for pattern in self.content_test.contains_regex]

        test_items += [
            ContentTestItem.from_parent(
                parent=self,
                string=pattern,
                should_contain=False,
                regex=True,
                content_name=self.content_name
            )
            for pattern in self.content_test.must_not_contain_regex]

        return test_items


class ContentTestItem(pytest.Item):
    """Item that reports if a string has been found in content."""

    def __init__(self, parent: ContentTestCollector, string: str,
                 should_contain: bool, regex: bool, content_name: str):
        """
        Create a ContentTestItem
        :param parent: A ContentTestCollector. We use a ContentTestCollector
        here and not just any pytest collector because we now can wait on the
        thread in the parent, and get its found strings when its thread is
        finished.
        :param string: The string that was searched for.
        :param should_contain: Whether the string should have been there
        :param regex: Wether we are looking for a regex
        :param content_name: the name of the content which allows for easier
        debugging if the test fails
        """
        contain = "contains" if should_contain else "does not contain"
        name = f"{contain} '{string}'"
        super().__init__(name, parent=parent)
        self.parent: ContentTestCollector = parent  # explicitly declare type
        self.should_contain = should_contain
        self.string = string
        self.content_name = content_name
        self.regex = regex

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
        if self.regex:
            assert ((self.string in self.parent.found_patterns) ==
                    self.should_contain)
        else:
            assert ((self.string in self.parent.found_strings) ==
                    self.should_contain)

    def repr_failure(self, excinfo, style=None):
        if self.parent.file_not_found:
            containing = ("containing" if self.should_contain else
                          "not containing")
            return (
                f"'{self.content_name}' does not exist and cannot be searched "
                f"for {containing} '{self.string}'."
            )
        else:
            found = "not found" if self.should_contain else "found"
            should = "should" if self.should_contain else "should not"
            return (
                f"'{self.string}' was {found} in {self.content_name} "
                f"while it {should} be there."
            )
