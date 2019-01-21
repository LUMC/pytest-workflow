
=======================
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
    command: echo vroom croom

With the command ``pytest --tag moo`` only the workflow named 'moo' will be
run. With ``pytest --tag 'rooster sound'`` only the 'cock-a-doodle-doo'
workflow will run. Multiple tags can be used like this:
``pytest --tag 'rooster sound' --tag animal`` This will run all workflows that
have both 'rooster sound' and 'animal'.

==================================
Writing tests with pytest-workflow
==================================

Below is an example of a YAML file that defines a test:

.. code-block:: yaml

  - name: Touch a file
    command: touch test.file
    files:
      - path: test.file

This will run ``touch test.file`` and check afterwards if a file with path:
``test.file`` is present. It will also check if the ``command`` has exited
with exit code ``0``, which is the only default test that is run. Testing
workflows that exit with another exit code is also possible.

A more advanced example:

.. code-block:: yaml

  - name: moo file                     # The name of the workflow (required)
    command: bash moo_workflow.sh      # The command to execute the workflow (required)
    files:                             # A list of files to check (optional)
      - path: "moo.txt"                # File path. (Required for each file)
        contains:                      # A list of strings that should be in the file (optional)
          - "moo"
        must_not_contain:              # A list of strings that should NOT be in the file (optional)
          - "Cock a doodle doo"
        md5sum: e583af1f8b00b53cda87ae9ead880224   # Md5sum of the file (optional)

  - name: simple echo                  # A second workflow. Notice the starting `-` which means
    command: "echo moo"                # that workflow items are in a list. You can add as much workflows as you want
    files:
      - path: "moo.txt"
        should_exist: false            # Whether a file should be there or not. (optional, if not given defaults to true)
    stdout:                            # Options for testing stdout (optional)
      contains:                        # List of strings which should be in stdout (optional)
        - "moo"
      must_not_contain:                # List of strings that should NOT be in stout (optional)
        - "Cock a doodle doo"

  - name: mission impossible           # Also failing workflows can be tested
    tags:                              # A list of tags that can be used to select which test
      - should fail                    # is run with pytest using the `--tag` flag.
    command: bash impossible.sh
    exit_code: 2                       # What the exit code should be (optional, if not given defaults to 0)
    files:
      - path: "fail.log"               # Multiple files can be tested for each workflow
      - path: "TomCruise.txt"
    stderr:                            # Options for testing stderr (optional)
      contains:                        # A list of strings which should be in stderr (optional)
        - "BSOD error, please contact the IT crowd"
      must_not_contain:                # A list of strings which should NOT be in stderr (optional)
        - "Mission accomplished!"


The above YAML file contains all the possible options for a workflow test.
