
Working with Semantic Structures
================================

PyDelphin accommodates three kinds of semantic structures:

* :mod:`delphin.mrs` -- Minimal Recursion Semantics
* :mod:`delphin.eds` -- Elementary Dependency Structures
* :mod:`delphin.dmrs` -- Dependency Minimal Recusion Semantics

MRS is the original underspecified representation in DELPH-IN, and is
the only one directly output when parsing with DELPH-IN grammars. In
PyDelphin, all three implement the
:class:`~delphin.sembase.SemanticStructure` interface, while MRS and
DMRS additionally implement the
:class:`~delphin.scope.ScopingSemanticStructure` interface.  Common
properties of :class:`~delphin.sembase.SemanticStructure` include a
notion of the top of the graph and a list of :class:`Predications
<delphin.sembase.Predication>`. The following ASCII-diagram
illustrates the class hierarchy of these representations::

   +----------------------+
   | delphin.lnk.LnkMixin |--------------------------+
   +----------------------+                          |
     |                                               |
     |  +-----------------------------------+        |  +-----------------------------+
     +--| delphin.sembase.SemanticStructure |        +--| delphin.sembase.Predication |
        +-----------------------------------+           +-----------------------------+
          |                                               |
          |  +-----------------+                          |  +------------------+
          +--| delphin.eds.EDS |                          +--| delphin.eds.Node |
          |  +-----------------+                          |  +------------------+
          |                                               |
          |  +----------------------------------------+   |
          +--| delphin.scope.ScopingSemanticStructure |   |
             +----------------------------------------+   |
               |                                          |
               |  +-----------------+                     |  +----------------+
               +--| delphin.mrs.MRS |                     +--| delphin.mrs.EP |
               |  +-----------------+                     |  +----------------+
               |                                          |
               |  +-------------------+                   |  +-------------------+
               +--| delphin.dmrs.DMRS |                   +--| delphin.dmrs.Node |
                  +-------------------+                      +-------------------+


Scoping and Non-scoping Structures
----------------------------------


Well-formed Structures
----------------------

While it is possible to manipulate and create
:class:`~delphin.mrs.MRS`, :class:`~delphin.eds.EDS`, and
:class:`~delphin.dmrs.DMRS` objects, there is no guarantee that these
actions result in a well-formed semantic structure. Well-formedness is
crucial for certain operations, such as realizing sentences with a
grammar or converting between representations.

>>> from delphin import mrs
>>> from delphin.codecs import simplemrs
>>> m = simplemrs.decode('[ TOP: h0 ... ]')
>>> mrs.is_connected(m)
True
>>> mrs.has_intrinsic_variable_property(m)
True
>>> mrs.plausibly_scopes(m)
True
>>> mrs.is_well_formed(m)
True
