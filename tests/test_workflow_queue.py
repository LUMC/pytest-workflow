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

import pytest

from pytest_workflow.workflow import Workflow, WorkflowQueue


def test_workflow_queue_put():
    workflow = Workflow("echo moo")
    workflow_queue = WorkflowQueue()
    workflow_queue.put(workflow)
    assert workflow_queue.qsize() == 1

def test_workflow_queue_put_faulty():
    workflow = 1231
    workflow_queue = WorkflowQueue()
    with pytest.raises(ValueError) as error:
        workflow_queue.put(workflow)
    error.match("Only Workflow type objects can be submitted to this queue")
