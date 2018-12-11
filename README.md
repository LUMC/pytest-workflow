# pytest-workflow
pytest-workflow is a pytest plugin that aims to make pipeline/workflow testing easy 
by using yaml files for the test configuration.

## Introduction

Writing workflows is hard. Testing if they are correct is even harder. Testing with
bash scripts or other code has some flaws. Is this bug in the pipeline. or in my test-framework?
Pytest-workflow aims to make testing as simple as possible so you can focus on debugging
your pipeline.

## Installation

- make sure your virtual environment is activated
- Install using pip `pip install git+https://github.com/lumc/pytest-workflow.git`
- create a `tests` directory in the root of your repository.
- Create your test yaml files in the test directory

We aim to make pytest-workflow available on PYPI in the future  

## Writing tests with pytest-workflow

Below is an example of a YAML file that defines a test:
```YAML
executable: "touch"
arguments: "test.file"
results:
    files:
      - path: test.file
```

When `pytest` is run the `pytest-workflow` plugin will:
1. Run whatever is in  `command` and capture its stdout and stderr.
2. Test whether the outputs of `command` match with the requirements
in the `results` section.

