# Enabling 'pytester' plugin which was written to help testing pytest plugins.
# Disable pylint invalid name checking for pytest  specific name
pytest_plugins = ["pytester"]  # pylint: disable=invalid-name
