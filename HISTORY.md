# Changelog for pytest-workflow

<!---
Newest changes should be on top.

NOTE: This document is user facing. Please word the changes in such a way 
that users understand how the changes affect the new version.
--->

## Current development version
+ Save stdout and stderr of each workflow to a file and report their locations
to stdout when running `pytest`.
+ Comprehensible failure messages were added to make debugging workflows
easier.

## Version 0.1.0
+ A full set of examples is now provided in the README.
+ Our code base is now checked by pylint and bandit as part of our test
procedure to ensure that our code adheres to python and security best 
practices.
+ Add functionality to test whether certain strings exist in files, stdout and 
stderr.
+ Enable easy to understand output when using pytest verbose mode 
(`pytest -v`).  
The required code refactoring has simplified the code base and made it easier 
to maintain.
+ Enable the checking of non-existing files
+ Enable the checking of file md5sums
+ Use a schema structure that is easy to use and understand.
+ Pytest-workflow now has continuous integration and coverage reporting,
so we can detect regressions quickly and only publish well-tested versions.
+ Fully parametrized tests enabled by changing code structure.
+ Initialized pytest-workflow with option to test if files exist. 
