"""All tests for workflow files"""

from typing import List
from pathlib import Path
import pytest


class WorkflowFilesTestCollector(pytest.Collector):
    def __init__(self, name, parent, files: List[dict]):
        self.files = files
        self.name = name
        super(WorkflowFilesTestCollector, self).__init__(name, parent=parent)

    def collect(self):
        filepaths = [Path(x.get("path")) for x in self.files]
        # Structure why not the file exists directly?
        # Because also some other operations on files will be added to
        # this list.
        return [FilesExistCollector(self.name, self, filepaths)]


class FilesExistCollector(pytest.Collector):
    def __init__(self, name, parent, files: List[Path]):
        self.files = files
        self.name = name
        super(FilesExistCollector, self).__init__(name, parent=parent)

    def collect(self):
        for file in self.files:
            name = "{0}. File exists: {1}".format(self.name, file)
            yield FileExists(name, self, file)


class FileExists(pytest.Item):
    def __init__(self, name, parent, file: Path):
        super(FileExists, self).__init__(name, parent)
        self.file = file

    def runtest(self):
        assert self.file.exists()
