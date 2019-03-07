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
import tempfile
import threading
import time
from pathlib import Path
from typing import List, Optional


class Workflow(object):
    # If there is a better way to do this we can disable the pylint warning.
    # pylint: disable=too-many-instance-attributes

    def __init__(self,
                 command: str,
                 cwd: Optional[Path] = None,
                 name: Optional[str] = None):
        """
        Initiates a workflow object
        :param command: The string that represents the command to be run
        :param cwd: The current working directory in which the command will
        be executed. If None given will default to Path()
        :param name: An alias for the workflow. This looks nicer than a printed
        command.
        """
        if command == "":
            raise ValueError("command can not be an empty string")
        self.command = command
        # Always ensure a name. command.split()[0] can't fail because we tested
        # for emptiness.
        self.name = name or command.split()[0]
        self.cwd = cwd or Path()
        # For long running workflows it is best to save the stdout and stderr
        # to a file which can be checked with ``tail -f``.
        # stdout and stderr will be written to a tempfile if no CWD is given
        # to prevent clutter created when testing.
        self.stdout_file = (
            Path(tempfile.NamedTemporaryFile(prefix=self.name,
                                             suffix=".out").name)
            if cwd is None
            else self.cwd / Path("log.out"))
        self.stderr_file = (
            Path(tempfile.NamedTemporaryFile(prefix=self.name,
                                             suffix=".err").name)
            if cwd is None
            else self.cwd / Path("log.err"))
        self._popen = None  # type: Optional[subprocess.Popen]
        self._started = False
        self.errors = []  # type: List[Exception]
        self.start_lock = threading.Lock()

    def start(self):
        """Runs the workflow in a subprocess in the background.
        To make sure the workflow is finished use the `.wait()` method"""
        # The lock ensures that the workflow is started only once, even if it
        # is started from multiple threads.
        with self.start_lock:
            if not self._started:
                try:
                    stdout_h = self.stdout_file.open('wb')
                    stderr_h = self.stderr_file.open('wb')
                    sub_process_args = shlex.split(self.command)
                    self._popen = subprocess.Popen(  # nosec: Shell is not enabled. # noqa
                        sub_process_args, stdout=stdout_h,
                        stderr=stderr_h, cwd=str(self.cwd))
                except Exception as error:  # pylint: disable=broad-except
                    # Append the error so it can be raised in the main thread.
                    self.errors.append(error)
                finally:
                    self._started = True
                    stdout_h.close()
                    stderr_h.close()
            else:
                raise ValueError("Workflows can only be started once")

    def run(self):
        """Runs the workflow and blocks until it is finished"""
        self.start()
        self.wait()

    def wait(self, timeout_secs: Optional[float] = None,
             wait_interval_secs: float = 0.01):
        """Waits for the workflow to complete
        :param timeout_secs: how many seconds should be waited on a workflow
        the total wait time = wait_to_start_time + run_time. This is set to
        None by default as it is very hard to predict how long a workflow runs
        and how long it has to wait on other workflows before starting.
        :param wait_interval_secs: check interval secs if a workflow is started
        """
        wait_time = 0.0
        # Wait until the workflow is started.
        # Unless the main thread has stopped
        while not self._started and threading.main_thread().is_alive():
            # This piece of code checks if a workflow has started yet. If
            # it has not, it waits. A counter is implemented here because
            # incrementing a counter is much faster than checking system
            # time
            if (timeout_secs is not None
                    and wait_time > timeout_secs):
                raise TimeoutError(
                    "Waiting on a workflow that has not started within the"
                    " last {0} seconds".format(timeout_secs))
            time.sleep(wait_interval_secs)
            wait_time += wait_interval_secs

        # Stdout and stderr are written to files. So popen.wait() does not
        # block process completion with long stderr or stdout.
        if timeout_secs is not None and self._popen is not None:
            # Wait for timeout_secs number of secs minus te time that was
            # already spent waiting for the workflow to start
            self._popen.wait(timeout_secs - wait_time)
        elif self._popen is not None:
            self._popen.wait()
        else:
            # If self._popen is none, something went wrong during starting the
            # workflow
            pass

    @property
    def stdout(self) -> bytes:
        self.wait()
        with self.stdout_file.open('rb') as stdout:
            return stdout.read()

    @property
    def stderr(self) -> bytes:
        self.wait()
        with self.stderr_file.open('rb') as stderr:
            return stderr.read()

    @property
    def exit_code(self) -> int:
        self.wait()
        if self._popen is not None:
            return self._popen.returncode
        else:
            raise ValueError("No exit code after waiting. Please contact the "
                             "developers and report this issue.")


class WorkflowQueue(queue.Queue):
    """A Queue object that will keep running 'n' numbers of workflows
    simultaneously until the queue is empty."""

    def __init__(self):
        # No argument for maxsize. This queue is infinite.
        super().__init__()
        # Collect errors during thread processing.
        self._process_errors = []

    def put(self, item, block=True, timeout=None):
        """Like Queue.put() but tests if item is a Workflow"""
        if isinstance(item, Workflow):
            super().put(item, block, timeout)
        else:
            raise ValueError("Only Workflow type objects can be submitted to "
                             "this queue.")

    # Queue processing with workers example taken from
    # https://docs.python.org/3.5/library/queue.html?highlight=queue#queue.Queue.join  # noqa
    def process(self, number_of_threads: int = 1):
        """
        Processes the workflow queue with a number of threads
        :param number_of_threads: The number of threads
        """
        threads = []
        for _ in range(number_of_threads):
            thread = threading.Thread(target=self.worker)
            thread.start()
            threads.append(thread)
        self.join()
        # If errors are detected raise the first error. Raising all errors
        # is not possible.
        if len(self._process_errors) > 0:
            raise self._process_errors[0]
        for thread in threads:
            thread.join()

    def worker(self):
        """
        Run workflows until the queue is empty
        """
        while True:
            try:
                # We know the type is Workflow, because this was enforced in
                # the put method.
                workflow = self.get_nowait()  # type: Workflow
            except queue.Empty:
                break
            else:
                print(
                    "start '{name}' with command '{command}' in '{dir}'. "
                    "stdout: '{stdout_file}'. "
                    "stderr: '{stderr_file}'."
                    .format(
                        name=workflow.name,
                        command=workflow.command,
                        dir=workflow.cwd,
                        stdout_file=workflow.stdout_file,
                        stderr_file=workflow.stderr_file))
                workflow.run()
                # Collect the workflow errors.
                self._process_errors.extend(workflow.errors)
                self.task_done()
                # Some reporting
                result = ("python error during starting"
                          if workflow.errors else "done")
                print("'{0}' {1}.".format(workflow.name, result))
