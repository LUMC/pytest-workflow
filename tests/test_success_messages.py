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

import subprocess  # nosec
import tempfile
import textwrap
from pathlib import Path

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
    [""],
]


@pytest.fixture(scope="module")
def succeeding_tests_output():
    tempdir = tempfile.mkdtemp()
    test_file = Path(Path(tempdir) / Path("test_succeeding.yml"))
    with test_file.open("w") as file_handler:
        file_handler.write(SUCCEEDING_TESTS_YAML)
    process_out = subprocess.run(args=["pytest", "-v"],  # nosec
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 cwd=tempdir)
    yield process_out.stdout.decode()


@pytest.mark.parametrize(["message"], SUCCESS_MESSAGES)
def test_message_in_result(message: str, succeeding_tests_output):
    # pylint: disable=redefined-outer-name
    assert message in succeeding_tests_output
