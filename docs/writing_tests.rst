==================================
Writing tests with pytest-workflow
==================================

In order to write tests that are discoverable by the plugin you need to
complete the following steps.

- Create a ``tests`` directory in the root of your repository.
- Create your test yaml files in the ``tests`` directory. The files need to
  start with ``test`` and have a ``.yml`` or ``.yaml`` extension.

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
