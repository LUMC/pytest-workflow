"""All tests for workflow files"""

from typing import List
from pathlib import Path
import pytest
class WorkflowFilesTestCollector(pytest.Collector):
    def __init__(self, files: List[dict]):
        self.files = files

class FilesExistCollector(pytest.Collector):
    def __init__(self, files: List[Path]):
        self.files = files

    def collect(self):
        for file in self.files:
            yield FileExists(file)

class FileExists(pytest.Item):
    def __init__(self, name, parent, files: List[dict]):
