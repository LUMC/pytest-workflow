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
def snakefile_yaml():
    yaml_path = Path(__file__).parent / Path("simple_snakefile_test_cases.yml")
    with yaml_path.open("r") as yaml_handle:
        return yaml_handle.read()


@pytest.fixture
def snakefile_contents():
    snake_path = (Path(__file__).parent.parent / Path("pipelines") /
                  Path("snakemake") / Path("SimpleSnakefile"))
    with snake_path.open("r") as snake_handle:
        return snake_handle.read()


@pytest.mark.functional
def test_snakemake(testdir, snakefile_contents, snakefile_yaml):
    testdir.makefile(ext="", SimpleSnakefile=snakefile_contents)
    testdir.makefile(ext=".yml", test_snakemake=snakefile_yaml)
    result = testdir.runpytest("-v", "--keep-workflow-wd-on-fail")
    exit_code = result.ret
    assert exit_code == 0
