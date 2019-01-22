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


@pytest.fixture
def simple_wdl_yaml():
    yaml_path = Path(__file__).parent / Path("simple_wdl_test_cases.yml")
    with yaml_path.open("r") as yaml_handle:
        return yaml_handle.read()


@pytest.fixture
def simple_wdl_contents():
    wdl_path = (Path(__file__).parent.parent / Path("pipelines") /
                  Path("wdl") / Path("simple.wdl"))
    with wdl_path.open("r") as wdl_handle:
        return wdl_handle.read()


@pytest.mark.functional
def test_cromwell(testdir, simple_wdl_yaml, simple_wdl_contents):
    testdir.makefile(ext=".wdl", simple=simple_wdl_contents)
    testdir.makefile(ext=".yml", test_cromwell=simple_wdl_yaml)
    result = testdir.runpytest("-v")
    exit_code = result.ret
    assert exit_code == 0
    assert "simple wdl" in result.stdout.str()
