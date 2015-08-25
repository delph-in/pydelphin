#!/usr/bin/env python3

import sys
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


setup(
    name='pyDelphin',
    version='0.3',
    url='https://github.com/delph-in/pydelphin',
    author='Michael Wayne Goodman',
    author_email='goodman.m.w@gmail.com',
    description='Libraries and scripts for DELPH-IN data.',
    license='MIT',
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
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Linguistic',
        'Topic :: Utilities'
    ],
    keywords='nlp semantics hpsg delph-in',
    packages=[
        'delphin',
        'delphin.interfaces',
        'delphin.mrs',
        'delphin.extra',
        'delphin.codecs',
    ],
    install_requires=[
        'networkx',
        'Pygments'
    ],
    # entry_points={
    #     'console_scripts': [
    #         'fine=...'
    #     ]
    # }
    tests_require=['pytest'],
    cmdclass={'test':PyTest, 'coverage':PyTestCoverage}
)
