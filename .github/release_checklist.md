Release checklist
- [ ] Check outstanding issues on JIRA and Github
- [ ] Check [latest documentation
](https://pytest-workflow.readthedocs.io/en/latest/) looks fine
- [ ] Create a release branch 
  - [ ] Set version to a stable number.
  - [ ] Change current development version in `HISTORY.rst` to stable version.
- [ ] Create a test pypi package from the release branch. ([Instructions.](
https://packaging.python.org/tutorials/packaging-projects/#generating-distribution-archives
))
- [ ] Merge the release branch into `master`
- [ ] Created an annotated tag with the stable version number. Include changes 
from history.rst.
- [ ] Push tag to remote.
- [ ] Create packages and push to pypi
- [ ] merge `master` branch back into `develop`.
- [ ] Add updated version number to develop