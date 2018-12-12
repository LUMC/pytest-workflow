"""All tests for workflow files"""

from pathlib import Path
from typing import List, Union

import pytest


class WorkflowFilesTestCollector(pytest.Collector):
    """Collects all the files related tests"""

    def __init__(self, name: str, parent: pytest.Collector, files: List[dict],
                 cwd: Union[bytes, str]):
        """
        A WorkflowFilesTestCollector starts all the files-related tests
        :param name: The name of the tests
        :param parent: The collector that started this collector
        :param files: A list of `files` which are dictionaries in the schema
        the dictionaries define the tests.
        :param cwd: The directory relative to which relative file paths will
        be tested.
        """
        self.files = files
        self.cwd = cwd
        super().__init__(name, parent=parent)

    def collect(self):
        """Starts all file related tests"""
        filepaths = [Path(x["path"]) for x in self.files]
        # Structure why not the file exists directly?
        # Because also some other operations on files will be added to
        # this list. Like contains, md5sum etc.
        return [FilesExistCollector(self.name, self, filepaths, self.cwd)]


class FilesExistCollector(pytest.Collector):
    """Spawns tests to check for files existence"""

    def __init__(self, name: str, parent: pytest.Collector, files: List[Path],
                 cwd: Union[bytes, str]):
        """
        :param name: Name of the test.
        :param parent: Collector that started this test.
        :param files: A list of paths to be tested.
        :param cwd: The directory relative to which relative paths are tested.
        """
        self.files = files
        self.cwd = cwd
        super().__init__(name, parent=parent)

    def collect(self):
        """Starts all the file existence tests."""
        for test_file in self.files:
            name = "{0}. File exists: {1}".format(self.name, test_file)
            yield FileExists(name, self, Path(self.cwd) / test_file)


class FileExists(pytest.Item):
    """A pytest file exists test."""

    def __init__(self, name: str, parent: pytest.Collector, file: Path):
        """
        :param name: Test name
        :param parent: Collector that started this test
        :param file: A path to the file
        """
        super().__init__(name, parent)
        self.file = file

    def runtest(self):
        assert self.file.exists()
