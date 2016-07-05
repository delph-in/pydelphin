#!/usr/bin/env python3

import sys
import os
from setuptools import setup
from setuptools.command.test import test as TestCommand

class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ['--doctest-glob=tests/*.md']

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)

class PyTestCoverage(PyTest):
    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = [
            '--doctest-glob=tests/*.md',
            '--cov=delphin',
            '--cov-report=html'
        ]

long_description = '''\
pyDelphin provides a suite of libraries for modeling Minimal Recursion
Semantics (MRS; including DMRS), derivation trees, and [incr tsdb()]
profiles; introspection tools for Type Description Language (TDL),
which is used to define HPSG grammars; a Python wrapper for the ACE
parser; and some extra tools for syntax highlighting or LaTeX output.
Python developers who work with DELPH-IN data can rely on pyDelphin to
correctly deal with such data via convenient interfaces.'''

base_dir = os.path.dirname(__file__)
about = {}
with open(os.path.join(base_dir, "delphin", "__about__.py")) as f:
    exec(f.read(), about)

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
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Linguistic',
        'Topic :: Utilities'
    ],
    keywords='nlp semantics hpsg delph-in',
    packages=[
        'delphin',
        'delphin.lib',
        'delphin.interfaces',
        'delphin.mrs',
        'delphin.extra',
        'delphin.codecs'
    ],
    install_requires=[
        'networkx',
        'requests',
        'Pygments'
    ],
    # entry_points={
    #     'console_scripts': [
    #         'fine=...'
    #     ]
    # }
    tests_require=['pytest>=2.8.0'],
    cmdclass={'test':PyTest, 'coverage':PyTestCoverage}
)
