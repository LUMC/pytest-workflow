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

"""This contains all the classes and methods for content testing of files
and logs."""

from pathlib import Path
from typing import Dict, Iterator, List


def check_content(strings: List[str], text: Iterator[str]) -> Dict[str, bool]:
    # Make a copy of the list here to prevent aliasing.
    not_found_strings = list(strings)
    # By default all strings are not found.
    found_dictionary = {key: False for key in not_found_strings}

    for line in text:
        for string in not_found_strings:
            if string in line:
                found_dictionary[string] = True
                not_found_strings.remove(string)
        # Break the loop if the list of not found strings is empty.
        if not not_found_strings:
            break
    return found_dictionary


def file_to_string_iterator(filepath: Path) -> Iterator[str]:
    with filepath.open("r") as f:  # Use 'r' here explicitly as opposed to 'rb'
        yield f.readline()
