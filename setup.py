#!/usr/bin/env/python3

from setuptools import setup, find_packages


with open("README.md", "r") as readme_file:
    long_description = readme_file.read()

setup(
    name="pytest-workflow",
    version="0.1.0-dev",
    description="A pytest plugin for configuring workflow/pipeline tests using YAML files",
    author="Leiden University Medical Center, various departments",
    author_email="sasc@lumc.nl",  # A placeholder for now
    long_description=long_description,
    license="AGPL-3.0-or-later",
    keywords="pytest workflow pipeline yaml yml",
    zip_safe=False,
    packages=find_packages('src'),
    package_dir={'': 'src'},
    package_data = {
        'pytest_workflow': ['schema/*.json']
    },
    url="https://github.com/LUMC/pytest-workflow",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Framework :: Pytest",
    ],
    install_requires=[
        "pytest>=4",
        "pyyaml",
        "jsonschema"
    ],
    # This line makes sure the plugin is automatically loaded when it is installed in the
    # same environment as pytest. No need to configure conftest.py to enable this plugin.
    entry_points={"pytest11": ["pytest-workflow = pytest_workflow.plugin"]}
)
