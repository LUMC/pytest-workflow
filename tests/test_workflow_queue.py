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

import time

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


def test_workflow_queue_process_empty():
    workflow_queue = WorkflowQueue()
    workflow_queue.process()


def generate_sleep_workflows(number: int, sleep_time: float):
    return [Workflow(f"sleep {sleep_time}") for _ in range(number)]


QUEUE_TESTS = [
    (2, 0.1, 1),
    (6, 0.1, 3)
]


@pytest.mark.parametrize(
    ["workflow_number", "sleep_time", "threads"], QUEUE_TESTS)
def test_workflow_queue(workflow_number: int, sleep_time: float, threads: int):
    workflows = generate_sleep_workflows(workflow_number, sleep_time)
    iterations = (
        workflow_number // threads if (workflow_number % threads == 0)
        else workflow_number // threads + 1)
    workflow_queue = WorkflowQueue()
    for workflow in workflows:
        workflow_queue.put(workflow)
    start_time = time.time()
    workflow_queue.process(threads)
    end_time = time.time()
    completion_time = end_time - start_time
    # If the completion time is shorter than (iterations * sleep_time), too
    # many threads are running.
    assert completion_time > iterations * sleep_time
    # If the completion time is longer than (iterations * sleep_time + 1) then
    # the code is probably not threaded properly.
    assert completion_time < (iterations + 1) * sleep_time
