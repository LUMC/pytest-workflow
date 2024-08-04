==========
Changelog
==========


.. Newest changes should be on top.

.. This document is user facing. Please word the changes in such a way
.. that users understand how the changes affect the new version.

unreleased
---------------------------
+ ``-s`` pytest flag is now supported, streaming stdout/stderr as the tests run

version 2.1.0
---------------------------
+ Python version 3.7 support is dropped because it is deprecated. Python
  version 3.12 was added.
+ Fixed a bug where pytest 8.1+ would raise a ``PluginValidationError`` because
  the hook ``pytest_collect_file()`` has finally dropped the deprecated
  argument ``path`` from its specification.
+ Add extract_md5sum check on uncompressed contents of compressed output files.
  Gzipped files contain a timestamp which makes it hard to directly compare the
  md5sums of gzipped files.
+ Document naming conventions for Python test discovery

version 2.0.1
---------------------------
+ Fixed a bug where pytest-workflow would crash on logs that used non-ASCII
  characters where the chunk of size ``--stderr-bytes`` did not properly align
  with the used encoding.

version 2.0.0
---------------------------
This major release greatly cleans up the output of pytest-workflow in case of
an error as well as providing the stderr and stdout last bytes for debugging
purposes. When the exit code test fails all other tests from the workflow
are skipped.

+ Python 3.6 is no longer supported. It has been removed from github actions,
  as such we can no longer guarantee that pytest-workflow works properly
  with python 3.6.
+ Fix an issue where symlinks in git repositories could not be properly copied.
+ Added an optional encoding key for files, stdout and stderr so the file can
  be opened with the proper encoding.
+ Make content tests more efficient by reading each file only once instead of
  twice when there are both strings and regexes to check for.
+ When the ``--git-aware`` flag is used a submodule check is performed in order
  to assert that all submodules are properly checked out. This prevents
  unclear copying errors.
+ Tests are now skipped if the workflow does not exit with the desired exit
  code, except for the exit code tests, to reduce visual clutter when reporting
  failing tests.
+ Tests for checking file content are now skipped when the file does not exist
  in order to reduce visual clutter when reporting failing tests.
+ Test and support for Python 3.11.
+ Add ``--stderr-bytes`` or ``--sb`` option to change the maximum 
  number of bytes to display for the stderr and stdout on 
  command failure. 
+ Add stderr and stdout to be displayed on command failure
+ Document using ``pytest.ini`` as a way of setting specific per repository
  settings for pytest-workflow.
+ Add tests for nextflow.
+ Document the use of environment variables with pytest-workflow.
+ A minimum of pytest 7.0.0 is now a requirement for pytest-workflow.
  This fixes the deprecation warnings that started on the release of pytest
  7.0.0.
+ Throw a more descriptive error when a file copied with the --git-aware flag
  is not present on the filesystem anymore.
+ Document pytest flags ``-k`` and ``-m`` are not supported.

version 1.6.0
---------------------------
+ Add a ``--git-aware`` or ``--ga`` option to only copy copy files listed by
  git ls-files. This omits the ``.git`` folder, all untracked files and
  everything ignored by ``.gitignore``. This reduces the number of copy
  operations drastically.

  Pytest-workflow will now emit a warning when copying of a git directory is
  detected without the ``--git-aware`` option.

+ Add support and tests for Python 3.10

version 1.5.0
---------------------------
+ Add support for python 3.9
+ Update the print statement for starting jobs to be more structured. This will
  make the output easier to to read and use, since different fields (stdout,
  stderr, command, etc) are all on their own line.
+ Do not crash when directories can not be removed due to permission errors.
  Instead display a message to notify the users which directories could not be
  removed. These issues occurred sometimes when tests involving docker were
  run.

version 1.4.0
---------------------------
+ Usage of the ``name`` keyword argument in workflow marks is now deprecated.
  Using this will crash the plugin with a DeprecationWarning.
+ Update minimum python requirement in the documentation.
+ Removed redundant check in string checking code.
+ Add new options ``contains_regex`` and ``must_not_contain_regex`` to check
  for regexes in files and stdout/stderr.

version 1.3.0
---------------------------
Python 3.6 and pytest 5.4.0.0 are now minimum requirements for pytest-workflow.
This was necessary for fixing the deprecation warning issue and the issue with
the subdirectory evaluation. This also gave the opportunity to simplify the
source code using new python 3.6 syntax.

+ Using the ``name`` keyword argument in workflow marks will be deprecated
  from 1.4.0 onwards. A warning will be given if this is used. For example:
  ``pytest.mark.workflow(name="my_workflow")``. Use the name as argument
  instead: ``pytest.mark.workflow("my_workflow")``.
+ Allow running custom tests on multiple workflows. You can now use
  ``pytest.mark.workflow("worflow name 1", "workflow name 2", ...)``.
  (`Issue #75 <https://github.com/LUMC/pytest-workflow/issues/75>`_)
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
