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

"""This tests the marker functionality that was added"""

import textwrap

from .test_success_messages import SIMPLE_ECHO

TEST_HOOK = textwrap.dedent("""\
import pytest

@pytest.mark.workflow(name="simple echo")
def test_hook_impl():
    assert True
""")

TEST_FIXTURE = textwrap.dedent("""\
import pytest

@pytest.mark.workflow(name="simple echo")
def test_fixture_impl(workflow_dir):
    assert workflow_dir.name == "simple_echo"
""")


def test_not_skipped(testdir):
    testdir.makefile(".yml", test_simple=SIMPLE_ECHO)
    testdir.makefile(".py", test_hook=TEST_HOOK)
    result = testdir.runpytest()
    result.assert_outcomes(passed=5)


def test_skipped(testdir):
    testdir.makefile(".yml", test_simple=SIMPLE_ECHO)
    testdir.makefile(".py", test_hook=TEST_HOOK)
    # No workflow will run because the tag does not match
    # ``-r s`` gives the reason why a test was skipped.
    result = testdir.runpytest("-v", "-r", "s", "--tag", "flaksdlkad")
    result.assert_outcomes(skipped=1)
    assert "'simple echo' has not run." in result.stdout.str()


def test_workflow_dir_arg(testdir):
    testdir.makefile(".yml", test_simple=SIMPLE_ECHO)
    testdir.makefile(".py", test_fixture=TEST_FIXTURE)
    result = testdir.runpytest()
    assert result.assert_outcomes(passed=5, failed=0, error=0, skipped=0)
