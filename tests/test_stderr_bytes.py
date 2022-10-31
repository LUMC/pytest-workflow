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

"""Tests the exitcode failure messages with --stderr_bytes flag active"""

import textwrap
from typing import List, Tuple  # noqa: F401  # Used in comments

import pytest

# message tests. Form: a tuple of a yaml file and expected messages.
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
def test_messages(test: str, message: str, pytester):
    pytester.makefile(".yml", textwrap.dedent(test))
    # Ideally this should be run in a LC_ALL=C environment. But this is not
    # possible due to multiple levels of process launching.
    result = pytester.runpytest("-v", "--sb", "5")
    assert message in result.stdout.str()
