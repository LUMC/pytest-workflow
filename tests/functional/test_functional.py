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

SIMPLE_WDL_YAML = Path(__file__).parent / "simple_wdl_test_cases.yml"
SNAKEFILE_YAML = Path(__file__).parent / "simple_snakefile_test_cases.yml"
NEXTFLOW_YAML = Path(__file__).parent / "simple_nextflow_test_cases.yml"
PIPELINE_DIR = Path(__file__).parent.parent / "pipelines"
SIMPLE_WDL = Path(PIPELINE_DIR, "wdl", "simple.wdl")
SIMPLE_WDL_JSON = Path(PIPELINE_DIR, "wdl", "simple.json")
SIMPLE_WDL_OPTIONS_JSON = Path(PIPELINE_DIR, "wdl", "simple.options.json")
SNAKEFILE = Path(PIPELINE_DIR, "snakemake", "SimpleSnakefile")
NEXTFLOWFILE = Path(PIPELINE_DIR, "nextflow", "nextflow_testpipeline.nf")


@pytest.mark.functional
def test_cromwell(pytester):
    pytester.makefile(ext=".json", simple=SIMPLE_WDL_JSON.read_text())
    pytester.makefile(ext=".wdl", simple=SIMPLE_WDL.read_text())
    pytester.makefile(ext=".yml", test_wdl=SIMPLE_WDL_YAML.read_text())
    pytester.makefile(ext=".options.json",
                      simple=SIMPLE_WDL_OPTIONS_JSON.read_text())
    result = pytester.runpytest("-v", "--tag", "cromwell",
                                "--keep-workflow-wd-on-fail")
    exit_code = result.ret
    assert exit_code == 0
    assert "simple wdl" in result.stdout.str()


@pytest.mark.functional
def test_miniwdl(pytester):
    pytester.makefile(ext=".json", simple=SIMPLE_WDL_JSON.read_text())
    pytester.makefile(ext=".wdl", simple=SIMPLE_WDL.read_text())
    pytester.makefile(ext=".yml", test_wdl=SIMPLE_WDL_YAML.read_text())
    result = pytester.runpytest("-v", "--tag", "miniwdl",
                                "--keep-workflow-wd-on-fail")
    assert result.ret == 0


@pytest.mark.functional
def test_snakemake(pytester):
    pytester.makefile(ext="", SimpleSnakefile=SNAKEFILE.read_text())
    pytester.makefile(ext=".yml", test_snakemake=SNAKEFILE_YAML.read_text())
    result = pytester.runpytest("-v", "--keep-workflow-wd-on-fail")
    exit_code = result.ret
    assert exit_code == 0


@pytest.mark.functional
def test_nextflow(pytester):
    pytester.makefile(ext=".nf",
                      nextflow_testpipeline=NEXTFLOWFILE.read_text())
    pytester.makefile(ext=".yml", test_nextflow=NEXTFLOW_YAML.read_text())
    result = pytester.runpytest("-v", "--keep-workflow-wd-on-fail")
    assert result.ret == 0
