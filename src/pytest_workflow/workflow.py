"""This file was created by A.H.B. Bollen as a proof of concept."""
import subprocess
from pathlib import Path
from typing import List


class Workflow(object):

    def __init__(self, executable: Path, arguments: List[str], cwd=None):
        """
        Initiates a workflow object
        :param executable: The executable, such as `snakemake` `/bin/make`
        or `cromwell`
        :param arguments: The arguments passed to the executable. Such as
        `-i inputs.json my_workflow.wdl`
        :param cwd: The current working directory in which the command will
        be executed.
        """

        self.executable = executable
        # TODO: a pre-test to make sure the executable even exists
        self.arguments = arguments

        self._proc_out = None
        self.cwd = cwd

    def run(self):
        sub_procces_args = [str(self.executable)] + self.arguments
        self._proc_out = subprocess.run(
            sub_procces_args, stdout=subprocess.PIPE,
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

    @classmethod
    def from_yaml_content(cls, yaml_contents: dict, cwd=None):
        # FIXME what is type of cwd?
        return cls(
            Path(yaml_contents['executable']),
            yaml_contents['arguments'],
            cwd=cwd
        )
