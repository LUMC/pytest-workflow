"""This file was created by A.H.B. Bollen as a proof of concept."""
from pathlib import Path
from typing import List
import subprocess


class Workflow(object):

    def __init__(self, executable: Path, arguments: List[str], cwd):
        self.executable = executable  # you could do a pre-test to make sure the executable even exists
        self.arguments = arguments

        self._proc_out = None
        self.cwd = cwd

    def run(self):
        sub_procces_args = [str(self.executable)] + self.arguments
        self._proc_out = subprocess.run(sub_procces_args, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, cwd=self.cwd)

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
        # TODO: Implement something?
        pass


def test_exit_code(hello_world_pipeline):
    assert hello_world_pipeline.exit_code == 0


def test_outputs_exist(hello_world_pipeline):
    for output in hello_world_pipeline.outputs:
        assert output.exists()
