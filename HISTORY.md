# Changelog for pytest-workflow

<!---
Newest changes should be on top.

NOTE: This document is user facing. Please word the changes in such a way 
that users understand how the changes affect the new version.
--->

## Current development version
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
