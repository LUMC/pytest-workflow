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

import hashlib
import os
from pathlib import Path

import pytest

from pytest_workflow.file_tests import file_md5sum

hash_file_dir = Path(Path(__file__).parent / Path("hash_files"))

hash_files_relative = os.listdir(hash_file_dir.absolute().__str__())

hash_files = [Path(hash_file_dir / Path(x)) for x in hash_files_relative]


@pytest.mark.parametrize("hash_file", hash_files)
def test_file_md5sum(hash_file: Path):
    whole_file_md5 = hashlib.md5(hash_file.read_bytes()).hexdigest()
    per_line_md5 = file_md5sum(hash_file)
    assert whole_file_md5 == per_line_md5
