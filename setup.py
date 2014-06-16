# -*- coding: utf-8 -*-
from setuptools import setup

import filemail

packages = []

requires = [
    'requests'
    ]

with open('README') as f:
    long_description = f.read()

setup(
    name='filemail',
    version=filemail.__verison__,
    description='Python API for file transfers with www.filemail.com',
    long_description=long_description,
    author='Daniel Flehner Heen',
    url='https://github.com/apetrynet/filemail',
    packages=packages,
    package_data={'': ['LICENSE']},
    package_dir={'filemail': 'filemail'},
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7'
        ],
    keywords='large files transfer',
)