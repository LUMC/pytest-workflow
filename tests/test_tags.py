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

TAG_TESTS = textwrap.dedent("""\
- name: three
  command: echo 3
  tags:
    - odd
    - prime
- name: three again
  command: echo 3
  tags:
    - odd
    - prime
    - again
- name: four
  command: echo 4
  tags:
    - even
- name: nine
  command: echo 9
  tags:
    - odd
""")


def test_name_tag_with_space(pytester):
    pytester.makefile(".yml", test_tags=TAG_TESTS)
    result = pytester.runpytest("-v", "--tag", "three again").stdout.str()
    assert "three again" in result
    assert "four" not in result
    assert "nine" not in result


def test_name_tag(pytester):
    pytester.makefile(".yml", test_tags=TAG_TESTS)
    result = pytester.runpytest("-v", "--tag", "three").stdout.str()
    assert "three" in result
    assert "three again" not in result
    assert "four" not in result
    assert "nine" not in result


def test_category_tag(pytester):
    pytester.makefile(".yml", test_tags=TAG_TESTS)
    result = pytester.runpytest("-v", "--tag", "odd").stdout.str()
    assert "three" in result
    assert "three again" in result
    assert "nine" in result
    assert "four" not in result


def test_category_tag2(pytester):
    pytester.makefile(".yml", test_tags=TAG_TESTS)
    result = pytester.runpytest("-v", "--tag", "even").stdout.str()
    assert "three" not in result
    assert "three again" not in result
    assert "four" in result
    assert "nine" not in result
