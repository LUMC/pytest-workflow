from pytest_workflow.workflow import Workflow

def test_stdout():
    workflow = Workflow("echo",["moo"])
    workflow.run()
    assert workflow.stdout == "moo"

def test_exit_code():
    workflow = Workflow("echo",["moo"])
    workflow.run()
    assert workflow.exit_code == 0
    workflow2 = Workflow("grep", [])
    workflow2.run()
    assert workflow2.exit_code == 2