Running pytest-workflow
=======================
Run ``pytest`` from an environment with pytest-workflow installed.
Pytest will automatically gather files in the ``tests`` directory starting with
``test`` and ending in ``.yaml`` or ``.yml``.

The workflows are run automatically. Each workflow gets its own temporary
directory to run. These directories are cleaned up after the tests are
completed. If you wish to inspect the output of a failing workflow you can use
the ``--keep-workflow-wd`` flag to disable cleanup.

If you wish to change the temporary directory in which the workflows are run
use ``--basetemp <dir>`` to change pytest's base temp directory.