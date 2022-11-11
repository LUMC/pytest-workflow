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

import textwrap

SKIP_TESTS = textwrap.dedent("""\
- name: wall_test
  command: echo "testing"
  files:
    - path: test.txt
      contains:
        - "brie"
    - path: test2.txt
      contains:
        - "halloumi"
      must_not_contain:
        - "gorgonzola"

- name: wall3_test
  command: bash -c "echo 'testing' > test3.txt"
  files:
    - path: test3.txt
      contains:
        - "kaas"
      must_not_contain:
        - "testing"    
""")

def test_skips(pytester):
    pytester.makefile(".yml", test=SKIP_TESTS)
    result = pytester.runpytest("-v").stdout.str()
    assert "4 failed, 3 passed, 3 skipped" in result