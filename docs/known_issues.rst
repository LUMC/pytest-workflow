================
Known issues
================

+ ``pytest-workflow`` does not work well together with ``pytest-cov``. This is
  due to the temporary directory creating nature of ``pytest-workflow``.
  This can be solved by using:

  .. code-block:: bash

    coverage run --source=<your_source_here> -m py.test <your_test_dir>

  This will work as expected.