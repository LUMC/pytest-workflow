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

import pytest

from .test_success_messages import SIMPLE_ECHO

TEST_HOOK_KWARGS = textwrap.dedent("""\
import pytest

@pytest.mark.workflow(name="simple echo")
def test_hook_impl():
    assert True
""")

TEST_HOOK_ARGS = textwrap.dedent("""\
import pytest

@pytest.mark.workflow("simple echo")
def test_hook_impl():
    assert True
""")


@pytest.mark.parametrize("test", [TEST_HOOK_ARGS])
def test_not_skipped(test, pytester):
    pytester.makefile(".yml", test_simple=SIMPLE_ECHO)
    pytester.makefile(".py", test_hook=test)
    result = pytester.runpytest()
    result.assert_outcomes(passed=5)


def test_name_use_is_deprecated(pytester):
    pytester.makefile(".py", test_hook=TEST_HOOK_KWARGS)
    pytester.makefile(".yml", test_simple=SIMPLE_ECHO)
    result = pytester.runpytest().stdout.str()
    assert "Use pytest.mark.workflow('workflow_name') instead." in result
    assert "DeprecationWarning" in result


@pytest.mark.parametrize("test", [TEST_HOOK_ARGS])
def test_skipped(test, pytester):
    pytester.makefile(".yml", test_simple=SIMPLE_ECHO)
    pytester.makefile(".py", test_hook=test)
    # No workflow will run because the tag does not match
    # ``-r s`` gives the reason why a test was skipped.
    result = pytester.runpytest("-v", "-r", "s", "--tag", "flaksdlkad")
    result.assert_outcomes(skipped=1)
    assert "'simple echo' has not run." in result.stdout.str()


TEST_FIXTURE_ARGS = textwrap.dedent("""\
import pytest

@pytest.mark.workflow("simple echo")
def test_fixture_impl(workflow_dir):
    assert workflow_dir.name == "simple_echo"
    assert workflow_dir.exists()
""")


@pytest.mark.parametrize("test", [TEST_FIXTURE_ARGS])
def test_workflow_dir_arg(test, pytester):
    # Call the test, `test_asimple` because tests are run alphabetically.
    # This will detect if the workflow dir has been removed.
    pytester.makefile(".yml", test_asimple=SIMPLE_ECHO)
    pytester.makefile(".py", test_fixture=test)
    result = pytester.runpytest()
    result.assert_outcomes(passed=5, failed=0, errors=0, skipped=0)


@pytest.mark.parametrize("test", [TEST_FIXTURE_ARGS])
def test_workflow_dir_arg_skipped(test, pytester):
    """Run this test to check if this does not run into fixture request
    errors"""
    pytester.makefile(".yml", test_asimple=SIMPLE_ECHO)
    pytester.makefile(".py", test_fixture=test)
    result = pytester.runpytest("-v", "-r", "s", "--tag", "flaksdlkad")
    result.assert_outcomes(skipped=1)


@pytest.mark.parametrize("test", [TEST_FIXTURE_ARGS])
def test_mark_not_unknown(test, pytester):
    pytester.makefile(".yml", test_asimple=SIMPLE_ECHO)
    pytester.makefile(".py", test_fixture=test)
    result = pytester.runpytest("-v")
    assert "PytestUnknownMarkWarning" not in result.stdout.str()


TEST_FIXTURE_WORKFLOW_NOT_EXIST = textwrap.dedent("""\
import pytest

@pytest.mark.workflow("shoobiedoewap")
def test_fixture_impl(workflow_dir):
    assert workflow_dir.name == "simple_echo"
""")


def test_workflow_not_exist_dir_arg(pytester):
    """Run this test to check if this does not run into fixture request
    errors"""
    pytester.makefile(".yml", test_asimple=SIMPLE_ECHO)
    pytester.makefile(".py", test_fixture=TEST_FIXTURE_WORKFLOW_NOT_EXIST)
    result = pytester.runpytest("-v", "-r", "s")
    result.assert_outcomes(skipped=1, passed=4)
    assert "'shoobiedoewap' has not run." in result.stdout.str()


TEST_FIXTURE_UNMARKED_TEST = textwrap.dedent("""\
import pytest

def test_fixture_impl(workflow_dir):
    assert workflow_dir.name == "simple_echo"
""")


def test_fixture_unmarked_test(pytester):
    """Run this test to check if this does not run into fixture request
    errors"""
    pytester.makefile(".yml", test_asimple=SIMPLE_ECHO)
    pytester.makefile(".py", test_fixture=TEST_FIXTURE_UNMARKED_TEST)
    result = pytester.runpytest("-v", "-r", "s")
    assert ("workflow_dir can only be requested in tests marked with "
            "the workflow mark.") in result.stdout.str()


TEST_MARK_WRONG_KEY = textwrap.dedent("""\
import pytest

@pytest.mark.workflow(naem="simple echo")
def test_fixture_impl(workflow_dir):
    assert workflow_dir.name == "simple_echo"
    assert workflow_dir.exists()
""")


def test_mark_wrong_key_with_fixture(pytester):
    """Run this test to check if this does not run into fixture request
    errors"""
    pytester.makefile(".yml", test_asimple=SIMPLE_ECHO)
    pytester.makefile(".py", test_fixture=TEST_MARK_WRONG_KEY)
    result = pytester.runpytest("-v", "-r", "s")
    assert ("A workflow name or names should be defined in the "
            "workflow marker of test_fixture.py::test_fixture_impl"
            ) in result.stdout.str()
    # Assert that no tests were run.
    result.assert_outcomes(passed=0, failed=0, skipped=0, errors=1)


def test_fixture_usable_for_file_tests(pytester):
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

    @pytest.mark.workflow("number files")
    def test_div_by_three(workflow_dir):
        number_file = workflow_dir / "123.txt"

        with number_file.open('rt') as file_h:
            number_file_content = file_h.read()

        assert int(number_file_content) % 3 == 0
    """)

    pytester.makefile(".yml", test_aworkflow=test_workflow)
    pytester.makefile(".py", test_div=test_div_by_three)
    result = pytester.runpytest("-v")
    result.assert_outcomes(passed=4, failed=0, skipped=0, errors=0)


def test_same_custom_test_multiple_times(pytester):
    test_workflow = textwrap.dedent("""\
    - name: one_two_three
      command: >-
        bash -c '
        echo 123 > numbers.txt' ;
      files:
        - path: numbers.txt
    - name: two_three_four
      command: >-
        bash -c '
        echo 234 > numbers.txt' ;
      files:
        - path: numbers.txt
    - name: three_four_five
      command: >-
        bash -c '
        echo 345 > numbers.txt' ;
      files:
        - path: numbers.txt""")
    test_div_by_three = textwrap.dedent("""\
    import pytest
    from pathlib import Path

    @pytest.mark.workflow("one_two_three", "two_three_four",
     "three_four_five")
    def test_div_by_three(workflow_dir):
        number_file = workflow_dir / "numbers.txt"
        assert int(number_file.read_text()) % 3 == 0
    """)

    pytester.makefile(".yml", test_aworkflow=test_workflow)
    pytester.makefile(".py", test_div=test_div_by_three)
    result = pytester.runpytest("-v")
    result.assert_outcomes(passed=9, failed=0, skipped=0, errors=0)


TEST_WORKFLOWS = textwrap.dedent("""\
- name: one_two_three
  command: >-
    bash -c '
    echo 123 > numbers.txt' ;
  files:
    - path: numbers.txt
- name: two_three_five
  command: >-
    bash -c '
    echo 235 > numbers.txt' ;
  files:
    - path: numbers.txt
- name: three_four_five
  command: >-
    bash -c '
    echo 345 > numbers.txt' ;
  files:
    - path: numbers.txt""")

TEST_DIV_BY_THREE = textwrap.dedent("""\
import pytest
from pathlib import Path

@pytest.mark.workflow("one_two_three", "two_three_five", "three_four_five")
def test_div_by_three(workflow_dir):
    number_file = workflow_dir / "numbers.txt"
    assert int(number_file.read_text()) % 3 == 0
""")


def test_same_custom_test_multiple_times_one_error(pytester):
    pytester.makefile(".yml", test_aworkflow=TEST_WORKFLOWS)
    pytester.makefile(".py", test_div=TEST_DIV_BY_THREE)
    result = pytester.runpytest("-v")
    result.assert_outcomes(passed=8, failed=1, skipped=0, errors=0)
    assert ("test_div.py::test_div_by_three[two_three_five] FAILED "
            in result.stdout.str())


def test_custom_tests_properly_skipped(pytester):
    pytester.makefile(".yml", test_aworkflow=TEST_WORKFLOWS)
    pytester.makefile(".py", test_div=TEST_DIV_BY_THREE)
    result = pytester.runpytest("-v", "--tag", "one_two_three")
    result.assert_outcomes(passed=3, failed=0, skipped=2, errors=0)
    assert ("test_div.py::test_div_by_three[two_three_five] SKIPPED "
            in result.stdout.str())
