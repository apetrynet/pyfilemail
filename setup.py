# -*- coding: utf-8 -*-
from setuptools import setup

import pyfilemail

packages = ['pyfilemail']

requires = [
    'requests',
    'appdirs',
    'keyring
    ]

with open('README') as f:
    long_description = f.read()

setup(
    name='pyfilemail',
    version=pyfilemail.__version__,
    description='Python command line tool and API for file transfers with www.filemail.com',
    long_description=long_description,
    author='Daniel Flehner Heen',
    url='https://github.com/apetrynet/pyfilemail',
    packages=packages,
    package_data={'': ['LICENSE']},
    package_dir={'pyfilemail': 'pyfilemail'},
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
