#!/usr/bin/env python3

import os
from setuptools import setup

long_description = '''\
PyDelphin provides a suite of libraries for modeling Minimal Recursion
Semantics (MRS; including EDS and DMRS), [incr tsdb()] profiles and
derivations, the Test Suite Query Language (TSQL), Type Description
Language (TDL), and YY token lattices. In addition, it provides an
implementation of the Regular Expression Preprocessor (REPP) and
Python interfaces for the ACE processor and HTTP API.'''

base_dir = os.path.dirname(__file__)
about = {}
with open(os.path.join(base_dir, "delphin", "__about__.py")) as f:
    exec(f.read(), about)

# thanks: https://snarky.ca/clarifying-pep-518/
docs_require = [
    'sphinx',
    'sphinx-rtd-theme'
]
tests_require = [
    'pytest'
]

setup(
    name=about['__title__'],
    version=about['__version__'],
    description=about['__summary__'],
    long_description=long_description,
    url=about['__uri__'],
    author=about['__author__'],
    author_email=about['__email__'],
    license=about['__license__'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Linguistic',
        'Topic :: Utilities'
    ],
    keywords='nlp semantics hpsg delph-in linguistics',
    packages=[
        'delphin',
        'delphin.lib',
        'delphin.interfaces',
        'delphin.mrs',
        'delphin.extra',
        'delphin.codecs'
    ],
    install_requires=[
        'penman >=0.6.1',
        # networkx 2.2 is not compatible with Python 2.7 (apparently) and 3.5
        'networkx >=2.0,<2.2',
        'requests',
        'Pygments',
    ],
    extras_require={
        'docs': docs_require,
        'tests': tests_require,
        'dev': docs_require + tests_require
    },
    entry_points={
        'console_scripts': [
            'delphin=delphin.main:main'
        ]
    },
)
