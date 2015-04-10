#!/usr/bin/env python3

from setuptools import setup

setup(
    name='pyDelphin',
    version='0.2',
    url='https://github.com/goodmami/pydelphin',
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
        'delphin.codecs'
    ],
    install_requires=[
        'networkx',
    ],
    # entry_points={
    #     'console_scripts': [
    #         'fine=...'
    #     ]
    # }
    test_suite='tests'
)
