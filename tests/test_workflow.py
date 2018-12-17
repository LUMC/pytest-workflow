from pathlib import Path

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
    assert "grep" in str(workflow.stderr)
