"""This file was created by A.H.B. Bollen as a proof of concept."""
import shlex
import subprocess
from typing import Union


class Workflow(object):

    def __init__(self, command: str,
                 cwd: Union[bytes, str] = None):
        """
        Initiates a workflow object
        :param command: The string that represents the command to be run
        :param cwd: The current working directory in which the command will
        be executed.
        """

        self.command = command
        self._proc_out = None
        self.cwd = cwd

    def run(self):
        arguments = shlex.split(self.command)
        sub_procces_args = arguments
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
