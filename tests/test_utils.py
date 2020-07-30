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
import shutil
import tempfile
from pathlib import Path

import pytest

from pytest_workflow.util import file_md5sum, is_in_dir, link_tree, \
    replace_whitespace

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


def test_link_tree():
    pipelines_dir = Path(__file__).parent / "pipelines"
    tempdir = Path(tempfile.mkdtemp(), "test")
    link_tree(pipelines_dir, tempdir)
    snakemake = Path(tempdir, "snakemake")
    snakemake_SimpleSnakeFile = Path(snakemake, "SimpleSnakefile")
    wdl = Path(tempdir, "wdl")
    wdl_simplejson = Path(wdl, "simple.json")
    wdl_simpleoptionsjson = Path(wdl, "simple.options.json")
    wdl_simplewdl = Path(wdl, "simple.wdl")
    assert snakemake.is_dir()
    assert snakemake_SimpleSnakeFile.is_symlink()
    assert (snakemake_SimpleSnakeFile.resolve() ==
            Path(pipelines_dir, "snakemake", "SimpleSnakefile"))
    assert wdl.is_dir()
    assert wdl_simplejson.is_symlink()
    assert (wdl_simplejson.resolve() ==
            Path(pipelines_dir, "wdl", "simple.json"))
    assert wdl_simpleoptionsjson.is_symlink()
    assert (wdl_simpleoptionsjson.resolve() ==
            Path(pipelines_dir, "wdl", "simple.options.json"))
    assert wdl_simplewdl.is_symlink()
    assert wdl_simplewdl.resolve() == Path(pipelines_dir, "wdl", "simple.wdl")
    shutil.rmtree(str(tempdir))


def test_link_tree_warning():
    urandom = Path("/dev/urandom")
    dest = Path("notexist")
    with pytest.warns(UserWarning,
                      match="Unsupported filetype. Skipping copying: "
                            "'/dev/urandom' to 'notexist'."):
        link_tree(urandom, dest)
    # Destination should not be created
    assert not dest.exists()


HASH_FILE_DIR = Path(__file__).parent / "hash_files"


@pytest.mark.parametrize("hash_file", HASH_FILE_DIR.iterdir())
def test_file_md5sum(hash_file: Path):
    # No sec added because this hash is only used for checking file integrity
    whole_file_md5 = hashlib.md5(hash_file.read_bytes()).hexdigest()  # nosec
    per_line_md5 = file_md5sum(hash_file)
    assert whole_file_md5 == per_line_md5
