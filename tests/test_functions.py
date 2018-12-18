import hashlib
import os
from pathlib import Path

import pytest

from pytest_workflow.workflow_file_tests import file_md5sum

hash_file_dir = Path(Path(__file__).parent / Path("hash_files"))

hash_files_relative = os.listdir(hash_file_dir.absolute().__str__())

hash_files = [Path(hash_file_dir / Path(x)) for x in hash_files_relative]


@pytest.mark.parametrize("hash_file", hash_files)
def test_file_md5sum(hash_file: Path):
    whole_file_md5 = hashlib.md5(hash_file.read_bytes()).hexdigest()
    per_line_md5 = file_md5sum(hash_file)
    assert whole_file_md5 == per_line_md5
