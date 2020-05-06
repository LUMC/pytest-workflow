============
Installation
============

Pytest-workflow is tested on python 3.6, 3.7 and 3.8. Python 2 is not
supported.

In a virtual environment
------------------------

- Create a new python3 virtual environment.
- Make sure your virtual environment is activated.
- Install using pip ``pip install pytest-workflow``.

On Ubuntu or Debian
-------------------

- This requires the ``python3`` and ``python3-pip`` packages to be installed.
- Installing

  - system-wide: ``sudo python3 -m pip install pytest-workflow``.
  - for your user only (no sudo needed):
    ``python3 -m pip install --user pytest-workflow``
- ``pytest`` can now be run with ``python3 -m pytest``.

.. note::

    Running plain ``pytest`` on Ubuntu or Debian outside of a virtual
    environment will not work with ``pytest-workflow`` because this will start
    the python2 version of ``pytest``. This is because python2 is the default
    python on any distribution released before January 1st 2020.

Conda
-----

Pytest-workflow is also available as a `conda package on conda-forge
<https://anaconda.org/conda-forge/pytest-workflow>`_.
To install with conda:

- `Set up conda to use the conda-forge channel
  <http://conda-forge.org/docs/user/introduction.html#how-can-i-install-packages-from-conda-forge>`_

  - If you want to use pytest-workflow together with bioconda you can follow
    `the instructions here
    <https://bioconda.github.io/index.html#set-up-channels>`_.
- ``conda install pytest-workflow``.
