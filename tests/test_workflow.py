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
