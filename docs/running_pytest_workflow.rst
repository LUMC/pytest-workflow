=======================
Running pytest-workflow
=======================
Run ``pytest`` from an environment with pytest-workflow installed or
``python3 -m pytest`` if using a system-wide or user-wide installation.
Pytest will automatically gather files in the ``tests`` directory starting with
``test`` and ending in ``.yaml`` or ``.yml``.

The workflows are run automatically. Each workflow gets its own temporary
directory to run. The ``stdout`` and ``stderr`` of the workflow command are
also saved to this directory to ``log.out`` and ``log.err`` respectively.
The temporary directories are cleaned up after the tests are completed.
If you wish to inspect the output of a failing
workflow you can use the ``--keep-workflow-wd`` or ``--kwd`` flag to disable
cleanup. This will also make sure the logs of the pipeline are not deleted.
If you only want to keep directories when one or more tests fail you can use
the ``--keep-workflow-wd-on-fail`` or ``--kwdof`` flag.

If you wish to change the temporary directory in which the workflows are run
use ``--basetemp <dir>`` to change pytest's base temp directory.

.. container:: warning

  WARNING: When a directory is passed to ``--basetemp`` some of the directory
  contents will be deleted. For example: if your workflow is named
  ``"my workflow"`` then any file or directory named ``my_workflow`` will be
  deleted. This makes sure you start with a clean slate if you run pytest
  again with the same ``basetemp`` directory.
  DO NOT use ``--basetemp`` on directories where none of the
  contents should be deleted.

To run multiple workflows simultaneously you can use
``--workflow-threads <int>`` or ``--wt <int>`` flag. This defines the number
of workflows that can be run simultaneously. This will speed up things if
you have enough resources to process these workflows simultaneously.

To check the progress of a workflow while it is running you can use ``tail -f``
on the ``stdout`` or ``stderr`` file of the workflow. The locations of these
files are reported in the log as soon as a workflow is started.

Running specific workflows
----------------------------
To run a specific workflow use the ``--tag`` flag. Each workflow is tagged with
its own name and additional tags in the ``tags`` key of the yaml.

.. code-block:: yaml

  - name: moo
    tags:
      - animal
    command: echo moo
  - name: cock-a-doodle-doo
    tags:
      - rooster sound
      - animal
    command: echo cock-a-doodle-doo
  - name: vroom vroom
    tags:
      - car
    command: echo vroom vroom

With the command ``pytest --tag moo`` only the workflow named 'moo' will be
run. With ``pytest --tag 'rooster sound'`` only the 'cock-a-doodle-doo'
workflow will run. Multiple tags can be used like this:
``pytest --tag 'rooster sound' --tag animal`` This will run all workflows that
have both 'rooster sound' and 'animal'.

Internally names and tags are handled the same so if the following tests:

.. code-block:: yaml

  - name: hello
    command: echo 'hello'
  - name: hello2
    command: echo 'hello2'
    tags:
      - hello

are run with ``pytest --tag hello`` then both ``hello`` and ``hello2`` are run.
