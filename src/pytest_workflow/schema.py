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

"""Schema for the YAML files used by pytest-workflow"""

import json
from pathlib import Path
from typing import NamedTuple, NewType, List, Type, Optional

import jsonschema

SCHEMA = Path(__file__).parent / Path("schema") / Path("schema.json")
DEFAULT_EXIT_CODE = 0
DEFAULT_FILES = []
with SCHEMA.open() as schema:
    JSON_SCHEMA = json.load(schema)


def validate_schema(instance):
    """
    Validates the pytest-workflow schema
    :param instance: an object that is validated against the schema
    :return: This function rasises a ValidationError
    when the schema is not correct.
    """
    jsonschema.validate(instance, JSON_SCHEMA)


####### Schema classes below
####### These should be dataclasses. But that's not supported in python<3.7
class ContentCheck(NamedTuple):
    def __init__(self, contains: List[str] = [],
                 must_not_contain: List[str] = []):
        pass


class FileTest(ContentCheck):
    def __init__(self, path: str, md5sum: Optional[str] = None,
                 contains: List[str] = [], must_not_contain: List[str] = []):
        super.__init__(contains=contains, must_not_contain=must_not_contain)
        pass


class WorkflowTest(NamedTuple):
    def __init__(self, name: str, command: str, exit_code: int = 0,
                 stdout: Type[ContentCheck] = ContentCheck(),
                 stderr: Type[ContentCheck] = ContentCheck(),
                 files: List[Type[FileTest]] = []):
        pass
