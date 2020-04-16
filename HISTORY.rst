==========
Changelog
==========

.. Newest changes should be on top.

.. This document is user facing. Please word the changes in such a way
.. that users understand how the changes affect the new version.

version 1.3.0-dev
---------------------------
Python 3.6 and pytest 5.4.0.0 are now minimum requirements for pytest-workflow.
This was necessary for fixing the deprecation warning issue and the issue with
the subdirectory evaluation. This also gave the opportunity to simplify the
source code using new python 3.6 syntax.

+ Add a miniwdl example to the documentation.
+ Added a ``--symlink`` flag to the CLI that changes the copying behavior.
  Instead of copying, it creates a similar directory structure where all files
  are linked to with symbolic links. (`Issue #96
  <https://github.com/LUMC/pytest-workflow/issues/98>`_)
+ Refactored the code base. Python 3.6's f-strings and type annotation were
  used consistently throughout the project. Some code was rewritten to be more
  concise and readable.
+ Improved speed for searching string content in files. This was achieved by
  removing intermediate functions and simplifying the search function.
+ Improved speed for calculating md5sums by increasing the read buffer size
  from 8k to 64k.
+ Solve issue where pytest would display a lot of deprecation warnings when
  running pytest-workflow. (`Issue #98
  <https://github.com/LUMC/pytest-workflow/issues/98>`_)
+ Fix issues with later versions of Cromwell and Snakemake in CI testing.
+ Add correct subdirectory evaluation to fix issue where ``/parent-dir/child``
  was evaluated as a subdirectory of ``/parent`` due to starting with the same
  string. (`Issue #95 <https://github.com/LUMC/pytest-workflow/issues/95>`_)
+ Fix error in cromwell example which did not allow it to remove folders
  correctly.

version 1.2.3
---------------------------
+ Added missing ``help`` section for ``--tag`` on the CLI.
+ Documentation: added usage chapter for pytest-workflow specific options.
+ Documentation: updated Cromwell example.
+ Removed redundant references to pylint in code comments and CI.
+ Remove Codacy from the CI.

version 1.2.2
---------------------------
+ Test against python3.8
+ Do not test on python3.5 snakemake as it crashes. Added test for python3.7
  snakemake.
+ Fix a typo in the documentation.
+ Add tags 'wdl', 'cromwell' and 'snakemake' to the package to increase
  discoverability.
+ Remove pylint from the lint procedure as it was very strict and got stricter
  with every update, causing tests that previously succeeded to fail on a
  regular basis.
+ Make sure pytest-workflow crashes when multiple workflows have the same name,
  even when they are in different files.
+ Added setup.cfg to include license in source distributions on PyPI for
  future versions

version 1.2.1
---------------------------
+ Since pytest 4.5.0 unknown markers give a warning. ``@pytest.mark.workflow``
  markers are now added to the configuration. Information on usage shows up
  with ``pytest --mark``.
+ Updated documentation to reflect the move to conda-forge as requested on
  `this github issue
  <https://github.com/bioconda/bioconda-recipes/issues/13964>`_.
+ Updated documentation on how to test Cromwell + WDL pipelines.


version 1.2.0
---------------------------
+ Giving a ``--basetemp`` directory that is within pytest's current working
  directory will now raise an exception to prevent infinite recursive directory
  copying.
+ The cleanup message is only displayed when pytest-workflow is used.
+ Added a ``--keep-workflow-wd-on-fail`` or ``--kwdof`` flag. Setting this flag
  will make sure temporary directories are only deleted when all tests succeed.

version 1.1.2
---------------------------
+ Fixed a bug where the program would hang indefinitely after a user input
  error.

version 1.1.1
---------------------------
+ Added ``--kwd`` as alias for ``--keep-workflow-wd``. Notify the user of
  deletion of temporary directories and logs.
+ Released pytest-workflow as a `conda package on bioconda
  <https://bioconda.github.io/recipes/pytest-workflow/README.html>`_.

version 1.1.0
---------------------------
+ Enabled custom tests on workflow files.

Version 1.0.0
---------------------------
Lots of small fixes that improve the usability of pytest-workflow are included
in version 1.0.0.

+ Gzipped files can now also be checked for contents. Files with '.gz' as
  extension are automatically decompressed.
+ ``stdout`` and ``stderr`` of workflows are now streamed to a file instead of
  being kept in memory. This means you can check the progress of a workflow by
  running ``tail -f <stdout or stderr>``. The location of ``stdout`` and
  ``stderr`` is now reported at the start of each worflow. If the
  ``--keep-workflow-wd`` is not set the ``stdout`` and ``stderr`` files will be
  deleted with the rest of the workflow files.
+ The log reports now when a workflow is starting, instead of when it is added
  to the queue. This makes it easier to see which workflows are currently
  running and if you forgot to use the ``--workflow-threads`` or ``--wt`` flag.
+ Workflow exit code failures now mention the name of the workflow. Previously
  the generic name "Workflow" was used, which made it harder to figure out
  which workflows failed.
+ When tests of file content fail because the file does not exist, a different
  error message is given compared to when the file exist, but the content is
  not there, which makes debugging easier. Also the accompanying
  "FileNotFound" error stacktrace is now suppressed, which keeps the test
  output more pleasant.
+ When tests of stdout/stderr content or file content fail a more informative
  error message is given to allow for easier debugging.
+ All workflows now get their own folder within the `same` temporary directory.
  This fixes a bug where if ``basetemp`` was not set, each workflow would get
  its own folder in a separate temp directory. For example running workflows
  'workflow1' and 'workflow2' would create two temporary folders:

  '/tmp/pytest_workflow\_\ **33mrz5a5**/workflow1' and
  '/tmp/pytest_workflow\_\ **b8m1wzuf**/workflow2'

  This is now changed to have all workflows in one temporary directory per
  pytest run:

  '/tmp/pytest_workflow\_\ **33mrz5a5**/workflow1' and
  '/tmp/pytest_workflow\_\ **33mrz5a5**/workflow2'

+ Disallow empty ``command`` and ``name`` keys. An empty ``command`` caused
  pytest-workflow to hang. Empty names are also disallowed.

Version 0.4.0
---------------------------
+ Added more information to the manual on how to debug pipelines and use
  ``pytest-workflow`` outside a virtual environment.
+ Reworked code to use ``tempfile.mkdtemp`` to create a truly unique
  temporary working directory if the ``--basetemp`` flag is not used. This
  replaces the old code which dependeded on pytest internal code which was
  flagged as deprecated. Also more information was added to the manual about
  the use of ``--basetemp``.
+ Added a test case for WDL pipelines run with Cromwell and wrote an example
  for using WDL+Cromwell in the manual.
+ Added ``--tag`` flag to allow for easier selection of workflows during
  testing.
+ Added a test case for snakemake pipelines and wrote an example for using
  pytest-workflow with snakemake in the manual.

Version 0.3.0
---------------------------
+ Improved the log output to look nicer and make workflow log paths easier to
  find in the test output.
+ Fixed an error that polluted the log message with a pytest stacktrace when
  running more than one workflow. Measures are taken in our test framework to
  detect such issues in the future.
+ Added the possibility to run multiple workflows simultaneously with the
  ``--workflow-threads`` or ``--wt`` flag.
+ Made code easier to maintain by using stdlib instead of pytest's ``py`` lib
  in all of the code.
+ Added a schema check to ensure that tests have unique names when whitespace
  is removed.

Version 0.2.0
---------------------------
+ Cleanup the readme and move advanced usage documentation to our readthedocs
  page.
+ Start using sphinx and readthedocs.org for creating project documentation.
+ The temporary directories in which workflows are run are automatically
  cleaned up at the end of each workflow test. You can disable this behaviour
  by using the ``--keep-workflow-wd`` flag, which allows you to inspect the
  working directory after the workflow tests have run. This is useful for
  debugging workflows.
+ The temporary directories in which workflows are run can now be
  changed by using the ``--basetemp`` flag. This is because pytest-workflow now
  uses the built-in tmpdir capabilities of pytest.
+ Save stdout and stderr of each workflow to a file and report their locations
  to stdout when running ``pytest``.
+ Comprehensible failure messages were added to make debugging workflows
  easier.

Version 0.1.0
---------------------------
+ A full set of examples is now provided in the README.
+ Our code base is now checked by pylint and bandit as part of our test
  procedure to ensure that our code adheres to python and security best
  practices.
+ Add functionality to test whether certain strings exist in files, stdout and
  stderr.
+ Enable easy to understand output when using pytest verbose mode
  (``pytest -v``).
  The required code refactoring has simplified the code base and made it easier
  to maintain.
+ Enable the checking of non-existing files
+ Enable the checking of file md5sums
+ Use a schema structure that is easy to use and understand.
+ Pytest-workflow now has continuous integration and coverage reporting,
  so we can detect regressions quickly and only publish well-tested versions.
+ Fully parametrized tests enabled by changing code structure.
+ Initialized pytest-workflow with option to test if files exist. 
