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

"""Tests whether the temporary directories are correctly saved/destroyed"""

import re
import shutil
import tempfile
import textwrap
from pathlib import Path

from .test_success_messages import SIMPLE_ECHO


def test_directory_kept(testdir):
    testdir.makefile(".yml", test=SIMPLE_ECHO)
    result = testdir.runpytest("-v", "--keep-workflow-wd")
    working_dir = re.search(r"command:   echo moo\n\tdirectory: ([\w/_-]*)",
                            result.stdout.str()).group(1)
    assert Path(working_dir).exists()
    assert Path(working_dir, "log.out").exists()
    assert Path(working_dir, "log.err").exists()
    shutil.rmtree(str(testdir))


def test_directory_not_kept(testdir):
    testdir.makefile(".yml", test=SIMPLE_ECHO)
    result = testdir.runpytest("-v")
    working_dir = re.search(r"command:   echo moo\n\tdirectory: ([\w/_-]*)",
                            result.stdout.str()).group(1)
    assert not Path(working_dir).exists()
    assert ("Removing temporary directories and logs. Use '--kwd' or "
            "'--keep-workflow-wd' to disable this behaviour."
            ) in result.stdout.str()


def test_basetemp_correct(testdir):
    testdir.makefile(".yml", test=SIMPLE_ECHO)
    tempdir = tempfile.mkdtemp()
    result = testdir.runpytest("-v", "--basetemp", tempdir)
    message = (f"\tcommand:   echo moo\n"
               f"\tdirectory: {tempdir}\n"
               f"\tstdout:    {tempdir}/simple_echo/log.out\n"
               f"\tstderr:    {tempdir}/simple_echo/log.err")
    assert message in result.stdout.str()

def test_basetemp_can_be_used_twice(testdir):
    testdir.makefile(".yml", test=SIMPLE_ECHO)
    tempdir = tempfile.mkdtemp()
    # First run to fill up tempdir
    testdir.runpytest("-v", "--keep-workflow-wd", "--basetemp", tempdir)
    # Make sure directory is there.
    assert Path(tempdir, "simple_echo").exists()
    # Run again with same basetemp.
    result = testdir.runpytest("-v", "--keep-workflow-wd", "--basetemp",
                               tempdir)
    exit_code = result.ret
    assert (f"'{tempdir}/simple_echo' already exists. Deleting ..." in
            result.stdout.str())
    assert exit_code == 0
    shutil.rmtree(tempdir)


def test_basetemp_will_be_created(testdir):
    testdir.makefile(".yml", test=SIMPLE_ECHO)
    # This creates an empty dir
    tempdir_base = tempfile.mkdtemp()
    # This path should not exist
    tempdir = Path(tempdir_base, "non", "existing")
    # If pytest-workflow does not handle non-existing nested directories well
    # it should crash.
    result = testdir.runpytest("-v", "--keep-workflow-wd", "--basetemp",
                               str(tempdir))
    assert tempdir.exists()
    assert result.ret == 0
    shutil.rmtree(tempdir_base)


def test_basetemp_can_not_be_in_rootdir(testdir):
    testdir.makefile(".yml", test=SIMPLE_ECHO)
    testdir_path = Path(str(testdir.tmpdir))
    tempdir = testdir_path / "tmp"
    result = testdir.runpytest("-v", "--basetemp", str(tempdir))
    message = f"'{str(tempdir)}' is a subdirectory of '{str(testdir_path)}'"
    assert message in result.stderr.str()


SUCCESS_TEST = """\
- name: success
  command: bash -c 'exit 0'
"""

FAIL_TEST = """\
- name: fail
  command: bash -c 'exit 1'
"""


def test_directory_kept_on_fail(testdir):
    testdir.makefile(".yml", test=FAIL_TEST)
    result = testdir.runpytest("-v", "--keep-workflow-wd-on-fail")
    working_dir = re.search(
        r"command:   bash -c 'exit 1'\n\tdirectory: ([\w/_-]*)",
        result.stdout.str()).group(1)
    assert Path(working_dir).exists()
    assert Path(working_dir, "log.out").exists()
    assert Path(working_dir, "log.err").exists()
    assert ("One or more tests failed. Keeping temporary directories and "
            "logs." in result.stdout.str())
    shutil.rmtree(working_dir)


def test_directory_not_kept_on_succes(testdir):
    testdir.makefile(".yml", test=SUCCESS_TEST)
    result = testdir.runpytest("-v", "--kwdof")
    working_dir = re.search(
        r"command:   bash -c 'exit 0'\n\tdirectory: ([\w/_-]*)",
        result.stdout.str()).group(1)
    assert not Path(working_dir).exists()
    assert ("All tests succeeded. Removing temporary directories and logs." in
            result.stdout.str())


def test_directory_of_symlinks(testdir):
    testdir.makefile(".yml", test=SIMPLE_ECHO)
    subdir = testdir.mkdir("subdir")
    Path(str(subdir), "subfile.txt").write_text("test")
    result = testdir.runpytest("-v", "--symlink", "--kwd")
    working_dir = re.search(
        r"command:   echo moo\n\tdirectory: ([\w/_-]*)",
        result.stdout.str()).group(1)
    assert Path(working_dir, "test.yml").is_symlink()
    assert Path(working_dir, "subdir").is_dir()
    assert Path(working_dir, "subdir", "subfile.txt").is_symlink()
    shutil.rmtree(working_dir)


def test_directory_unremovable_message(testdir):
    # Following directory contains nested contents owned by root.
    test = textwrap.dedent("""
    - name: Create unremovable dir
      command: >-
        bash -c "docker run -v $(pwd):$(pwd) -w $(pwd) debian \
        bash -c 'mkdir test && touch test/test'"
    """)
    testdir.makefile(".yaml", test=test)
    result = testdir.runpytest()
    assert ("Unable to remove the following directories due to permission "
            "errors" in result.stdout.str())
    assert result.ret == 0
