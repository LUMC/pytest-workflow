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
import gzip
import hashlib
import itertools
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from pytest_workflow.util import decode_unaligned, duplicate_tree, \
    extract_md5sum, file_md5sum, git_check_submodules_cloned, git_root, \
    is_in_dir, link_tree, replace_whitespace

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
    src_dir = Path(tempfile.mkdtemp())
    dest_dir = Path(tempfile.mkdtemp(), "test")

    not_a_file = src_dir / "not_a_file"
    os.mkfifo(not_a_file)
    with pytest.warns(UserWarning,
                      match=f"Unsupported filetype for copying. Skipping"
                            f" {not_a_file}"):
        link_tree(src_dir, dest_dir)
    # Destination should not be created
    assert not (dest_dir / "not_a_file").exists()
    shutil.rmtree(src_dir)
    shutil.rmtree(dest_dir.parent)


@pytest.fixture()
def git_dir():
    git_dir = Path(tempfile.mkdtemp())
    (git_dir / "test").mkdir()
    test_file = git_dir / "test" / "test.txt"
    test_file.touch()
    subprocess.run(["git", "-C", str(git_dir), "init"])
    subprocess.run(["git", "-C", str(git_dir), "add", str(test_file)])
    subprocess.run(["git", "-C", str(git_dir), "commit", "-m",
                    "initial commit"])
    yield git_dir
    shutil.rmtree(git_dir)


def test_duplicate_git_tree(git_dir):
    assert (git_dir / ".git").exists()
    dest = Path(tempfile.mkdtemp()) / "test"
    duplicate_tree(git_dir, dest, git_aware=True)
    assert dest.exists()
    assert not (dest / ".git").exists()
    assert (dest / "test" / "test.txt").exists()


def test_duplicate_git_tree_file_removed_error(git_dir):
    assert (git_dir / ".git").exists()
    os.remove(git_dir / "test" / "test.txt")
    dest = Path(tempfile.mkdtemp()) / "test"
    with pytest.raises(FileNotFoundError) as e:
        duplicate_tree(git_dir, dest, git_aware=True)
    e.match("checked in")
    e.match(f"\"git -C '{git_dir}' rm '{str(Path('test', 'test.txt'))}'\"")


def test_duplicate(git_dir):
    assert (git_dir / ".git").exists()
    dest = Path(tempfile.mkdtemp()) / "test"
    duplicate_tree(git_dir, dest, git_aware=False)
    assert dest.exists()
    assert (dest / ".git").exists()
    assert (dest / "test" / "test.txt").exists()


def test_duplicate_notadirerror():
    fd, file = tempfile.mkstemp()
    dir = tempfile.mkdtemp()
    with pytest.raises(NotADirectoryError):
        duplicate_tree(file, Path(dir, "somedir"), symlink=True)
    shutil.rmtree(dir)
    os.close(fd)
    os.remove(file)


def test_git_root(git_dir):
    assert git_root(git_dir / "test") == str(git_dir)


HASH_FILE_DIR = Path(__file__).parent / "hash_files"


@pytest.mark.parametrize("hash_file", HASH_FILE_DIR.iterdir())
def test_file_md5sum(hash_file: Path):
    whole_file_md5 = hashlib.md5(hash_file.read_bytes()).hexdigest()
    per_line_md5 = file_md5sum(hash_file)
    assert whole_file_md5 == per_line_md5


def test_extract_md5sum():
    hash_file = HASH_FILE_DIR / "LICENSE.gz"
    with gzip.open(hash_file, "rb") as contents_fh:
        whole_file_md5 = hashlib.md5(contents_fh.read()).hexdigest()
    per_line_md5 = extract_md5sum(hash_file)
    assert whole_file_md5 == per_line_md5


def create_git_repo(path):
    dir = Path(path)
    os.mkdir(dir)
    file = dir / "README.md"
    file.write_text("# My new project\n\nHello this project is awesome!\n")
    subdir = dir / "sub"
    subdir.mkdir()
    another_file = subdir / "subtext.md"
    another_file.write_text("# Subtext\n\nSome other example text.\n")
    subdir_link = dir / "gosub"
    subdir_link.symlink_to(subdir.relative_to(dir), target_is_directory=True)
    subprocess.run(["git", "init", "-b", "main"], cwd=dir)
    subprocess.run(["git", "config", "user.name", "A U Thor"], cwd=dir)
    subprocess.run(["git", "config", "user.email", "author@example.com"],
                   cwd=dir)
    subprocess.run(["git", "add", "."], cwd=dir)
    subprocess.run(["git", "commit", "-m", "initial commit"], cwd=dir)


@pytest.fixture()
def git_repo_with_submodules():
    repo_dir = Path(tempfile.mkdtemp())
    bird_repo = repo_dir / "bird"
    nest_repo = repo_dir / "nest"
    create_git_repo(bird_repo)
    create_git_repo(nest_repo)
    # https://bugs.launchpad.net/ubuntu/+source/git/+bug/1993586
    subprocess.run(["git", "-c", "protocol.file.allow=always",
                    "submodule", "add", bird_repo.absolute()],
                   cwd=nest_repo.absolute())
    subprocess.run(["git", "commit", "-m", "add bird repo as a submodule"],
                   cwd=nest_repo.absolute())
    yield nest_repo
    shutil.rmtree(repo_dir)


def test_git_submodule_check(git_repo_with_submodules, tmp_path):
    cloned_repo = tmp_path / "cloned"
    subprocess.run(
        # No recursive clone
        ["git", "-c", "protocol.file.allow=always",
         "clone", git_repo_with_submodules.absolute(), cloned_repo.absolute()],
        cwd=tmp_path
    )
    with pytest.raises(RuntimeError) as error:
        git_check_submodules_cloned(cloned_repo)
    # Error message should allow user to resolve the issue.
    error.match("'git submodule update --init --recursive'")
    subprocess.run(["git", "-c", "protocol.file.allow=always", "submodule",
                    "update", "--init", "--recursive"],
                   cwd=cloned_repo.absolute())
    # Check error does not occur when issue resolved.
    git_check_submodules_cloned(cloned_repo)


# https://github.com/LUMC/pytest-workflow/issues/162
def test_duplicate_git_tree_submodule_symlinks(git_repo_with_submodules):
    assert (git_repo_with_submodules / ".git").exists()
    dest = Path(tempfile.mkdtemp()) / "test"
    duplicate_tree(git_repo_with_submodules, dest, git_aware=True)
    assert dest.exists()
    assert not (dest / ".git").exists()
    link = dest / "bird" / "gosub"
    assert link.exists()
    assert link.is_symlink()
    assert link.resolve() == dest / "bird" / "sub"


@pytest.mark.parametrize(["offset", "encoding"],
                         list(itertools.product(
                             range(4), (None, "utf-8", "utf-16", "utf-32"))
                         ))
def test_decode_unaligned(offset, encoding):
    string = "èèèèèèèèèèè"
    data = string.encode(encoding or sys.getdefaultencoding())
    decoded = decode_unaligned(data[offset:], encoding)
    assert string.endswith(decoded)


def test_decode_unaligned_wrong_encoding_throws_error():
    data = "hello".encode("utf-8")
    with pytest.raises(UnicodeDecodeError):
        decode_unaligned(data, "utf-32-le")
