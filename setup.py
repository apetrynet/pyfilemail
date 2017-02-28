# -*- coding: utf-8 -*-
from setuptools import setup

import pyfilemail

dependencies = [
    'requests',
    'requests_toolbelt',
    'appdirs',
    'keyring',
    'clint'
    ]

with open('README.rst') as f:
    long_description = f.read()

version = pyfilemail.__version__

setup(
    name='pyfilemail',
    version=version,
    description='Python command line tool and API for \
file transfers with www.filemail.com',
    long_description=long_description,
    author='Daniel Flehner Heen',
    url='https://github.com/apetrynet/pyfilemail',
    download_url='https://github.com/apetrynet/pyfilemail/tarball/' + version,
    packages=['pyfilemail'],
    package_data={'': ['LICENSE.txt']},
    package_dir={'pyfilemail': 'pyfilemail'},
    license='MIT',
    install_requires=dependencies,
    entry_points={
        'console_scripts': [
            'pyfilemail=pyfilemail.__main__:main',
            ],
        },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7'
        ],
    keywords=[
        'filemail',
        'pyfilemail',
        'file transfer',
        'large file transfer',
        'fast transfer',
        'transfer',
        'fast'],
)
