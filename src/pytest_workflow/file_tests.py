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

from pathlib import Path

import pytest

from .content_tests import ContentTestCollector
from .schema import FileTest
from .util import file_md5sum
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

        tests += [FileExists.from_parent(
            parent=self,
            filepath=filepath,
            should_exist=self.filetest.should_exist,
            workflow=self.workflow)]

        if any((self.filetest.contains, self.filetest.must_not_contain,
                self.filetest.contains_regex,
                self.filetest.must_not_contain_regex)):
            tests += [ContentTestCollector.from_parent(
                name="content",
                parent=self,
                filepath=filepath,
                content_test=self.filetest,
                # FileTest inherits from ContentTest. So this is valid.
                workflow=self.workflow)]

        if self.filetest.md5sum:
            tests += [FileMd5.from_parent(
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
        if not self.workflow.matching_exitcode():
            pytest.skip(f"'{self.parent.workflow.name}' did not exit with"
                        f"desired exit code.")
        assert self.file.exists() == self.should_exist

    def repr_failure(self, excinfo, style=None):
        exist = "not exist" if self.should_exist else "exist"
        should = "should" if self.should_exist else "should not"
        # self.file gives the actual path that was tested (including /tmp
        # bits). self.parent.filetest.path gives the path that the user
        # gave in the test yaml. self.file is probably more useful when
        # debugging.
        return f"'{str(self.file)}' does {exist} while it {should}"


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
        if not self.workflow.matching_exitcode():
            pytest.skip(f"'{self.parent.workflow.name}' did not exit with"
                        f"desired exit code.")
        self.observed_md5sum = file_md5sum(self.filepath)
        assert self.observed_md5sum == self.expected_md5sum

    def repr_failure(self, excinfo, style=None):
        return (
            f"Observed md5sum '{self.observed_md5sum}' not equal to expected "
            f"md5sum '{self.expected_md5sum}' for file '{self.filepath}'"
        )
