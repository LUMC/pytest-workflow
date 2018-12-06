"""This file was created by A.H.B. Bollen as a proof of concept."""
from pathlib import Path
from typing import List, Optional
import subprocess

import pytest


class Pipeline(object):

    def __init__(self, executable: Path, arguments: List[str], outputs: Optional[List[Path]] = None):
        self.executable = executable  # you could do a pre-test to make sure the executable even exists
        self.arguments = arguments
        self.outputs = outputs

        self._proc_out = None

    def run(self):
        sub_procces_args = [str(self.executable)] + self.arguments
        self._proc_out = subprocess.run(sub_procces_args, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)

    @property
    def stdout(self):
        return self._proc_out.stdout  # for testing log

    @property
    def stderr(self):
        return self._proc_out.stderr  # for testing log

    @property
    def exit_code(self):
        return self._proc_out.returncode

    def cleanup(self):
        # e.g. cleanup output files
        raise NotImplementedError

    @classmethod
    def from_yaml(cls, yaml_path: Path):
        # make instance of this class from a yaml file
        raise NotImplementedError


@pytest.fixture(scope="module")  # scope=module so that it only executes once.
def hello_world_pipeline():
    pipeline = Pipeline(Path("/bin/echo"), ["hello_world!"], [Path("hello.txt")])
    pipeline.run()
    yield pipeline
    # everything after 'yield' in a pytest fixture
    #  is performed after test completion.
    pipeline.cleanup()


def test_exit_code(hello_world_pipeline):
    assert hello_world_pipeline.exit_code == 0


def test_outputs_exist(hello_world_pipeline):
    for output in hello_world_pipeline.outputs:
        assert output.exists()
