================
Known issues
================

+ ``pytest-workflow`` does not work well together with ``pytest-cov``. This is
  due to the temporary directory creating nature of ``pytest-workflow``.
  This can be solved by using:

  .. code-block::

    coverage run --source=<your source here> -m py.test <your test dir>

  This will work as expected.