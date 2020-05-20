================
Known issues
================

+ ``pytest-workflow`` does not work well together with ``pytest-cov``. This is
  due to the temporary directory creating nature of ``pytest-workflow``.
  This can be solved by using:

  .. code-block:: bash

    coverage run --source=<your_source_here> -m py.test <your_test_dir>

  This will work as expected.

+ ``contains_regex`` and ``must_not_contain_regex`` only work well with single
  quotes in the yaml file. This is due to the way the yaml file is parsed: with
  double quotes, special characters (like ``\t``) will be expanded, which can
  lead to crashes.

+ Special care should be taken when using the backslash character (``\``) in
  ``contains_regex`` and ``must_not_contain_regex``, since this collides with
  Python's usage of the same character to escape special characters in strings.
  Please see the `Python documentation on regular expressions
  <https://docs.python.org/3.6/library/re.html>`_ for details.
