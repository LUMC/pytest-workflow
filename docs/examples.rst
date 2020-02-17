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

By default Cromwell outputs its files in the execution folder in a
deeply-nested folder structure. Cromwell can output to a separate
workflow-outputs folder and since Cromwell version 40 it can also output the
files in a structure that is not nested. For more information check the
`Cromwell documentation on global workflow options
<https://cromwell.readthedocs.io/en/stable/wf_options/Overview/#global-workflow-options>`_.

In order to run Cromwell for CI tests an options file should be present in the
repository with the following contents:

.. code-block:: json

    {
    "final_workflow_outputs_dir": "test-output",
    "use_relative_output_paths": true
    }

``final_workflow_outputs_dir`` will make sure all the files produced in the
workflow will be copied to the ``final_workflow_outputs_dir``.
``use_relative_output_paths`` will get rid of all the Cromwell specific folders
such as ``call-myTask`` etc.

The following yaml file tests a Cromwell pipeline. In this case Cromwell is
installed via conda. The conda installation adds a wrapper to Cromwell so it
can be used as a command, instead of having to use the jar.

.. code-block:: yaml

  - name: My pipeline
    command: cromwell run -i inputs.json -o options.json moo.wdl
    files:
      - path: test-output/moo.txt.gz
        md5sum: 173fd8023240a8016033b33f42db14a2
    stdout:
      contains:
        - "WorkflowSucceededState"

