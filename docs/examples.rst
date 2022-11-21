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
        - "workflow finished with status 'Succeeded'"

WDL with miniwdl example
------------------------

For miniwdl please consult the `runner reference
<https://miniwdl.readthedocs.io/en/stable/runner_reference.html>`_ for more
information on the localization of output files as well as options to modify
the running of miniwdl from the environment.

Miniwdl will localize all the output files to an ``output_links`` directory
inside the test output directory. If you have a workflow with the output::

    output {
        File moo_file = moo_task.out
        Array[File] stats = moo_task.stats_files
    }

Inside the ``out`` directory the directories ``moo_file`` and
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

Nextflow example
-----------------

With nextflow each process is run in a unique directory where the output files will
also be stored. Nextflow can output a copy of the output files to a separate workflow-outputs 
directory. This can be achieved by defining a ``publishDir`` in the process. Through ``params.outdir``
it is possible to define the output directory when running the code.

An example code defining a ``publishDir`` is listed below. ::

    process Hello {
        publishDir = [
            path: { "${params.outdir}/hello"}
        ]

        output:
        path "HelloWorld.txt"
        script:
        """
        echo "Hello World!" > HelloWorld.txt
        """
    }

    workflow {
        Hello
    }

To run the code listed above the following command can be used in which ``examplecode.nf`` is the code listed above:

.. code-block:: bash

    nextflow run examplecode.nf --outdir test-output

``publishDir`` will make it so that all the output files of the process are copied to the given directory. 
``--outdir`` is used to define the path the output files will go to. In this case ``HelloWorld.txt`` will 
be copied to the  directory called ``test-output/hello``.

An example yaml file that could be used to test the nextflow pipeline from ``examplecode.nf`` is listed
below.

.. code-block:: yaml

    - name: My pipeline
      command: nextflow run examplecode.nf --outdir test-output
      files:
        - path: "test-output/hello/HelloWorld.txt"

Bash example
------------

The following is an example of a Bash file that can run directly as a script, or sourced to test each function separately:

.. code-block:: bash

    #!/usr/bin/env bash

    function say_hello() {
        local name="$1"
        echo "Hello, ${name}!"
    }

    function main() {
        say_hello world
    }

    # Only execute main when this file is run as a script
    if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
        main
    fi

Save the bash file as ``script.sh``, and test it with the following pytest-workflow configuration:


.. code-block:: yaml

    - name: test bash script
      command: bash script.sh
      stdout:
        contains:
          - "Hello, world!"

    - name: test bash function
      command: >
        bash -c "
        source script.sh;
        say_hello pytest-workflow
        "
      stdout:
        contains:
          - "Hello, pytest-workflow!"
        must_not_contain:
          - "Hello, world!"
