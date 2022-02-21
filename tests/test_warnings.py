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

import shutil
import tempfile

from .test_success_messages import MOO_FILE


# Add a test to make sure no deprecation, or other warnings occur due to
# changes in upstream libraries.
def test_no_warnings(pytester):
    basetemp = tempfile.mkdtemp()
    pytester.makefile(".yml", test_a=MOO_FILE)
    result = pytester.runpytest("--basetemp", basetemp)
    outcomes = result.parseoutcomes()
    assert outcomes.get('warnings', 0) == 0
    shutil.rmtree(basetemp)


def test_git_warning(pytester):
    basetemp = tempfile.mkdtemp()
    pytester.mkdir(".git")
    pytester.makefile(".yml", test_a=MOO_FILE)
    result = pytester.runpytest("--basetemp", basetemp)
    outcomes = result.parseoutcomes()
    assert outcomes.get('warnings') == 1
    assert ".git dir detected" in result.stdout.str()
