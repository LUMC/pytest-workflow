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

# Test errors in pytest-workflow that occur in one of the workflow threads

import textwrap


def test_shlex_error(pytester):
    test = textwrap.dedent("""\
    - name: wrong command
      command: a command with a dangling double-quote"
    """)
    pytester.makefile(".yml", test=test)
    result = pytester.runpytest("-v")
    assert "shlex" in result.stdout.str()
    assert "ValueError: No closing quotation" in result.stdout.str()
    assert "'wrong command' python error during start" in result.stdout.str()
