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

from pytest_workflow.content_tests import check_content

LICENSE = Path(__file__).parent / "content_files" / "LICENSE"
LICENSE_ZIPPED = LICENSE.parent / "LICENSE.gz"

# Yes we are checking the AGPLv3+. I am pretty sure some strings will not be
# there
SUCCEEDING_TESTS = [
    # Test both finding and not finding
    (["When we speak of free software"],
     ["All hail Google, Guardian of our privacy"]),
    # Test finding, this should break the loop in the function
    (["When we speak of free software"], []),
    # Test not finding
    ([], ["All hail Google, Guardian of our privacy"])
]

REGEX_TESTS = [
    (["^  When we speak"], [".*Google.*"]),
    (["When we speak"], ["^When we speak"])
]


@pytest.mark.parametrize(["contains_strings", "does_not_contain_strings"],
                         SUCCEEDING_TESTS)
def test_check_content_succeeding(contains_strings, does_not_contain_strings):
    all_strings = set(contains_strings).union(set(does_not_contain_strings))
    with LICENSE.open("rt") as license_h:
        found_strings, _ = check_content(
            list(all_strings), [], license_h)
    assert set(contains_strings) == found_strings
    assert set(does_not_contain_strings) == all_strings - found_strings


@pytest.mark.parametrize(["contains_regex", "does_not_contain_regex"],
                         REGEX_TESTS)
def test_check_regex_content_succeeding(contains_regex,
                                        does_not_contain_regex):
    all_regex = set(contains_regex).union(set(does_not_contain_regex))
    with LICENSE.open("rt") as license_h:
        _, found_regex = check_content(
            [], list(all_regex), license_h)
    assert set(contains_regex) == found_regex
    assert set(does_not_contain_regex) == all_regex - found_regex


def test_multiple_finds_one_line():
    content = [
        "I have a dream that one day this nation will rise up and live out",
        "the true meaning of its creed: \"We hold these truths to be",
        "self-evident: that all men are created equal.\""]
    contains = ["dream", "day", "nation", "creed", "truths"]
    found_strings, _ = check_content(contains, [], content)
    assert set(contains) == found_strings
