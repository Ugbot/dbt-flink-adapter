#!/usr/bin/env python
import os
import sys
import re

# require python 3.9 or newer (aligned with dbt-core 1.8-1.10 requirements)
# targeting Python 3.12+ for optimal compatibility
if sys.version_info < (3, 9):
    print("Error: dbt-flink-adapter requires Python 3.9 or higher.")
    print("Please upgrade to Python 3.9 or higher.")
    print("Note: Python 3.12+ recommended. Python 3.13 is experimental.")
    sys.exit(1)


# require version of setuptools that supports find_namespace_packages
from setuptools import setup

try:
    from setuptools import find_namespace_packages
except ImportError:
    # the user has a downlevel version of setuptools.
    print("Error: dbt requires setuptools v40.1.0 or higher.")
    print('Please upgrade setuptools with "pip install --upgrade setuptools" ' "and try again")
    sys.exit(1)


# pull long description from README
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md")) as f:
    long_description = f.read()


# get this package's version from dbt/adapters/<name>/__version__.py
def _get_plugin_version_dict():
    _version_path = os.path.join(this_directory, "dbt", "adapters", "flink", "__version__.py")
    _semver = r"""(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"""
    _pre = r"""((?P<prekind>a|b|rc)(?P<pre>\d+))?"""
    _version_pattern = rf"""version\s*=\s*["']{_semver}{_pre}["']"""
    with open(_version_path) as f:
        match = re.search(_version_pattern, f.read().strip())
        if match is None:
            raise ValueError(f"invalid version at {_version_path}")
        return match.groupdict()


# require a compatible minor version (~=), prerelease if this is a prerelease
def _get_dbt_core_version():
    parts = _get_plugin_version_dict()
    minor = "{major}.{minor}.0".format(**parts)
    pre = parts["prekind"] + "1" if parts["prekind"] else ""
    return f"{minor}{pre}"


package_name = "dbt-flink-adapter"
package_version = "1.8.0"
# make sure this always matches dbt/adapters/{adapter}/__version__.py
dbt_core_version = _get_dbt_core_version()
description = """The Flink adapter plugin for dbt"""

setup(
    name=package_name,
    version=package_version,
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="GetInData",
    author_email="office@getindata.com",
    url="https://github.com/getindata/dbt-flink-adapter",
    packages=find_namespace_packages(include=["dbt", "dbt.*"]),
    include_package_data=True,
    install_requires=[
        "dbt-adapters>=1.0.0,<2.0.0",
        "dbt-common>=1.0.0,<2.0.0",
        "dbt-core>=1.8.0",
        "flink-gateway>=0.1.0",
    ],
    extras_require={
        "ververica-tests": [
            "python-dotenv>=1.0.0",
            "pydantic-settings>=2.1.0",
            "pytest-asyncio>=0.21.0",
            "httpx>=0.27.0",
        ],
        "e2e-tests": [
            "podman>=5.0.0",
            "docker>=7.0.0",
            "psycopg2-binary>=2.9",
            "aiokafka>=0.10.0",
            "requests>=2.28",
        ],
    },
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.9",
)
