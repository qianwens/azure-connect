#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from setuptools import setup, find_packages

VERSION = "0.0.1"

CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'Intended Audience :: System Administrators',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'License :: OSI Approved :: MIT License',
]

DEPENDENCIES = []

setup(
    name='connect',
    version=VERSION,
    description='Azure connect extension',
    long_description='Help developer connect Azure services.',
    license='MIT',
    author='Cupertino Team',
    url='https://github.com/VSChina/azure-connect',
    classifiers=CLASSIFIERS,
    packages=find_packages(),
    package_data={'azext_connect': ['azext_metadata.json']},
    install_requires=DEPENDENCIES
)