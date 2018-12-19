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
and logs."""

from pathlib import Path
from typing import Dict, Iterable, List

from . import GenericTest
import pytest


def check_content(strings: List[str], text: Iterable[str]) -> Dict[str, bool]:
    # Make a copy of the list here to prevent aliasing.
    not_found_strings = list(strings)
    # By default all strings are not found.
    found_dictionary = {key: False for key in not_found_strings}

    for line in text:
        for string in not_found_strings:
            if string in line:
                found_dictionary[string] = True
                not_found_strings.remove(string)
        # Break the loop if the list of not found strings is empty.
        if not not_found_strings:
            break
    return found_dictionary


def file_to_string_generator(filepath: Path) -> Iterable[str]:
    with filepath.open("r") as f:  # Use 'r' here explicitly as opposed to 'rb'
        for line in f:
            yield line


def generate_content_tests(
        parent: pytest.Collector,
        content: Iterable[str],
        contains: List[str],
        must_not_contain: List[str],
        prefix: str = "") -> List[pytest.Item]:
    found_dictionary = check_content(contains + must_not_contain, content)

    test_items = []

    # Check whether `contains` strings have been found
    test_items += [
        GenericTest(
            name=prefix + "contains '{0}'".format(string),
            parent=parent,
            result=found_dictionary[string]
        )
        for string in contains]

    # Check whether `must_not_contain` strings have been found
    test_items += [
        GenericTest(
            name=prefix + "does not contain '{0}".format(string),
            parent=parent,
            result=not found_dictionary[string]  # If not found, result should
            # be True, so the test succeeds.
        )
        for string in must_not_contain]

    return test_items
