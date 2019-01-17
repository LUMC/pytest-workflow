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

"""
Contains all functionality regarding the running of workflows and reporting
on stdout, stderr and exit code.
This file was created by A.H.B. Bollen. Multithreading functionality was added
later.
"""
import queue
import shlex
import subprocess  # nosec: security implications have been considered
import threading
import time
from pathlib import Path
from typing import List, Optional  # noqa: F401  # used for typing


class Workflow(object):
    # pylint: disable=too-many-instance-attributes
    # Is there a better way of doing things, as pylint suggests?
    def __init__(self,
                 command: str,
                 cwd: Path = Path(),
                 name: Optional[str] = None):
        """
        Initiates a workflow object
        :param command: The string that represents the command to be run
        :param cwd: The current working directory in which the command will
        be executed.
        :param name: An alias for the workflow. This looks nicer than a printed
        command.
        """
        self.command = command
        self.name = name
        self.cwd = cwd
        self._popen = None  # type: Optional[subprocess.Popen]
        self._stderr = None
        self._stdout = None
        self.start_lock = threading.Lock()
        self.wait_lock = threading.Lock()
        self.wait_timeout_secs = None
        self.wait_time_secs = 0.0
        self.wait_interval_secs = 0.01

    def start(self):
        """Runs the workflow in a subprocess in the background.
        To make sure the workflow is finished use the `.wait()` method"""
        # The lock ensures that the workflow is started only once, even if it
        # is started from multiple threads.
        with self.start_lock:
            if self._popen is None:
                sub_process_args = shlex.split(self.command)
                self._popen = subprocess.Popen(  # nosec: Shell is not enabled.
                    sub_process_args, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, cwd=str(self.cwd))
            else:
                raise ValueError("Workflows can only be started once")

    def run(self):
        """Runs the workflow and blocks until it is finished"""
        self.start()
        self.wait()

    def stdout_to_file(self) -> Path:
        self.wait()
        return bytes_to_file(self.stdout, self.cwd / Path("log.out"))

    def stderr_to_file(self) -> Path:
        self.wait()
        return bytes_to_file(self.stderr, self.cwd / Path("log.err"))

    def wait(self):
        """Waits for the workflow to complete"""
        # Lock the wait step. Only one waiter is allowed here to wait for
        # the workflow to complete and write the stderr.
        # A popen.stderr is a buffered reader and can only be read once.
        # Once self._stderr and self._stdout are written the lock can be
        # released
        with self.wait_lock:
            while self._popen is None:
                # This piece of code checks if a workflow has started yet. If
                # it has not, it waits. A counter is implemented here because:
                # 1. Incrementing a counter is much faster than checking system
                #    time
                # 2. The counter is linked to the self object. This means we
                #    wait only once for the workflow to start. All consecutive
                #    wait commands will fail instantly. Having all of these
                #    wait as well would be a waste of time.
                if (self.wait_timeout_secs is not None
                        and self.wait_time_secs > self.wait_timeout_secs):
                    raise ValueError(
                        "Waiting on a workflow that has not started within the"
                        " last {0} seconds".format(self.wait_timeout_secs))
                time.sleep(self.wait_interval_secs)
                self.wait_time_secs += self.wait_interval_secs

            # Wait for process to finish with _popen.communicate(). This blocks
            # until the command completes.
            # _popen.wait() will block with stdout=pipe and stderr=pipe
            if (self._popen.returncode is None and
                    self._stderr is None and
                    self._stdout is None):
                self._stdout, self._stderr = self._popen.communicate()

    @property
    def stdout(self) -> bytes:
        self.wait()
        return self._stdout  # for testing log

    @property
    def stderr(self) -> bytes:
        self.wait()
        return self._stderr  # for testing log

    @property
    def exit_code(self) -> int:
        self.wait()
        return self._popen.returncode

    def stdout_lines(self) -> List[str]:
        self.wait()
        return self._stdout.decode().splitlines()

    def stderr_lines(self) -> List[str]:
        self.wait()
        return self._stderr.decode().splitlines()


def bytes_to_file(bytestring: bytes, output_file: Path) -> Path:
    with output_file.open('wb') as file_handler:
        file_handler.write(bytestring)
    return output_file


class WorkflowQueue(queue.Queue):
    """A Queue object that will keep running 'n' numbers of workflows
    simultaneously until the queue is empty."""

    def __init__(self):
        # No argument for maxsize. This queue is infinite.
        super().__init__()

    def put(self, item, block=True, timeout=None):
        """Like Queue.put() but tests if item is a Workflow"""
        if isinstance(item, Workflow):
            super().put(item, block, timeout)
        else:
            raise ValueError("Only Workflow type objects can be submitted to "
                             "this queue.")

    # Queue processing with workers example taken from
    # https://docs.python.org/3.5/library/queue.html?highlight=queue#queue.Queue.join  # noqa
    def process(self, number_of_threads: int = 1, save_logs: bool = False):
        """
        Processes the workflow queue with a number of threads
        :param number_of_threads: The number of threads
        :param save_logs: Whether to save the logs of the workflows that have
        run
        """
        threads = []
        for _ in range(number_of_threads):
            thread = threading.Thread(target=self.worker, args=(save_logs,))
            thread.start()
            threads.append(thread)
        self.join()
        for thread in threads:
            thread.join()

    def worker(self, save_logs: bool = False):
        """
        Run workflows until the queue is empty
        :param save_logs: Whether to save the logs of the workflows that have
        run
        """
        while True:
            try:
                # We know the type is Workflow, because this was enforced in
                # the put method.
                workflow = self.get_nowait()  # type: Workflow
            except queue.Empty:
                break
            else:
                workflow.run()
                self.task_done()
                # Some reporting
                if workflow.name is not None:
                    print("'{0}' done.".format(workflow.name))
                else:
                    print("command: '{0}' done.".format(workflow.command))
                if save_logs:
                    log_err = workflow.stderr_to_file()
                    log_out = workflow.stdout_to_file()
                    print("'{0}' stdout saved in: {1}".format(
                        workflow.name or workflow.command, str(log_out)))
                    print("'{0}' stderr saved in: {1}".format(
                        workflow.name or workflow.command, str(log_err)))
