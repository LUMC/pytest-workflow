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

from pathlib import Path

import pytest

from pytest_workflow.util import is_in_dir, replace_whitespace


WHITESPACE_TESTS = [
    ("bla\nbla", "bla_bla"),
    ("bla\tbla", "bla_bla"),
    ("bla bla", "bla_bla"),
    ("bla\t\n  \n \t   bla", "bla_bla"),
    ("bla      bla", "bla_bla")
]


@pytest.mark.parametrize(["string", "result"], WHITESPACE_TESTS)
def test_replace_whitespace(string, result):
    assert replace_whitespace(string) == result


IN_DIR_TESTS = [
    ("/my/parent/subdir/subdir/child", "/my/parent", True),
    ("/my/parent-dir/child", "/my/parent", False),  # Issue 95
    ("relparent/subdir/child", "relparent", True),
    ("simple", "simple/parent", False)
]

@pytest.mark.parametrize(["child", "parent", "in_dir"], IN_DIR_TESTS)
def test_is_in_dir(child: str, parent: str, in_dir: bool):
    assert is_in_dir(Path(child), Path(parent)) is in_dir
