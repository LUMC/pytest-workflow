===============
pytest-workflow
===============

.. Badges have empty alts. So nothing shows up if they do not work.
.. This fixes readthedocs issues with badges.
.. image:: https://img.shields.io/pypi/v/pytest-workflow.svg
  :target: https://pypi.org/project/pytest-workflow/
  :alt:

.. image:: https://img.shields.io/conda/v/conda-forge/pytest-workflow.svg
  :target: https://anaconda.org/conda-forge/pytest-workflow
  :alt:

.. image:: https://img.shields.io/pypi/pyversions/pytest-workflow.svg
  :target: https://pypi.org/project/pytest-workflow/
  :alt:

.. image:: https://img.shields.io/pypi/l/pytest-workflow.svg
  :target: https://github.com/LUMC/pytest-workflow/blob/master/LICENSE
  :alt:

.. image:: https://travis-ci.org/LUMC/pytest-workflow.svg?branch=develop
  :target: https://travis-ci.org/LUMC/pytest-workflow
  :alt:

.. image:: https://codecov.io/gh/LUMC/pytest-workflow/branch/develop/graph/badge.svg
  :target: https://codecov.io/gh/LUMC/pytest-workflow
  :alt:

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.3757727.svg
  :target: https://doi.org/10.5281/zenodo.3757727
  :alt: More information on how to cite pytest-workflow here.

pytest-workflow is a workflow-system agnostic testing framework that aims 
to make pipeline/workflow testing easy by using YAML files for the test 
configuration. Whether you write your pipelines in WDL, snakemake, nextflow, 
bash or any other workflow framework, pytest-workflow makes testing easy.
pytest-workflow is build on top of the pytest test framework.

For our complete documentation and examples checkout our
`readthedocs page <https://pytest-workflow.readthedocs.io/>`_.


Installation
============
Pytest-workflow requires Python 3.7 or higher. It is tested on Python 3.7,
3.8, 3.9, 3.10 and 3.11.

- Make sure your virtual environment is activated.
- Install using pip ``pip install pytest-workflow``
- Create a ``tests`` directory in the root of your repository.
- Create your test yaml files in the ``tests`` directory.

Pytest-workflow is also available as a `conda package on conda-forge
<https://anaconda.org/conda-forge/pytest-workflow>`_. Follow
`these instructions 
<http://conda-forge.org/docs/user/introduction.html#how-can-i-install-packages-from-conda-forge>`_ 
to set up channels properly in order to use conda-forge. Alternatively,
you can `set up the channels correctly for use with bioconda 
<https://bioconda.github.io/index.html#set-up-channels>`_. After that ``conda
install pytest-workflow`` can be used to install pytest-workflow. 

Quickstart
==========

Run ``pytest`` from an environment with pytest-workflow installed.
Pytest will automatically gather files in the ``tests`` directory starting with
``test`` and ending in ``.yaml`` or ``.yml``.

To check the progress of a workflow while it is running you can use ``tail -f``
on the ``stdout`` or ``stderr`` file of the workflow. The locations of these
files are reported in the log as soon as a workflow is started.

For debugging pipelines using the ``--kwd`` or ``--keep-workflow-wd`` flag  is
recommended. This will keep the workflow directory and logs after the test run
so it is possible to check where the pipeline crashed. The ``-v`` flag can come
in handy as well as it gives a complete overview of succeeded and failed tests.

Below is an example of a YAML file that defines a test:

.. code-block:: yaml

  - name: Touch a file
    command: touch test.file
    files:
      - path: test.file

This will run ``touch test.file`` and check afterwards if a file with path:
``test.file`` is present. It will also check if the ``command`` has exited
with exit code ``0``, which is the only default test that is run. Testing
workflows that exit with another exit code is also possible. Several other
predefined tests as well as custom tests are possible.

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

For more information on how Python parses regular expressions, see the `Python
documentation <https://docs.python.org/3/library/re.html>`_.

Documentation for more advanced use cases including the custom tests can be
found on our `readthedocs page <https://pytest-workflow.readthedocs.io/>`_.
