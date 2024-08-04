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

"""Tests the failure messages"""

import textwrap
from typing import List, Tuple  # noqa: F401  # Used in comments

import pytest

# message tests. Form: a tuple of a yaml file and expected messages.
FAILURE_MESSAGE_TESTS: List[Tuple[str, str]] = [
    ("""\
    - name: fail_test
      command: grep
    """,
     "'fail_test' exited with exit code '2' instead of '0'"),
    ("""\
    - name: exitcode_test
      command: bash -c 'printf "This code had an error" >&2 ; exit 12'
    """,
     "stderr: This code had an error"),
    ("""\
    - name: create file
      command: echo moo
      files:
        - path: moo
    """,
     "moo' does not exist while it should"),
    ("""\
    - name: echo something
      command: touch moo
      files:
        - path: moo
          should_exist: false
    """,
     "moo' does exist while it should not"),
    ("""\
    - name: moo file
      command: bash -c 'echo moo > moo.txt'
      files:
        - path: moo.txt
          md5sum: e583af1f8b00b53cda87ae9ead880225
    """,
     "Observed md5sum 'e583af1f8b00b53cda87ae9ead880224' not equal to "
     "expected md5sum 'e583af1f8b00b53cda87ae9ead880225' for file"),
    ("""\
    - name: moo file contains miaow
      command: bash -c 'echo moo > moo.txt'
      files:
        - path: moo.txt
          contains:
            - miaow
    """,
     "moo_file_contains_miaow/moo.txt while it should be there"),
    ("""\
    - name: moo file does not contain moo
      command: bash -c 'echo moo > moo.txt'
      files:
        - path: moo.txt
          must_not_contain:
            - moo
    """,
     "moo_file_does_not_contain_moo/moo.txt while it should not be there"),
    ("""\
    - name: echo miaow
      command: echo moo
      stdout:
        contains:
          - miaow
    """,
     "'miaow' was not found in 'echo miaow': stdout while it should be there"),
    ("""\
    - name: echo does not contain moo
      command: echo moo
      stdout:
        must_not_contain:
          - moo
    """,
     "moo' was found in 'echo does not contain moo': stdout while "
     "it should not be there"),
    ("""\
    - name: fail_test
      command: bash -c 'echo "" >&2'
      stderr:
        contains:
          - "No arguments?"
    """,
     "'No arguments?' was not found in 'fail_test': stderr "
     "while it should be there"),
    ("""\
   - name: fail_test
     command: bash -c 'echo "grep --help" >&2'
     stderr:
        must_not_contain:
          - "grep --help"
    """,
     "'grep --help' was found in 'fail_test': stderr while "
     "it should not be there"),
    ("""\
    - name: simple echo
      command: "echo Hello, world"
      stdout:
        contains_regex:
          - 'Hello .*'
     """,
     "'Hello .*' was not found in 'simple echo': stdout while it should be "
     "there."),
    ("""\
    - name: simple echo
      command: "echo Hello, world"
      stdout:
        must_not_contain_regex:
          - "^He.*"
     """,
     "'^He.*' was found in 'simple echo': stdout while it should not be "
     "there."),
    ("""\
    - name: to file
      command: bash -c 'echo Hello, world > file.txt'
      files:
        - path: file.txt
          contains_regex:
            - 'Hello .*'
     """,
     "to file::file.txt::content::contains 'Hello .*'"),
    ("""\
    - name: to file
      command: bash -c 'echo Hello, world > file.txt'
      files:
        - path: file.txt
          must_not_contain_regex:
            - "^He.*"
     """,
     "to file::file.txt::content::does not contain '^He.*"),
]


@pytest.mark.parametrize(["test", "message"], FAILURE_MESSAGE_TESTS)
def test_messages(test: str, message: str, pytester):
    pytester.makefile(".yml", textwrap.dedent(test))
    # Ideally this should be run in a LC_ALL=C environment. But this is not
    # possible due to multiple levels of process launching.
    result = pytester.runpytest("-v")
    assert message in result.stdout.str()


EXITCODE_MESSAGE_TESTS: List[Tuple[str, str]] = [
    ("""\
    - name: stderr_bytes_stderr_test
      command: bash -c 'printf "This code had an error" ; exit 12'
    """,
     "stdout: error"),
    ("""\
    - name: stderr_bytes_stdout_test
      command: bash -c 'printf "This code had an error" >&2 ; exit 12'
    """,
     "stderr: error")
]


@pytest.mark.parametrize(["test", "message"], EXITCODE_MESSAGE_TESTS)
def test_messages_exitcode(test: str, message: str, pytester):
    pytester.makefile(".yml", textwrap.dedent(test))
    # Ideally this should be run in a LC_ALL=C environment. But this is not
    # possible due to multiple levels of process launching.
    result = pytester.runpytest("-v", "--sb", "5")
    assert message in result.stdout.str()


def test_invalid_test_capture(pytester):
    test_yml_contents = """\
    - name: tee test
      command: bash -c "echo foo"
      stdout:
        contains:
          - foo
    """
    pytester.makefile(".yml", textwrap.dedent(test_yml_contents))
    result = pytester.runpytest("-v", "-s")
    assert (
        "Invalid test 'tee test': stdout, unknown file to validate"
        in result.stdout.str()
    )
