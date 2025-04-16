#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Installation of the movatalk package.
"""

import os
from setuptools import setup, find_packages

# Long description from README.md
try:
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "README.md"), encoding="utf-8") as f:
        LONG_DESCRIPTION = '\n' + f.read()
except FileNotFoundError:
    LONG_DESCRIPTION = ''

# Configuration setup
setup(
    name="movatalk",
    version="0.1.40",
    description="libs for cameramonit, ocr, fin-officer, cfo, and other projects",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author="Tom Sapletta",
    author_email="tom@sapletta.com",
    maintainer="pyfunc developers",
    maintainer_email="info@softreck.dev",
    python_requires=">=3.7",
    url="https://www.pyfunc.com",
    project_urls={
        "Repository": "https://github.com/pyfunc/lib",
        "Changelog": "https://github.com/pyfunc/lib/releases",
        "Wiki": "https://github.com/pyfunc/lib/wiki",
        "Issue Tracker": "https://github.com/pyfunc/lib/issues/new",
    },
    packages=["movatalk", "movatalk.config"],
    package_dir={"": "src"},
    license="Apache-2.0",  # Use simple string format
    license_files=("LICENSE"),  # Empty tuple to explicitly prevent license files
    keywords=["python", "pyfunc", "movatalk", "pyfunc3", "pyfunc"],
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    # Critical fix for the license-file issue:
    # This prevents setuptools from automatically adding a license-file entry
)