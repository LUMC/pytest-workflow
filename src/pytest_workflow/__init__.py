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

import re
import shutil
from pathlib import Path
from typing import List


# This function was created to ensure the same conversion is used throughout
# pytest-workflow.
def replace_whitespace(string: str, replace_with: str = '_') -> str:
    """
    Replaces all whitespace with the string in replace_with.
    :param string: input string
    :param replace_with: Replace whitespace with this string. Default: '_'
    :return: The string with whitespace converted.
    """
    return re.sub(r'\s+', replace_with, string)


def rm_dirs(directories: List[Path]):
    for directory in directories:
        shutil.rmtree(str(directory))
