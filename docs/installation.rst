============
Installation
============

Pytest-workflow is tested on python 3.5, 3.6 and 3.7. Python 2 is not supported.

In a virtual environment:

- Create a new python3 virtual environment.
- Make sure your virtual environment is activated.
- Install using pip ``pip install pytest-workflow``

On Ubuntu or Debian:

- This requires the ``python3`` and ``python3-pip`` packages to be installed.
- Installing

  - system-wide: ``sudo python3 -m pip install pytest-workflow``
  - for your user only (no sudo needed):
    ``python3 -m pip install --user pytest-workflow``
- ``pytest`` can now be run with ``python3 -m pytest``.

.. container:: note

    NOTE: Running plain ``pytest`` on Ubuntu or Debian outside of a virtual
    environment will not work with ``pytest-workflow`` because this will start
    the python2 version of ``pytest``. This is because python2 is the default
    python on any distribution released before January 1st 2020.
