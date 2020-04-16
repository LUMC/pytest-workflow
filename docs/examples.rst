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
    "use_relative_output_paths": true,
    "default_runtime_attributes": {
      "docker_user": "$EUID"
      }
    }

``final_workflow_outputs_dir`` will make sure all the files produced in the
workflow will be copied to the ``final_workflow_outputs_dir``.
``use_relative_output_paths`` will get rid of all the Cromwell specific folders
such as ``call-myTask`` etc. The ``default_runtime_attributes`` are only
necessary when using docker containers. It will make sure all the files are
created by the same user that runs the test (docker containers run as root by
default). This will ensure that files can be deleted by pytest-workflow
afterwards.

The following yaml file tests a WDL pipeline run with Cromwell. In this case
Cromwell is installed via conda. The conda installation adds a wrapper to
Cromwell so it can be used as a command, instead of having to use the jar.

.. code-block:: yaml

  - name: My pipeline
    command: cromwell run -i inputs.json -o options.json moo.wdl
    files:
      - path: test-output/moo.txt.gz
        md5sum: 173fd8023240a8016033b33f42db14a2
    stdout:
      contains:
        - "WorkflowSucceededState"

WDL with miniwdl example
------------------------

For miniwdl please consult the `runner reference
<https://miniwdl.readthedocs.io/en/stable/runner_reference.html>`_ for more
information on the localization of output files as well as options to modify
the running of miniwdl from the environment.

Miniwdl will localize all the output files to an ``output_links`` directory
inside the test output directory. If you have a workflow with the output:

.. code-block::

        output {
            File moo_file = moo_task.out
            Array[File] stats = moo_task.stats_files
        }

Inside the ``output_links`` directory the directories ``moo_file`` and
``stats`` will be created. Inside these directories will be the produced files.

The following yaml file tests a WDL pipeline run with miniwdl.

.. code-block:: yaml

  - name: My pipeline
    command: miniwdl run -i inputs.json -d test-output/ moo.wdl
    files:
      - path: test-output/output_links/moo_file/moo.txt.gz
        md5sum: 173fd8023240a8016033b33f42db14a2
      - path: test-output/output_links/stats/number_of_moos_per_cow.tsv
        contains:
          - 42
      - path: test-output/output_links/stats/joy_invoking_moos.tsv
        must_not_contain:
          - 0

Please note that the trailing slash in ``-d test-output/`` is important. It
will ensure the files end up in the ``test-output`` directory.
