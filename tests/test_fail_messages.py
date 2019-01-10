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
FAILURE_MESSAGE_TESTS = [
    ("""\
    - name: fail_test
      command: grep
    """,
     "The workflow exited with exit code '2' instead of '0'"),
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
     "'miaow' was not found in content while it should be there"),
    ("""\
    - name: moo file does not contain moo
      command: bash -c 'echo moo > moo.txt'
      files:
        - path: moo.txt
          must_not_contain:
            - moo
    """,
     "'moo' was found in content while it should not be there"),
    ("""\
    - name: echo miaow
      command: echo moo
      stdout:
        contains:
          - miaow
    """,
     "'miaow' was not found in stdout while it should be there"),
    ("""\
    - name: echo does not contain moo
      command: echo moo
      stdout:
        must_not_contain:
          - moo
    """,
     "moo' was found in stdout while it should not be there"),
    ("""\
    - name: fail_test
      command: grep
      stderr:
        contains:
          - "No arguments?"
    """,
     "'No arguments?' was not found in stderr while it should be there"),
    ("""\
    - name: fail_test
      command: grep
      stderr:
        must_not_contain:
          - "grep --help"
    """,
     "'grep --help' was found in stderr while it should not be there")
]  # type: List[Tuple[str,str]]


@pytest.mark.parametrize(["test", "message"], FAILURE_MESSAGE_TESTS)
def test_messages(test: str, message: str, testdir):
    testdir.makefile(".yml", textwrap.dedent(test))
    # Ideally this should be run in a LC_ALL=C environment. But this is not
    # possible due to multiple levels of process launching.
    result = testdir.runpytest("-v")
    assert message in result.stdout.str()
