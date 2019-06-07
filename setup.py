#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""setup.py

Distribution setup

(c) The James Hutton Institute 2017-2019

Author: Leighton Pritchard
Contact: leighton.pritchard@hutton.ac.uk

Leighton Pritchard,
Information and Computing Sciences,
James Hutton Institute,
Errol Road,
Invergowrie,
Dundee,
DD6 9LH,
Scotland,
UK

The MIT License

Copyright (c) 2017-2019 The James Hutton Institute

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import os
import sys
import re
import setuptools

try:
    import distribute_setup

    distribute_setup.use_setuptools()
except ImportError:
    pass

# Get long description from README.md
with open("README.md", "r") as dfh:
    long_description = dfh.read()  # pylint: disable=C0103

# parse version from package/module without importing or
# evaluating the code
with open("pyani/__init__.py") as fh:
    for line in fh:
        m = re.search(r"^__version__ = '(?P<version>[^']+)'$", line)
        if m:
            version = m.group("version")
            break

if sys.version_info <= (3, 0):
    sys.stderr.write("ERROR: pyani requires Python 3 " + "or above...exiting.\n")
    sys.exit(1)

setuptools.setup(
    name="pyani",
    version=version,
    author="Leighton Pritchard",
    author_email="leighton.pritchard@hutton.ac.uk",
    description="".join(
        [
            (
                "pyani provides a package and script for calculation of "
                "genome-scale average nucleotide identity."
            )
        ]
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    keywords="genome bioinformatics sequence taxonomy",
    platforms="Posix; MacOS X",
    url="http://widdowquinn.github.io/pyani/",  # project home page
    download_url="https://github.com/widdowquinn/pyani/releases",
    scripts=[
        os.path.join("bin", "average_nucleotide_identity.py"),
        os.path.join("bin", "delta_filter_wrapper.py"),
        os.path.join("bin", "genbank_get_genomes_by_taxon.py"),
    ],
    entry_points={"console_scripts": ["pyani = pyani.scripts.pyani_script:run_main"]},
    packages=setuptools.find_packages(),
    package_data={"pyani": ["tests/test_JSpecies/*.tab"]},
    include_package_date=True,
    install_requires=[
        "biopython",
        "matplotlib",
        "namedlist",
        "networkx",
        "pandas",
        "scipy",
        "seaborn",
        "tqdm",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
)
