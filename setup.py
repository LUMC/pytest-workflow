#!/usr/bin/env/python3

from setuptools import setup, find_packages


with open("README.md", "r") as readme_file:
    long_description = readme_file.read()

setup(
    name="pytest-workflow",
    version="0.1.0dev",
    description="A pytest plugin for configuring workflow/pipeline tests using YAML files",
    author="Leiden University Medical Center, various departments",
    author_email="sasc@lumc.nl",  # A placeholder for now
    long_description=long_description,
    license="AGPL-3.0-or-later",
    keywords="pytest workflow pipeline yaml yml",
    zip_safe=False,
    packages=find_packages(),
    url="https://github.com/LUMC/pytest-workflow",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Framework :: Pytest",
    ],
    install_requires=[
        "pytest>=4"
    ]
)
