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

"""Tests the success messages"""

import shutil
import subprocess  # nosec
import textwrap
from pathlib import Path

from _pytest.tmpdir import TempdirFactory

import pytest

MOO_FILE = textwrap.dedent("""\
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
""")

SIMPLE_ECHO = textwrap.dedent("""\
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
""")

FAILING_GREP = textwrap.dedent("""\
- name: failing grep
  command: "grep"
  stdout:
    must_not_contain:
      - "grep"  # stdout should be empty
  stderr:
    contains:
      - "'grep --help'"
  exit_code: 2
""")

SUCCEEDING_TESTS_YAML = MOO_FILE + SIMPLE_ECHO + FAILING_GREP

SUCCESS_MESSAGES = [
    ["test_succeeding.yml::moo file::exit code should be 0 PASSED"],
    ["test_succeeding.yml::moo file::moo.txt::content::contains 'moo' PASSED"],
    ["test_succeeding.yml::moo file::moo.txt::content::does not contain 'Cock a doodle doo' PASSED"],  # noqa: E501
    ["test_succeeding.yml::moo file::moo.txt::md5sum PASSED"],
    ["test_succeeding.yml::moo file::moo.txt::should exist PASSED"],
    ["test_succeeding.yml::simple echo::exit code should be 0 PASSED"],
    ["test_succeeding.yml::simple echo::moo.txt::should not exist PASSED"],
    ["test_succeeding.yml::simple echo::stdout::contains 'moo' PASSED"],
    ["test_succeeding.yml::simple echo::stdout::does not contain 'Cock a doodle doo' PASSED"],  # noqa: E501
    ["test_succeeding.yml::simple echo::exit code should be 0 PASSED"],
    ["test_succeeding.yml::failing grep::exit code should be 2 PASSED"],
    ["test_succeeding.yml::failing grep::stdout::does not contain 'grep' PASSED"],  # noqa: E501
    ["test_succeeding.yml::failing grep::stderr::contains ''grep --help''"],  # noqa: E501
    ["'moo file' with command 'bash -c 'echo moo > moo.txt'' in"],
    ["command: 'bash -c 'echo moo > moo.txt'' done."]
]


@pytest.fixture(scope="session")
def succeeding_tests_output(tmpdir_factory: TempdirFactory):
    """This fixture was written because the testdir function has a default
    scope of 'function'. This is very inefficient when testing multiple
    success messages in the output as the whole test yaml with all commands
    has to be run again.
    This fixture runs the succeeding tests once with pytest -v"""
    tempdir = str(tmpdir_factory.mktemp("succeeding_tests"))
    test_file = Path(Path(tempdir) / Path("test_succeeding.yml"))
    with test_file.open("w") as file_handler:
        file_handler.write(SUCCEEDING_TESTS_YAML)
    process_out = subprocess.run(args=["pytest", "-v"],  # nosec
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 cwd=tempdir)
    yield process_out.stdout.decode()
    shutil.rmtree(tempdir)


@pytest.mark.parametrize(["message"], SUCCESS_MESSAGES)
def test_message_in_result(message: str, succeeding_tests_output):
    # pylint: disable=redefined-outer-name
    assert message in succeeding_tests_output


def test_message_success_no_errors_or_fails(succeeding_tests_output):
    # pylint: disable=redefined-outer-name
    assert "ERROR" not in succeeding_tests_output
    assert "FAIL" not in succeeding_tests_output


def test_message_directory_kept_no_errors_or_fails(testdir):
    testdir.makefile(".yml", test=SUCCEEDING_TESTS_YAML)
    result = testdir.runpytest("-v", "--keep-workflow-wd")
    assert "ERROR" not in result.stdout.str()
    assert "FAIL" not in result.stdout.str()
