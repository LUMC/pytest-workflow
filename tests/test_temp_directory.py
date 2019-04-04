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
import tempfile
from pathlib import Path

from .test_success_messages import SIMPLE_ECHO


def test_directory_kept(testdir):
    testdir.makefile(".yml", test=SIMPLE_ECHO)
    result = testdir.runpytest("-v", "--keep-workflow-wd")
    working_dir = re.search(r"with command 'echo moo' in '([\w/_-]*)'",
                            result.stdout.str()).group(1)
    assert Path(working_dir).exists()
    assert Path(working_dir / Path("log.out")).exists()
    assert Path(working_dir / Path("log.err")).exists()


def test_directory_not_kept(testdir):
    testdir.makefile(".yml", test=SIMPLE_ECHO)
    result = testdir.runpytest("-v")
    working_dir = re.search(r"with command 'echo moo' in '([\w/_-]*)'",
                            result.stdout.str()).group(1)
    assert not Path(working_dir).exists()
    assert ("Removing temporary directories and logs. Use '--kwd' or "
            "'--keep-workflow-wd' to disable this behaviour."
            ) in result.stdout.str()


def test_basetemp_correct(testdir):
    testdir.makefile(".yml", test=SIMPLE_ECHO)
    tempdir = tempfile.mkdtemp()
    result = testdir.runpytest("-v", "--basetemp", tempdir)
    message = ("start 'simple echo' with command 'echo moo' in "
               "'{tempdir}/simple_echo'. "
               "stdout: '{tempdir}/simple_echo/log.out'. "
               "stderr: '{tempdir}/simple_echo/log.err'."
               ).format(tempdir=str(tempdir))
    assert message in result.stdout.str()


def test_basetemp_can_be_used_twice(testdir):
    testdir.makefile(".yml", test=SIMPLE_ECHO)
    tempdir = tempfile.mkdtemp()
    # First run to fill up tempdir
    testdir.runpytest("-v", "--keep-workflow-wd", "--basetemp", tempdir)
    # Make sure directory is there.
    assert (Path(tempdir) / Path("simple_echo")).exists()
    # Run again with same basetemp.
    result = testdir.runpytest("-v", "--keep-workflow-wd", "--basetemp",
                               tempdir)
    exit_code = result.ret
    assert "'{0}/simple_echo' already exists. Deleting ...".format(
        tempdir) in result.stdout.str()
    assert exit_code == 0


def test_basetemp_will_be_created(testdir):
    testdir.makefile(".yml", test=SIMPLE_ECHO)
    # This creates an empty dir
    tempdir_base = tempfile.mkdtemp()
    # This path should not exist
    tempdir = Path(tempdir_base) / Path("non") / Path("existing")
    # If pytest-workflow does not handle non-existing nested directories well
    # it should crash.
    result = testdir.runpytest("-v", "--keep-workflow-wd", "--basetemp",
                               str(tempdir))
    assert tempdir.exists()
    assert result.ret == 0


def test_basetemp_can_not_be_in_rootdir(testdir):
    testdir.makefile(".yml", test=SIMPLE_ECHO)
    testdir_path = Path(str(testdir.tmpdir))
    tempdir = testdir_path / Path("tmp")
    result = testdir.runpytest("-v", "--basetemp", str(tempdir))
    message = "'{tempdir}' is a subdirectory of '{rootdir}'".format(
        tempdir=str(tempdir),
        rootdir=str(testdir_path))
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
        r"with command 'bash -c 'exit 1'' in '([\w/_-]*)'",
        result.stdout.str()).group(1)
    assert Path(working_dir).exists()
    assert Path(working_dir / Path("log.out")).exists()
    assert Path(working_dir / Path("log.err")).exists()
    assert ("One or more tests failed. Keeping temporary directories and "
            "logs." in result.stdout.str())


def test_directory_not_kept_on_succes(testdir):
    testdir.makefile(".yml", test=SUCCESS_TEST)
    result = testdir.runpytest("-v", "--kwdof")
    working_dir = re.search(
        r"with command 'bash -c 'exit 0'' in '([\w/_-]*)'",
        result.stdout.str()).group(1)
    assert not Path(working_dir).exists()
    assert ("All tests succeeded. Removing temporary directories and logs." in
            result.stdout.str())
