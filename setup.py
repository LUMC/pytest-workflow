# Copyright (C) 2018 Leiden University Medical Center
# This file is part of pytest-workflow
#
# pytest-workflow is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# pytest-workflow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with pytest-workflow.  If not, see <https://www.gnu.org/licenses/

from pathlib import Path

from setuptools import find_packages, setup

setup(
    name="pytest-workflow",
    version="2.1.0",
    description="A pytest plugin for configuring workflow/pipeline tests "
                "using YAML files",
    author="Leiden University Medical Center",
    author_email="sasc@lumc.nl",  # A placeholder for now
    long_description=Path("README.rst").read_text(),
    long_description_content_type="text/x-rst",
    license="AGPL-3.0-or-later",
    keywords="pytest workflow pipeline yaml yml wdl cromwell snakemake",
    zip_safe=False,
    packages=find_packages('src'),
    package_dir={'': 'src'},
    package_data={
        'pytest_workflow': ['schema/*.json']
    },
    url="https://github.com/LUMC/pytest-workflow",
    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: "
        "GNU Affero General Public License v3 or later (AGPLv3+)",
        "Framework :: Pytest",
    ],
    # Because we cannot test anymore on Python 3.8.
    python_requires=">=3.8",
    install_requires=[
        "pytest>=7.0.0",  # To use pathlib Path's in pytest
        "pyyaml",
        "jsonschema",
        "xopen>=1.4.0",
        "zstandard",
    ],
    # This line makes sure the plugin is automatically loaded when it is
    # installed in the same environment as pytest. No need to configure
    # conftest.py to enable this plugin.
    entry_points={"pytest11": ["pytest-workflow = pytest_workflow.plugin"]}
)
