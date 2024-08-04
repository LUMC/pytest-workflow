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
import subprocess

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


def test_wait_timeout_workflow_not_started():
    workflow = Workflow("echo moo")
    with pytest.raises(TimeoutError) as error:
        workflow.wait(timeout_secs=0.1, wait_interval_secs=0.01)
    assert error.match(
        "Waiting on a workflow that has not started within the last 0.1 "
        "seconds"
    )


def test_wait_timeout_workflow_started():
    workflow = Workflow("sleep 10")
    workflow.start()
    with pytest.raises(subprocess.TimeoutExpired) as error:
        workflow.wait(timeout_secs=0.1, wait_interval_secs=0.01)
    assert error.match("timed out after 0.1 seconds")


def test_start_lock():
    workflow = Workflow("echo moo")
    workflow.start()
    with pytest.raises(ValueError) as error:
        workflow.start()
    assert error.match("Workflows can only be started once")


def test_long_log():
    """If stdout is longer than 65536 bytes then it completely fills up the
    buffer on the linux kernel. If the buffer is not emptied, this will stall
    the process that is writing to stdout. This test produces an output that is
    bigger than 65536 bytes to make sure pytest-workflow handles these cases
    correctly."""
    workflow = Workflow(
        "bash -c 'for i in {1..262144}; do echo \"this is a long log\"; done'")
    workflow.run()
    assert len(workflow.stdout) > 65536


def test_empty_command():
    with pytest.raises(ValueError) as error:
        Workflow("")
    error.match("command can not be an empty string")


def test_workflow_name():
    workflow = Workflow("echo moo", name="moo")
    assert workflow.name == "moo"


def test_workflow_name_inferred():
    workflow = Workflow("echo moo")
    assert workflow.name == "echo"


def test_workflow_matching_exit_code():
    workflow = Workflow("echo moo")
    workflow.run()
    assert workflow.matching_exitcode()
    workflow2 = Workflow("grep", desired_exit_code=2)
    workflow2.run()
    assert workflow2.matching_exitcode()


def test_capture_unsupported():
    with pytest.raises(ValueError) as error:
        Workflow("echo moo", capture="tee-sys")
    error.match("only capture methods")


def test_capture_no():
    workflow = Workflow("echo moo", capture="no")
    workflow.run()
    with pytest.raises(ValueError) as error:
        workflow.stdout
    error.match("Stdout not available")
