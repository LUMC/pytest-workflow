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

"""This contents all the tests for the content functions in pytest-workflow"""

from pathlib import Path

import pytest

from pytest_workflow.content_tests import check_content, \
    file_to_string_generator

LICENSE = Path(__file__).parent / Path("content_files") / Path("LICENSE")

# Yes we are checking the AGPLv3+. I am pretty sure some strings will not be
# there
tests = [
    # Test both finding and not finding
    {"When we speak of free software": True,
     "All hail Google, Guardian of our privacy": False},
    # Test finding, this should break the loop in the function
    {"When we speak of free software": True},
    # Test not finding
    {"All hail Google, Guardian of our privacy": False}
]


@pytest.mark.parametrize(["input_strings", "expected_output"],
                         [(list(test.keys()), test) for test in tests])
def test_check_content(input_strings, expected_output):
    assert check_content(
        input_strings, file_to_string_generator(LICENSE)) == expected_output


def test_file_to_string_iterator():
    license_iterator = file_to_string_generator(LICENSE)
    # This was checked using `wc -l`
    assert len(list(license_iterator)) == 661
