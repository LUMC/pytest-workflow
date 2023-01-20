==================================
Writing tests with pytest-workflow
==================================

Getting started
---------------

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

Test options
------------

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
        encoding: UTF-8                # Encoding for the text file (optional). Defaults to system locale.

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
      encoding: ASCII                  # Encoding for stdout (optional). Defaults to system locale.

  - name: mission impossible           # Also failing workflows can be tested
    tags:                              # A list of tags that can be used to select which test
      - should fail                    # is run with pytest using the `--tag` flag.
    command: bash impossible.sh
    exit_code: 2                       # What the exit code should be (optional, if not given defaults to 0)
    files:
      - path: "fail.log"               # Multiple files can be tested for each workflow
      - path: "TomCruise.txt.gz"       # Gzipped files can also be searched, provided their extension is '.gz'
        contains:
          - "starring"
    stderr:                            # Options for testing stderr (optional)
      contains:                        # A list of strings which should be in stderr (optional)
        - "BSOD error, please contact the IT crowd"
      must_not_contain:                # A list of strings which should NOT be in stderr (optional)
        - "Mission accomplished!"
      encoding: UTF-16                 # Encoding for stderr (optional). Defaults to system locale.

  - name: regex tests
    command: echo Hello, world
    stdout:
      contains_regex:                  # A list of regex patterns that should be in stdout (optional)
        - 'Hello.*'                    # Note the single quotes, these are required for complex regexes
        - 'Hello .*'                   # This will fail, since there is a comma after Hello, not a space

      must_not_contain_regex:          # A list of regex patterns that should not be in stdout (optional)
        - '^He.*'                      # This will fail, since the regex matches Hello, world
        - '^Hello .*'                  # Complex regexes will break yaml if double quotes are used


The above YAML file contains all the possible options for a workflow test.

Please see the `Python documentation on regular expressions
<https://docs.python.org/3/library/re.html>`_ to see how Python handles escape
sequences.

.. note::
    Workflow names must be unique. Pytest workflow will crash when multiple
    workflows have the same name, even if they are in different files.

Environment variables
----------------------
Pytest-workflow runs tests in the same environment as in which the pytest
executable was started. This means programs started in tests can use
environnment variables. However, environment variables inside the command
section itself are quoted by pytest-workflow using
`shlex.quote <https://docs.python.org/3/library/shlex.html#shlex.quote>`_.
See the examples below:

.. code-block:: YAML

    - name: Try to use an environment variable
      command: echo $MY_VAR
      # Output will be literally "$MY_VAR"

    - name: Circumenvent shlex quoting by explicitly starting the command in a shell.
      command: bash -c 'echo $MY_VAR'
      # Output will be the content of $MY_VAR

    - name: Use a program that checks an environment variable
      command: singularity run my_container.sif
      # Correctly uses "SINGULARITY_" prefixed variables

If you want to use shell scripting features such as environment
variables inside ``command``, you need to explicitly set the shell as shown
above.

Writing custom tests
--------------------

Pytest-workflow provides a way to run custom tests on files produced by a
workflow.

.. code-block:: python

    import pathlib
    import pytest

    @pytest.mark.workflow('files containing numbers')
    def test_div_by_three(workflow_dir):
        number_file = pathlib.Path(workflow_dir, "123.txt")
        number_file_content = number_file.read_text()
        assert int(number_file_content) % 3 == 0

The ``@pytest.mark.workflow('files containing numbers')`` marks the test
as belonging to a workflow named ``files containing numbers``. This test will
only run if the workflow 'files containing numbers' has run.

Multiple workflows can use the same custom test like this:

.. code-block:: python

    import pathlib
    import pytest

    @pytest.mark.workflow('my_workflow', 'another_workflow',
                          'yet_another_workflow')
    def test_ensure_long_logs_are_written(workflow_dir):
        log = pathlib.Path(workflow_dir, "log.out")
        assert len(log.readtext()) > 10000

``workflow_dir`` is a fixture. It does not work without a
``pytest.mark.workflow('workflow_name')`` mark.  This is a
`pathlib.Path <https://docs.python.org/3/library/pathlib.html>`_ object that
points to the folder where the named workflow was executed. This allows writing
of advanced python tests for each file produced by the workflow.

Custom tests must follow the `conventions for Python test discovery
<https://docs.pytest.org/en/latest/explanation/goodpractices.html#conventions-for-python-test-discovery>`_,
which constrains the names of files and functions containing custom tests.

.. note::

    stdout and stderr are available as files in the root of the
    ``workflow_dir`` as ``log.out`` and ``log.err`` respectively.
