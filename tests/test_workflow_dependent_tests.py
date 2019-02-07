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


TEST_FIXTURE = textwrap.dedent("""\
import pytest

@pytest.mark.workflow(name="simple echo")
def test_fixture_impl(workflow_dir):
    assert workflow_dir.name == "simple_echo"
    assert workflow_dir.exists()
""")


def test_workflow_dir_arg(testdir):
    # Call the test, `test_asimple` because tests are run alphabetically.
    # This will detect if the workflow dir has been removed.
    testdir.makefile(".yml", test_asimple=SIMPLE_ECHO)
    testdir.makefile(".py", test_fixture=TEST_FIXTURE)
    result = testdir.runpytest()
    result.assert_outcomes(passed=5, failed=0, error=0, skipped=0)


def test_worfklow_dir_arg_skipped(testdir):
    """Run this test to check if this does not run into fixture request
    errors"""
    testdir.makefile(".yml", test_asimple=SIMPLE_ECHO)
    testdir.makefile(".py", test_fixture=TEST_FIXTURE)
    result = testdir.runpytest("-v", "-r", "s", "--tag", "flaksdlkad")
    result.assert_outcomes(skipped=1)


TEST_FIXTURE_WORKFLOW_NOT_EXIST = textwrap.dedent("""\
import pytest

@pytest.mark.workflow(name="shoobiedoewap")
def test_fixture_impl(workflow_dir):
    assert workflow_dir.name == "simple_echo"
""")


def test_worfklow_not_exist_dir_arg(testdir):
    """Run this test to check if this does not run into fixture request
    errors"""
    testdir.makefile(".yml", test_asimple=SIMPLE_ECHO)
    testdir.makefile(".py", test_fixture=TEST_FIXTURE_WORKFLOW_NOT_EXIST)
    result = testdir.runpytest("-v", "-r", "s")
    result.assert_outcomes(skipped=1, passed=4)
    assert "'shoobiedoewap' has not run." in result.stdout.str()


TEST_FIXTURE_UNMARKED_TEST = textwrap.dedent("""\
import pytest

def test_fixture_impl(workflow_dir):
    assert workflow_dir.name == "simple_echo"
""")


def test_fixture_unmarked_test(testdir):
    """Run this test to check if this does not run into fixture request
    errors"""
    testdir.makefile(".yml", test_asimple=SIMPLE_ECHO)
    testdir.makefile(".py", test_fixture=TEST_FIXTURE_UNMARKED_TEST)
    result = testdir.runpytest("-v", "-r", "s")
    result.assert_outcomes(error=1, passed=4)
    assert ("workflow_dir can only be requested in tests marked with "
            "the workflow mark.") in result.stdout.str()


def test_fixture_usable_for_file_tests(testdir):
    test_workflow = textwrap.dedent("""\
    - name: number files
      command: >-
        bash -c '
        echo 123 > 123.txt ;
        echo 456 > 456.txt'
      files:
        - path: 123.txt
        - path: 456.txt
    """)
    test_div_by_three = textwrap.dedent("""\
    import pytest
    from pathlib import Path

    @pytest.mark.workflow(name="number files")
    def test_div_by_three(workflow_dir):
        number_file = workflow_dir / Path("123.txt")

        with number_file.open('rt') as file_h:
            number_file_content = file_h.read()

        assert int(number_file_content) % 3 == 0
    """)

    testdir.makefile(".yml", test_aworkflow=test_workflow)
    testdir.makefile(".py", test_div=test_div_by_three)
    result = testdir.runpytest("-v")
    result.assert_outcomes(passed=4, failed=0, skipped=0, error=0)
