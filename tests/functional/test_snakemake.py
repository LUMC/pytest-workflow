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

from _pytest.pytester import Testdir

import pytest

_snakemake_yaml_string = ("""
- name: test-dry-run
  command: snakemake -n -r -p -s SimpleSnakefile --config N_LINES_TO_READ=1
- name: test-config-missing
  command: snakemake -n -r -p -s SimpleSnakefile
  exit_code: 1
  stdout:
    contains:
      - "You must set --config N_LINES_TO_READ=<a value>."
- name: test-config-wrong-type
  command: snakemake -n -r -p -s SimpleSnakefile --config N_LINES_TO_READ=one
  exit_code: 1
  stdout:
    contains:
      - "N_LINES_TO_READ must be an integer."
- name: test-config-invalid-value
  command: snakemake -n -r -p -s SimpleSnakefile --config N_LINES_TO_READ=-1
  exit_code: 1
  stdout:
    contains:
      - "N_LINES_TO_READ must at least be 1."
- name: test-snakemake-run
  command: snakemake -r -p -s SimpleSnakefile --config N_LINES_TO_READ=500
  files:
    - path: rand/0.txt
    - path: rand/1.txt
    - path: rand/2.txt
    - path: rand/3.txt
    - path: rand/4.txt
    - path: rand/5.txt
    - path: rand/6.txt
    - path: rand/7.txt
    - path: rand/8.txt
    - path: rand/9.txt
    - path: b64/0.txt
    - path: b64/1.txt
    - path: b64/2.txt
    - path: b64/3.txt
    - path: b64/4.txt
    - path: b64/5.txt
    - path: b64/6.txt
    - path: b64/7.txt
    - path: b64/8.txt
    - path: b64/9.txt
    - path: randgz/0.txt.gz
    - path: randgz/1.txt.gz
    - path: randgz/2.txt.gz
    - path: randgz/3.txt.gz
    - path: randgz/4.txt.gz
    - path: randgz/5.txt.gz
    - path: randgz/6.txt.gz
    - path: randgz/7.txt.gz
    - path: randgz/8.txt.gz
    - path: randgz/9.txt.gz
    - path: all_data.gz
  stderr:
    contains:
      - "Building DAG of jobs..."
      - "(100%) done"
      - "Complete log:"
""")


@pytest.fixture
def snakefile_contents():
    snake_path = (Path(__file__).parent.parent / Path("pipelines") /
                  Path("snakemake") / Path("SimpleSnakefile"))
    with snake_path.open("r") as snake_handle:
        return snake_handle.read()


@pytest.mark.functional
def test_snakemake(testdir: Testdir, snakefile_contents):
    testdir.makefile(ext="", SimpleSnakefile=snakefile_contents)
    testdir.makefile(ext=".yml", test_snakemake=_snakemake_yaml_string)
    result = testdir.runpytest("-v")
    exit_code = result.ret
    assert exit_code == 0
