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

"""All tests for workflow files"""
import hashlib
from pathlib import Path

import pytest

from .content_tests import ContentTestCollector
from .schema import FileTest
from .workflow import Workflow


class FileTestCollector(pytest.Collector):
    """This collector returns all tests for one particular file"""

    def __init__(self, parent: pytest.Collector, filetest: FileTest,
                 workflow: Workflow):
        """
        Create a FiletestCollector
        :param parent: The collector that started this collector
        :param filetest: a FileTest object
        :param workflow: the workflow that is running to generate this file
        """
        name = str(filetest.path)
        super().__init__(name, parent)
        self.filetest = filetest
        self.cwd = workflow.cwd
        self.workflow = workflow

    def collect(self):
        """Returns all tests for one file. Also the absolute path of the files
        is determined in this function."""
        filepath = (
            self.filetest.path if self.filetest.path.is_absolute()
            else self.cwd / self.filetest.path)

        # Below structure was chosen since it allows for adding tests when
        # certain conditions are met.
        tests = []

        tests += [FileExists(parent=self,
                             filepath=filepath,
                             should_exist=self.filetest.should_exist,
                             workflow=self.workflow)]

        if self.filetest.contains or self.filetest.must_not_contain:
            tests += [ContentTestCollector(
                name="content",
                parent=self,
                filepath=filepath,
                content_test=self.filetest,
                # FileTest inherits from ContentTest. So this is valid.
                workflow=self.workflow)]

        if self.filetest.md5sum:
            tests += [FileMd5(
                parent=self,
                filepath=filepath,
                md5sum=self.filetest.md5sum,
                workflow=self.workflow)]

        return tests


class FileExists(pytest.Item):
    """A pytest file exists test."""

    def __init__(self, parent: pytest.Collector, filepath: Path,
                 should_exist: bool, workflow: Workflow):
        """
        :param parent: Collector that started this test
        :param filepath: A path to the file
        :param should_exist: Whether the file should exist
        :param workflow: The workflow running to generate the file
        """
        name = "should exist" if should_exist else "should not exist"
        super().__init__(name, parent)
        self.file = filepath
        self.should_exist = should_exist
        self.workflow = workflow

    def runtest(self):
        # Wait for the workflow process to finish before checking if the file
        # exists.
        self.workflow.wait()
        assert self.file.exists() == self.should_exist

    def repr_failure(self, excinfo):
        # pylint: disable=unused-argument
        # excinfo needed for pytest.
        message = "'{path}' does {exist} while it {should}".format(
            # self.file gives the actual path that was tested (including /tmp
            # bits). self.parent.filetest.path gives the path that the user
            # gave in the test yaml. self.file is probably more useful when
            # debugging.
            path=str(self.file),
            exist="not exist" if self.should_exist else "exist",
            should="should" if self.should_exist else "should not"
        )
        return message


class FileMd5(pytest.Item):
    def __init__(self, parent: pytest.Collector, filepath: Path,
                 md5sum: str, workflow: Workflow):
        """
        Create a tests for the file md5sum.
        :param parent: The collector that started this item
        :param filepath: The path to the file
        :param md5sum:  The expected md5sum
        :param workflow: The workflow running to generate the file
        """
        name = "md5sum"
        super().__init__(name, parent)
        self.filepath = filepath
        self.expected_md5sum = md5sum
        self.observed_md5sum = None
        self.workflow = workflow

    def runtest(self):
        # Wait for the workflow to finish before we check the md5sum of a file.
        self.workflow.wait()
        self.observed_md5sum = file_md5sum(self.filepath)
        assert self.observed_md5sum == self.expected_md5sum

    def repr_failure(self, excinfo):
        # pylint: disable=unused-argument
        # excinfo needed for pytest.
        message = (
            "Observed md5sum '{observed}' not equal to expected md5sum "
            "'{expected}' for file '{path}'"
        ).format(
            observed=self.observed_md5sum,
            expected=self.expected_md5sum,
            path=str(self.filepath)
        )
        return message


def file_md5sum(filepath: Path) -> str:
    """
    Generates a md5sum for a file. Reads file in blocks to save memory.
    :param filepath: a pathlib. Path to the file
    :return: a md5sum as hexadecimal string.
    """

    hasher = hashlib.md5()  # nosec: only used for file integrity
    with filepath.open('rb') as file_handler:  # Read the file in bytes
        # Hardcode the blocksize at 8192 bytes here.
        # This can be changed or made variable when the requirements compel us
        # to do so.
        for block in iter(lambda: file_handler.read(8192), b''):
            hasher.update(block)
    return hasher.hexdigest()
