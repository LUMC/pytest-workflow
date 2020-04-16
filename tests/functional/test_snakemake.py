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

SNAKEFILE_YAML = (Path(__file__).parent /
                  Path("simple_snakefile_test_cases.yml"))
SNAKEFILE = (Path(__file__).parent.parent /
             Path("pipelines", "snakemake", "SimpleSnakefile"))


@pytest.mark.functional
def test_snakemake(testdir):
    testdir.makefile(ext="", SimpleSnakefile=SNAKEFILE.read_text())
    testdir.makefile(ext=".yml", test_snakemake=SNAKEFILE_YAML.read_text())
    result = testdir.runpytest("-v", "--keep-workflow-wd-on-fail")
    exit_code = result.ret
    assert exit_code == 0
