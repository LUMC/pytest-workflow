#!/usr/bin/env python3

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

# This file contains tests for the schema for the yaml file

import textwrap

import pytest


SUCCEEDING_TESTS_YAML = textwrap.dedent("""\
- name: moo file
  # Gruesome command injection here. This is for testing purposes only.
  # Do not try this at home.
  command: "bash -c 'echo moo > moo.txt'"
  files:
    - path: "moo.txt"
      contains:
        - "moo"
      must_not_contain:
        - "Cock a doodle doo"  # Unless our cow has severe identity disorders
      md5sum: e583af1f8b00b53cda87ae9ead880224

- name: simple echo
  command: "echo moo"
  files:
    - path: "moo.txt"
      should_exist: false
  stdout:
    contains:
      - "moo"
    must_not_contain:
      - "Cock a doodle doo"

- name: failing grep
  command: "grep"
  stdout:
    must_not_contain:
      - "grep"  # stdout should be empty
  stderr:
    contains:
      - 'Usage: grep'
      - "Try 'grep --help'"
  exit_code: 2
""")

SUCCESS_MESSAGES = [
    "bla",
]


@pytest.fixture(scope="class")
def succeeding_tests(testdir) -> str:
    testdir.makefile(".yml", succeeding_tests=SUCCEEDING_TESTS_YAML)
    result = testdir.runpytest("-v")
    yield result.stdout.str()


class TestSuccessMessages:
    def __init__(self, succeeding_tests):
        self.results = succeeding_tests

    @pytest.mark.parametrize(["message"], SUCCESS_MESSAGES)
    def message_in_result(self, message: str):
        assert message in self.results
