==========
Changelog
==========

.. Newest changes should be on top.

.. NOTE: This document is user facing. Please word the changes in such a way
.. that users understand how the changes affect the new version.

Version 0.4.0-dev
---------------------------

+ Added ``--tag`` flag to allow for easier selection of workflows during
  testing.
+ Adds additional test cases for snakemake pipelines.

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
