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

"""Check how different encodings are handled by pytest-workflow"""

import textwrap
TEST_TEXT = """In het Nederlands komen verscheidene diakritische tekens voor.
Een veel gebruikte is het trema ofwel de dubbele puntjes die boven een letter
geplaatst worden vaak wanneer een meervoud een onduidelijke klank zou hebben
zonder de verduidelijking van het trema. Zoals bijvoorbeeld: zee -> zeeën,
bacterie -> bacteriën.
Daarnaast worden veel diakritische tekens gebruikt in leenworden. Denk hierbij
aan woorden als: überhaupt, crème fraîche en Curaçao."""


def test_encoding(pytester):
    pytester.makefile(".yml", textwrap.dedent("""
    - name: test_encoding
      command: "bash -c 'true'"
      files:
        - path: diakritische_tekens.txt
          encoding: UTF32
          contains:
            - überhaupt
            - crème fraîche
    """))
    test_txt = pytester.path / "diakritische_tekens.txt"
    # UTF32 is not the default on windows and linux I believe
    test_txt.write_text(TEST_TEXT, encoding="UTF32")
    result = pytester.runpytest("-v")
    assert result.ret == 0
