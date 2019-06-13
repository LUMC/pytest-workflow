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

from .test_success_messages import SIMPLE_ECHO

import pytest


def test_same_name_different_files(testdir):
    testdir.makefile(".yml", test_a=SIMPLE_ECHO)
    testdir.makefile(".yml", test_b=SIMPLE_ECHO)
    result = testdir.runpytest()
    assert result.ret != 0
    assert ("workflow 'simple echo' is used more than once"
            in result.stdout.str())
    conflicting_message = ("Conflicting tests: " 
                          "{0}, {1}.".format(
        str(testdir.tmpdir) + "test_a.yml::" + "simple echo",
        str(testdir.tmpdir) + "test_b.yml::" + "simple echo",
    ))
    assert conflicting_message in result.stdout.str()