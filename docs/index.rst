.. PyDelphin documentation master file, created by
   sphinx-quickstart on Mon Jun 11 22:08:46 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

PyDelphin
=========

.. sidebar:: Quick Links

  - `Project page <https://github.com/delph-in/pydelphin>`_
  - `How to contribute <https://github.com/delph-in/pydelphin/blob/develop/CONTRIBUTING.md>`_
  - `Report a bug <https://github.com/delph-in/pydelphin/issues>`_
  - `Changelog <https://github.com/delph-in/pydelphin/blob/develop/CHANGELOG.md>`_
  - `Code of conduct <https://github.com/delph-in/pydelphin/blob/develop/CODE_OF_CONDUCT.md>`_
  - `License (MIT) <https://github.com/delph-in/pydelphin/blob/develop/LICENSE>`_

.. toctree::
  :maxdepth: 1
  :caption: Guides:

  guides/setup.rst
  guides/walkthrough.rst
  guides/semantics.rst
  guides/ace.rst
  guides/commands.rst
  guides/itsdb.rst
  guides/developer.rst

.. toctree::
  :maxdepth: 1
  :caption: API Reference:
  :hidden:

  api/delphin.ace.rst
  api/delphin.cli.rst
  api/delphin.codecs.rst
  api/delphin.commands.rst
  api/delphin.derivation.rst
  api/delphin.dmrs.rst
  api/delphin.eds.rst
  api/delphin.exceptions.rst
  api/delphin.hierarchy.rst
  api/delphin.interface.rst
  api/delphin.itsdb.rst
  api/delphin.lnk.rst
  api/delphin.predicate.rst
  api/delphin.mrs.rst
  api/delphin.repp.rst
  api/delphin.sembase.rst
  api/delphin.scope.rst
  api/delphin.semi.rst
  api/delphin.tdl.rst
  api/delphin.tfs.rst
  api/delphin.tokens.rst
  api/delphin.tsdb.rst
  api/delphin.tsql.rst
  api/delphin.variable.rst
  api/delphin.vpm.rst
  api/delphin.web.rst

API Reference:
--------------

Core API
''''''''

- :doc:`api/delphin.exceptions`
- :doc:`api/delphin.hierarchy` -- Multiple-inheritance hierarchies
- :doc:`api/delphin.codecs` -- Serialization codecs
- :doc:`api/delphin.commands`


Interfacing External Tools
''''''''''''''''''''''''''

- :doc:`api/delphin.interface`
- :doc:`api/delphin.ace` -- ACE
- :doc:`api/delphin.web` -- DELPH-IN Web API

Tokenization
''''''''''''

- :doc:`api/delphin.lnk` -- Surface alignment
- :doc:`api/delphin.repp` -- Regular Expression Preprocessor
- :doc:`api/delphin.tokens` -- YY token lattices

Syntax
''''''

- :doc:`api/delphin.derivation` -- UDF/UDX derivation trees

Semantics
'''''''''

- :doc:`api/delphin.dmrs` -- Dependency Minimal Recursion Semantics
- :doc:`api/delphin.eds` -- Elementary Dependency Structures
- :doc:`api/delphin.predicate` -- Semantic predicates
- :doc:`api/delphin.mrs` -- Minimal Recursion Semantics
- :doc:`api/delphin.sembase`
- :doc:`api/delphin.semi` -- Semantic Interface (or model)
- :doc:`api/delphin.scope` -- Scope operations
- :doc:`api/delphin.variable`
- :doc:`api/delphin.vpm` -- Variable property mapping

Test Suites
'''''''''''

- :doc:`api/delphin.itsdb` -- [incr tsdb()]
- :doc:`api/delphin.tsdb` -- Test Suite Database
- :doc:`api/delphin.tsql` -- Test Suite Query Language


Grammars
''''''''

- :doc:`api/delphin.tdl` -- Type Description Language
- :doc:`api/delphin.tfs` -- Typed feature structures



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

