#!/usr/bin/env python3

# Copyright (C) 2018 Leiden University Medical Center
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/

# This file contains tests for the schema for the yaml file

from pathlib import Path

import pytest

from pytest_workflow.schema import validate_schema

import yaml


valid_yaml_dir = (Path(__file__).parent / Path("yamls") / Path("valid"))
valid_yamls = [
        (valid_yaml_dir / Path("dream_file.yaml"))
    ]


@pytest.mark.parametrize("yaml_path", valid_yamls)
def test_validate_schema(yaml_path):
    with yaml_path.open() as yaml_fh:
        validate_schema(yaml.safe_load(yaml_fh))
