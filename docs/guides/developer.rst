
Developer Guide
===============

This guide is for helping developers of modules in the `delphin`
namespace or developers of PyDelphin itself.

.. contents::
   :local:


PyDelphin Development Philosophy
--------------------------------

PyDelphin aims to be a library that makes it easy for both newcomers
to DELPH-IN and experienced researchers to make use of DELPH-IN
resources. The following are the main priorities for PyDelphin
development:

1. Implementations are correct and grammar-agnostic
2. Public APIs are documented
3. Public APIs are user-friendly
4. Code is tested
5. Code is legible
6. Code is computationally efficient

Note that grammar-agnosticism and correctness are the same point. Some
DELPH-IN technologies were created with only one grammar or tool in
mind, but PyDelphin will, as much as possible, implement structures
and processes that are independent of any one tool or grammar. This
means that PyDelphin implements according to specifications (e.g.,
research papers or wiki specifications), and creates those
specifications if the technology is not sufficiently documented. For
some concrete examples, the wikis for `MRS
<http://moin.delph-in.net/MrsRfc>`_, `TDL
<http://moin.delph-in.net/TdlRfc>`_, `TSQL
<http://moin.delph-in.net/TsqlRfc>`_, and `SEM-I
<http://moin.delph-in.net/SemiRfc>`_ (among others) were created, in
part, to establish the specification for PyDelphin to implement. Much
of the information in those wikis was pieced together from various
places, such as other wikis, Lisp and C code, publications, and actual
examples of the respective technologies. PyDelphin generally should
*not* include novel and experimental techniques or representations
(but it can certainly be *used* to create such things!).

The API documentation of PyDelphin is almost as important as the code
itself. Every class, method, function, attribute, and module that is
exposed to the user should be documented. The APIs should also follow
conventions (such as those set by the `Python Standard Library
<https://docs.python.org/3/library/>`_) to help the APIs stay natural
and intuitive to the user. The API should try to be helpful to the
user while being transparent about what it is doing.

The code of PyDelphin should be unit tested for a variety of expected
(and some unintended) uses. The code should follow `PEP-8
<https://www.python.org/dev/peps/pep-0008/>`_ style guidelines and,
going forward, make use of `PEP-484
<https://www.python.org/dev/peps/pep-0484>`_ type annotations. The
lowest priority (but a priority nonetheless) is for code to be
computationally efficient. Software is more useful when it gives
results quickly, but if users have a real need for efficient code
they may want to look beyond Python.


Creating a New Plugin Module
----------------------------

The ``delphin`` package of PyDelphin is, as of version 1.0.0, a
`namespace package
<https://docs.python.org/3/reference/import.html#namespace-packages>`_,
which means that it is possible to create plugins under the `delphin`
namespace.


Plugin Names
''''''''''''

Plugin modules that define a single module or subpackage should be
named ``delphin.{name}`` (e.g., `delphin.highlight
<https://github.com/delph-in/delphin.highlight>`_). If it includes
more than one module or the plugin name doesn't strictly coincide with
the project name, use ``delphin-{{name}}`` (e.g., `delphin-latex
<https://github.com/delph-in/delphin-latex>`_).


Project Structure
'''''''''''''''''

The general project structure of a plugin module looks like
this:

.. code-block:: bash

   delphin.myplugin
   ├── delphin
   │   └── myplugin.py
   ├── tests
   │   └── test_myplugin.py
   ├── LICENSE
   ├── README.md
   └── setup.py

The important thing to note is that the ``delphin/`` subdirectory does
*not* contain an ``__init__.py`` file. If ``myplugin.py`` needed to be
a package rather than a module, it could be a subdirectory of
``delphin/`` with an ``__init__.py`` file inside of it. Packages and
modules under ``delphin/`` should not conflict with existing names in
PyDelphin.


Plugin Versions
'''''''''''''''

Each module should specify its version. The version should be included
in ``setup.py`` as well as in the module as the `__version__` module
constant.


Creating a New Codec Plugin
---------------------------

Creating serialization codec plugins is the same as for regular
plugins, except that the module should go under
``delphin/codecs/mycodec.py``, and neither ``delphin/`` nor
``delphin/codecs/`` should contain an ``__init__.py``. The project
could be dot-named ``delphin.codecs.{{name}}`` or something more
generic with hyphen (such as the aforementioned `delphin-latex
<https://github.com/delph-in/delphin-latex>`_).

In addition, the module should implement the :doc:`Codec API
<../api/delphin.codecs>`, including the required module constant
`CODEC_INFO`. If the module follows this API, it will be recognized by
PyDelphin and appear in the list of available codecs when running
``delphin convert --list`` (see the :ref:`convert-tutorial` command).


Defining a New Subcommand
-------------------------

Plugins can define subcommands that become available as
:command:`delphin <subcommand>` by creating a module in the
``delphin.cli`` namespace. Normally, the primary code of a plugin goes
in the module of the ``delphin`` namespace and the ``delphin.cli``
module only defines a translation from command-line arguments to
internal function calls.

See :doc:`../api/delphin.cli` for more information about defining such
modules.


Adding New Modules to PyDelphin
-------------------------------

The modules that are included by default with the PyDelphin
distribution should be generally useful and not include experimental
features (see the `PyDelphin Development Philosophy`_). With the
understanding that in research software the line between "established"
and "experimental" can get fuzzy, it might help to ask:

- *does this feature pertain to only one grammar?*
- *was this feature used for a one-off experiment?*

If the answer is *yes* to any of the above, then it might not be
relevant for PyDelphin, but it is possible to create a plugin module,
as described above, and distribute it on `PyPI
<https://pypi.org/>`_. One would only need to ``pip install ...`` to
incorporate the new module into the ``delphin`` namespace.

If in fact users could benefit from including the module with
PyDelphin proper, then one might petition the project maintainer to
include the module in the next release of PyDelphin. In this case,
please file an `issue
<https://github.com/delph-in/pydelphin/issues/new>`_ or `pull request
<https://github.com/delph-in/pydelphin/pull/new>`_ to request the
merge.


Module Dependencies
-------------------

Below is a listing of modules arranged into tiers by their
dependencies. A "tier" is just a grouping here; there is no
corresponding structure in the code except for the imports used in the
modules. Each module within a tier only imports modules from tiers
above it (imported modules, except for Tier 0 ones, are shown in
parentheses after the module name).

It is good for a module to be conservative with its dependencies
(i.e., descend to lower tiers). Module authors may consult this list
to see on which tier their modules would fit.

If someone wants to take over maintainership of a PyDelphin module and
spin it off as a separate repository, then modules without
dependencies are the most eligible. For instance, if someone wants to
take over responsibility for the :mod:`delphin.mrs` module, then they
may want to also include the MRS codecs in their repository, or at
least test the codecs to changes they make.

* Tier 0

  - `delphin.__about__`
  - :mod:`delphin.exceptions`
  - `delphin.util`

* Tier 1

  - :mod:`delphin.derivation`
  - :mod:`delphin.hierarchy`
  - :mod:`delphin.interface` (soft dependencies on `tokens`,
    `derivation`, and `codecs`)
  - :mod:`delphin.lnk`
  - :mod:`delphin.predicate`
  - :mod:`delphin.variable`

* Tier 2

  - :mod:`delphin.ace` [`interface`]
  - :mod:`delphin.itsdb` [`interface`]
  - :mod:`delphin.sembase` [`lnk`]
  - :mod:`delphin.semi` [`hierarchy`, `predicate`]
  - :mod:`delphin.tfs` [`hierarchy`]
  - :mod:`delphin.tokens` [`lnk`]
  - :mod:`delphin.vpm` [`variable`]
  - :mod:`delphin.web.client` [`interface`]

* Tier 3

  - :mod:`delphin.repp` [`lnk`, `tokens`]
  - :mod:`delphin.scope` [`lnk`, `predicate`, `sembase`]
  - :mod:`delphin.tdl` [`tfs`]
  - :mod:`delphin.tsql` [`itsdb`]

* Tier 4

  - :mod:`delphin.dmrs` [`lnk`, `scope`, `sembase`, `variable`]
  - :mod:`delphin.eds` [`lnk`, `scope`, `sembase`, `variable`]
  - :mod:`delphin.mrs` [`lnk`, `predicate`, `scope`, `sembase`, `variable`]

* Tier 5

  - `delphin.codecs` [`dmrs`, `eds`, `mrs`, ...] (see :doc:`../api/delphin.codecs`)
  - :mod:`delphin.web.server` [`ace`, `codecs`, `derivation`, `dmrs`, `eds`, `itsdb`, `tokens`]

* Tier 6

  - :mod:`delphin.commands` [`itsdb`, `lnk`, `semi`, `tsql`, ...]

