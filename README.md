[![Codacy Badge Code Quality](https://api.codacy.com/project/badge/Grade/f8bc14b0a507429eac7c06194fafcd59)](https://www.codacy.com/app/LUMC/pytest-workflow?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=LUMC/pytest-workflow&amp;utm_campaign=Badge_Grade) 
[![codecov](https://codecov.io/gh/LUMC/pytest-workflow/branch/develop/graph/badge.svg)](https://codecov.io/gh/LUMC/pytest-workflow)
[![Build Status](https://travis-ci.org/LUMC/pytest-workflow.svg?branch=develop)](https://travis-ci.org/LUMC/pytest-workflow)

# pytest-workflow
pytest-workflow is a pytest plugin that aims to make pipeline/workflow testing easy 
by using yaml files for the test configuration.

## Introduction

Writing workflows is hard. Testing if they are correct is even harder. Testing with
bash scripts or other code has some flaws. Is this bug in the pipeline or in my test-framework?
Pytest-workflow aims to make testing as simple as possible so you can focus on debugging
your pipeline.

## Installation
Pytest-workflow is tested on python 3.5, 3.6 and 3.7. Python 2 is not supported.

- Make sure your virtual environment is activated.
- Install using pip `pip install pytest-workflow`
- Create a `tests` directory in the root of your repository.
- Create your test yaml files in the `tests` directory.

## Running pytest-workflow
Run `pytest` from an environment with pytest-workflow installed. 
Pytest will automatically gather files in the `tests` directory starting with 
`test` and ending in `.yaml` or `.yml`. 

The tests are run automatically.

## Writing tests with pytest-workflow

Below is an example of a YAML file that defines a test:
```YAML
- name: Touch a file
  command: touch test.file
  files:
    - path: test.file
```
This will run `touch test.file` and check afterwards if a file with path: 
`test.file` is present. It will also check if the `command` has exited 
with exit code `0`, which is the only default test that is run. Testing 
workflows that exit with another exit code is also possible.

A more advanced example:
```YAML
- name: moo file                     # The name of the workflow (required)
  command: bash moo_workflow.sh      # The command to execute the workflow (required)
  files:                             # A list of files to check (optional)
    - path: "moo.txt"                # File path. (Required for each file)
      contains:                      # A list of strings that should be in the file (optional)
        - "moo"
      must_not_contain:              # A list of strings that should NOT be in the file (optional)
        - "Cock a doodle doo"  
      md5sum: e583af1f8b00b53cda87ae9ead880224   # Md5sum of the file (optional)

- name: simple echo                  # A second workflow. Notice the starting `-` which means 
  command: "echo moo"                # that workflow items are in a list. You can add as much workflows as you want
  files:
    - path: "moo.txt"
      should_exist: false            # Whether a file should be there or not. (optional, if not given defaults to true)
  stdout:                            # Options for testing stdout (optional)
    contains:                        # List of strings which should be in stdout (optional)
      - "moo"
    must_not_contain:                # List of strings that should NOT be in stout (optional)
      - "Cock a doodle doo"

- name: mission impossible           # Also failing workflows can be tested
  command: bash impossible.sh 
  exit_code: 2                       # What the exit code should be (optional, if not given defaults to 0)
  files:
    - path: "fail.log"               # Multiple files can be tested for each workflow
    - path: "TomCruise.txt"
  stderr:                            # Options for testing stderr (optional)
    contains:                        # A list of strings which should be in stderr (optional)
      - "BSOD error, please contact the IT crowd"
    must_not_contain:                # A list of strings which should NOT be in stderr (optional)
      - "Mission accomplished!"
```

The above YAML file contains all the possible options for a workflow test.
