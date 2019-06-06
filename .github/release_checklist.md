Release checklist
- [ ] Check outstanding issues on JIRA and Github
- [ ] Check [latest documentation
](https://pytest-workflow.readthedocs.io/en/latest/) looks fine
- [ ] Create a release branch 
  - [ ] Set version to a stable number.
  - [ ] Change current development version in `HISTORY.rst` to stable version.
- [ ] Merge the release branch into `master`
- [ ] Create a test pypi package from the master branch. ([Instructions.](
https://packaging.python.org/tutorials/packaging-projects/#generating-distribution-archives
))
- [ ] Install the packages from the test pypi repository to see if they work.
- [ ] Created an annotated tag with the stable version number. Include changes 
from history.rst.
- [ ] Push tag to remote.
- [ ] Push tested packages to pypi
- [ ] merge `master` branch back into `develop`.
- [ ] Add updated version number to develop
- [ ] Update the package on conda-forge
- [ ] Build the new tag on readthedocs. Only build the last patch version of
each minor version. So `1.1.1` and `1.2.0` but not `1.1.0`, `1.1.1` and `1.2.0`.
