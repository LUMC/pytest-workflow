==================
Examples
==================

Snakemake example
-----------------

An example yaml file that could be used to test a snakemake pipeline is listed
below.

.. code-block:: yaml

    - name: test-dry-run
      command: snakemake -n -r -p -s Snakefile
    - name: test-full-run
      command: snakemake -r -p -s Snakefile
      files:
        - "my_output.txt"
      stderr:
        contains:
         - "(100%) done"

WDL with Cromwell example
-------------------------

Below an example yaml file is explained which can be used to test a WDL
pipeline run through Cromwell.

One problem with Cromwell is the way it handles relative paths and how it
handles the input file:

+ Relative paths are written only within the ``cromwell-executions`` folder.
  If you want to write outside this folder you need absolute paths. This is
  fine but for testing your pipeline ``pytest-workflow`` creates a temporary
  folder from which the pipeline is run. You don't know beforehand which path
  this is, but you could use the environment variable ``$PWD``.
+ However the second problem is that inputs can only be supplied to Cromwell in
  a json file, not on the command line. So you cannot dynamically choose an
  output folder. You have to rewrite the input file.

To fix this problem you can write ``command`` to be a bash script that injects
``$PWD`` into the inputs.json.

.. code-block:: yaml

  - name: My pipeline
    command: >-
      bash -c '
      TEST_JSON=tests/inputs/my_pipeline_test1.json ;
      sed -i "2i\"my_pipeline.output_dir\":\"$PWD/test-output\"," $TEST_JSON ;
      cromwell run -i $TEST_JSON simple.wdl'
    files:
      - path: test-output/moo.txt.gz
        md5sum: 173fd8023240a8016033b33f42db14a2
    stdout:
      contains:
        - "WorkflowSucceededState"

``sed -i "2i\"my_pipeline.output_dir\":\"$PWD/test-output\"," $TEST_JSON``
inserts ``"my_pipeline.output_dir":"</pytest/temporary/dir>/test-output",`` on
the second line of ``$TEST_JSON``. This solves the problem. File paths can now
be traced from ``test-output`` as demonstrated in the example.
