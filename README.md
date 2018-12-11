# pytest-workflow
pytest-workflow is a pytest plugin that aims to make pipeline/workflow testing easy 
by using yaml files for the test configuration.

## Introduction

[There are nine million bicycles in Bejing](https://youtu.be/eHQG6-DojVw). 
That's a fact, it's a thing we can't deny, like the fact that the number of workflow
engines is rapidly approaching [the same number](https://github.com/common-workflow-language/common-workflow-language/wiki/Existing-Workflow-systems).
Not to mention all the custom workflows that are scripted in python, bash or another language.

These workflows all still need to be tested in some way or an other. Custom scripts do the job,
but these are not easily ported to other projects, and neither are they very transparant in
what is being tested. There has to be a better way. Enter pytest-workflow.

## Installation

- make sure your virtual environment is activated
- Install using pip `pip install git+https://github.com/lumc/pytest-workflow.git`
- create a `tests` directory in the root of your repository.
- Create your test yaml files in the test directory

We aim to make pytest-workflow available on PYPI in the future  

## Writing tests with pytest-workflow

Below is an example of a YAML file that defines a test:
```YAML
command: "echo test > test.log && echo 'Finished!' "
results:
    files:
      - path: test.log
```

When `pytest` is run the `pytest-workflow` plugin will:
1. Run whatever is in  `command` and capture its stdout and stderr.
2. Test whether the outputs of `command` match with the requirements
in the `results` section.

