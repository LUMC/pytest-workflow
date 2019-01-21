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

import textwrap

import pytest

MARKER_TESTS = textwrap.dedent("""\
- name: three
  command: echo 3
  markers:
    - odd
    - prime
- name: three again
  command: echo 3
  markers:
    - odd
    - prime
    - again
- name: four
  command: echo 4
  markers:
    - even
- name: nine
  command: echo 9
  markers:
    - odd
""")


def test_name_marker_with_space(testdir):
    testdir.makefile(".yml", test_markers=MARKER_TESTS)
    result = testdir.runpytest("-v", "-m", "three_again").stdout.str()
    assert "three again" in result
    assert "four" not in result
    assert "nine" not in result


