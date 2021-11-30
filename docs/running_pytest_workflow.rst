=======================
Running pytest-workflow
=======================

Usage
-----

Run ``pytest`` from an environment with pytest-workflow installed or
``python3 -m pytest`` if using a system-wide or user-wide installation.
Pytest will automatically gather files in the ``tests`` directory starting with
``test`` and ending in ``.yaml`` or ``.yml``.

The workflows are run automatically. Each workflow gets its own temporary
directory to run. The ``stdout`` and ``stderr`` of the workflow command are
also saved to this directory to ``log.out`` and ``log.err`` respectively.

To check the progress of a workflow while it is running you can use ``tail -f``
on the ``stdout`` or ``stderr`` file of the workflow. The locations of these
files are reported in the log as soon as a workflow is started.

Specific pytest options for pytest workflow
------------------------------------------------

.. argparse::
    :module: pytest_workflow.plugin
    :func: __pytest_workflow_cli
    :prog: pytest

Temporary directory cleanup and creation
----------------------------------------

The temporary directories are cleaned up after the tests are completed.
If you wish to inspect the output of a failing
workflow you can use the ``--keep-workflow-wd`` or ``--kwd`` flag to disable
cleanup. This will also make sure the logs of the pipeline are not deleted.
If you only want to keep directories when one or more tests fail you can use
the ``--keep-workflow-wd-on-fail`` or ``--kwdof`` flag.
``--keep-workflow-wd-on-fail`` will keep all temporary directories, even from
workflows that have succeeded.

If you wish to change the temporary directory in which the workflows are run
use ``--basetemp <dir>`` to change pytest's base temp directory.

.. warning::

  When a directory is passed to ``--basetemp`` some of the directory
  contents will be deleted. For example: if your workflow is named
  ``"my workflow"`` then any file or directory named ``my_workflow`` will be
  deleted. This makes sure you start with a clean slate if you run pytest
  again with the same ``basetemp`` directory.
  DO NOT use ``--basetemp`` on directories where none of the
  contents should be deleted.

The temporary directories created are copies of pytest's root directory, the
directory from which it runs the tests. If you have lots of tests, and if you
have a large repository, this may take a lot of disk space. To alleviate this
you can use the ``--symlink`` flag which will create the same directory layout
but instead symlinks the files instead of copying them. This carries with it
the risk that the tests may alter files from your work directory. If there are
a lot of large files and files are used read-only in tests, then it will use a
lot less disk space and be faster as well.

.. note::

    When your workflow is version controlled in git please use the
    ``--git-aware`` option. This will omit the ``.git`` directory and all
    files ignored by git. This reduces the number of copy operations
    significantly.


Running multiple workflows simultaneously
-----------------------------------------

To run multiple workflows simultaneously you can use
``--workflow-threads <int>`` or ``--wt <int>`` flag. This defines the number
of workflows that can be run simultaneously. This will speed up things if
you have enough resources to process these workflows simultaneously.

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
