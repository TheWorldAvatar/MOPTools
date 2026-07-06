#!/usr/bin/env python3
"""Setup script for MOPTools package."""

from setuptools import setup, find_packages


NOTEBOOK_REQUIREMENTS = [
    "ipykernel",
    "nbformat",
    "kaleido",
    "xyzrender>=0.3.0",
]

DEV_REQUIREMENTS = [
    *NOTEBOOK_REQUIREMENTS,
    "pytest",
    "pytest-cov",
]

# Read requirements from requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Read long description from README
try:
    with open("twa_mops/README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "MOPTools - Tools for working with Metal-Organic Polyhedra"

setup(
    name="twa_mops",
    version="0.1.0",
    description="MOPTools - Tools for working with Metal-Organic Polyhedra",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="TWA Team",
    author_email="info@theworldavatar.com",
    url="https://www.theworldavatar.com",
    package_dir={"": "."},
    packages=find_packages(where=".", include=["twa_mops*"]),
    python_requires=">=3.8, <3.13",
    install_requires=requirements,
    extras_require={
        "notebook": NOTEBOOK_REQUIREMENTS,
        "xyzrender": ["xyzrender>=0.3.0"],
        "dev": DEV_REQUIREMENTS,
        "all": DEV_REQUIREMENTS,
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
