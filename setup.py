#!/usr/bin/env python3

import os
from setuptools import setup

base_dir = os.path.dirname(__file__)
about = {}
with open(os.path.join(base_dir, "delphin", "__about__.py")) as f:
    exec(f.read(), about)

with open(os.path.join(base_dir, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

repp_requires = ['regex==2020.1.8']
web_requires = ['requests==2.22.0', 'falcon==2.0.0']

# thanks: https://snarky.ca/clarifying-pep-518/
doc_requirements = os.path.join(base_dir, 'docs', 'requirements.txt')
if os.path.isfile(doc_requirements):
    with open(doc_requirements) as f:
        docs_require = f.readlines()
else:
    docs_require = []

tests_require = repp_requires + web_requires + [
    'pytest',
    'flake8',
    'mypy',
    'types-requests',
]

setup(
    name=about['__title__'],
    version=about['__version__'],
    description=about['__summary__'],
    long_description=long_description,
    long_description_content_type='text/markdown',
    url=about['__uri__'],
    author=about['__author__'],
    author_email=about['__email__'],
    license=about['__license__'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Linguistic',
        'Topic :: Utilities'
    ],
    keywords='nlp semantics hpsg delph-in linguistics',
    packages=[
        'delphin',
        'delphin.cli',
        'delphin.codecs',
        'delphin.mrs',
        'delphin.eds',
        'delphin.dmrs',
        'delphin.web',
    ],
    install_requires=[
        'penman==1.1.0',
        'progress==1.5',
    ],
    extras_require={
        'docs': docs_require,
        'tests': tests_require,
        'dev': docs_require + tests_require + [
            # https://packaging.python.org/guides/making-a-pypi-friendly-readme
            'setuptools >= 38.6.0',
            'wheel >= 0.31.0',
            'twine >= 1.11.0'
        ],
        'web': web_requires,
        'repp': repp_requires,
    },
    entry_points={
        'console_scripts': [
            'delphin=delphin.main:main'
        ],
    },
)
