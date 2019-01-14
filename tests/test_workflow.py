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

"""Tests the Workflow class"""

import pytest

from pytest_workflow.workflow import Workflow


def test_stdout():
    workflow = Workflow("echo moo")
    workflow.run()
    assert workflow.stdout == b"moo\n"


def test_exit_code():
    workflow = Workflow("echo moo")
    workflow.run()
    assert workflow.exit_code == 0
    workflow2 = Workflow("grep")
    workflow2.run()
    assert workflow2.exit_code == 2


def test_stderr():
    # This will fail and print a shortened grep usage.
    workflow = Workflow("grep")
    workflow.run()
    assert "grep" in workflow.stderr.decode()


def test_wait_timeout():
    workflow = Workflow("echo moo")
    workflow.wait_timeout_secs = 0.1
    workflow.wait_interval_secs = 0.01
    with pytest.raises(ValueError) as error:
        workflow.wait()
    assert workflow.wait_counter == int(0.1/0.01) + 1
    assert error.match(
        "Waiting on a workflow that has not started within the last 0.1 "
        "seconds"
    )


def test_start_lock():
    workflow = Workflow("echo moo")
    workflow.start()
    with pytest.raises(ValueError) as error:
        workflow.start()
    assert error.match("Workflows can only be started once")
