
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


Basic Semantic Structures
-------------------------

The basic :class:`~delphin.sembase.SemanticStructure` interface
provides methods for inspecting a structure's predications and
arguments, morphosemantic properties, and quantification
structure. First let's load an MRS to play with:

>>> from delphin.codecs import simplemrs
>>> # Load MRS for "They have enough capital to build a second factory."
>>> # (Tanaka Corpus i-id=30000034)
>>> m = simplemrs.decode('''
...   [ LTOP: h0 INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
...     RELS: < [ pron<0:4> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: pl IND: + PT: std ] ]
...             [ pronoun_q<0:4> LBL: h5 ARG0: x3 RSTR: h6 BODY: h7 ]
...             [ _have_v_1<5:9> LBL: h1 ARG0: e2 ARG1: x3 ARG2: x8 [ x PERS: 3 NUM: sg ] ]
...             [ _enough_q<10:16> LBL: h9 ARG0: x8 RSTR: h10 BODY: h11 ]
...             [ _capital_n_1<17:24> LBL: h12 ARG0: x8 ]
...             [ with_p<25:51> LBL: h12 ARG0: e13 [ e SF: prop ] ARG1: e14 [ e SF: prop-or-ques TENSE: untensed MOOD: indicative PROG: - PERF: - ] ARG2: x8 ]
...             [ _build_v_1<28:33> LBL: h12 ARG0: e14 ARG1: i15 ARG2: x16 [ x PERS: 3 NUM: sg IND: + ] ]
...             [ _a_q<34:35> LBL: h17 ARG0: x16 RSTR: h18 BODY: h19 ]
...             [ ord<36:42> LBL: h20 CARG: "2" ARG0: e22 [ e SF: prop TENSE: untensed MOOD: indicative PROG: bool PERF: - ] ARG1: x16 ]
...             [ _factory_n_1<43:51> LBL: h20 ARG0: x16 ] >
...     HCONS: < h0 qeq h1 h6 qeq h4 h10 qeq h12 h18 qeq h20 >
...     ICONS: < > ]''')

Then the basic structure can be inspected as follows:

>>> m.top
'h0'
>>> len(m.predications)
10

These two attributes are the only two described by the
:class:`~delphin.sembase.SemanticStructure` interface and subclasses
then define additional data structures. For instance,
:class:`~delphin.mrs.MRS` has several additional attributes:

>>> m.index
'e2'
>>> len(m.rels)  # m.rels is equivalent to m.predications
10
>>> len(m.hcons)
4
>>> len(m.icons)
0
>>> list(m.variables)
['e2', 'x3', 'h6', 'h7', 'x8', 'h10', 'h11', 'e13', 'e14', 'i15', 'x16', 'h18', 'h19', 'e22', 'h0', 'h1', 'h4', 'h12', 'h20', 'h5', 'h9', 'h17']

The basic interface for predications is defined by the
:class:`~delphin.sembase.Predication` class:

>>> p = m.predications[2]  # for MRS, same as m.rels[2]
>>> p.id  # see note below
'e2'
>>> p.predicate
'_have_v_1'
>>> p.type
'e'

Note that while EDS and DMRS have unique ids for each node, MRS does
not formally guarantee unique ids for each of its Elementary
Predications, but PyDelphin creates one for each
:class:`~delphin.mrs.EP` in an :class:`~delphin.mrs.MRS`. These ids
are used for some methods on
:class:`~delphin.sembase.SemanticStructure` instances, as exemplified
in a later example.

For MRS, the :class:`~delphin.mrs.EP` subclass is used for
predications, defining some additional attributes:

>>> p.label
'h1'
>>> p.iv  # intrinsic variable
'e2'
>>> p.args
{'ARG0': 'e2', 'ARG1': 'x3', 'ARG2': 'x8'}

:class:`~delphin.sembase.SemanticStructure` also defines methods for
getting at information that may be implemented differently by
subclasses. For instance, :class:`~delphin.mrs.MRS` and
:class:`~delphin.eds.EDS` define arguments (or edges) on their
respective :class:`~delphin.sembase.Predication` objects, while
:class:`~delphin.dmrs.DMRS` lists them separately as
:attr:`~delphin.dmrs.DMRS.links`, but the
:meth:`SemanticStructure.arguments
<delphin.sembase.SemanticStructure.arguments>` method works for all
representations, and returns a dictionary mapping predication ids to
lists of role-argument pairs for all *outgoing* arguments
(:class:`~delphin.mrs.MRS` has ``ARG0`` intrinsic arguments and
``CARG`` constant arguments which are not represented as arguments in
:class:`~delphin.eds.EDS` and :class:`~delphin.dmrs.DMRS`, so these
are accessed separately).

>>> for id, args in m.arguments().items():
...     print(id, args)
... 
x3 []
q3 [('RSTR', 'h6'), ('BODY', 'h7')]
e2 [('ARG1', 'x3'), ('ARG2', 'x8')]
q8 [('RSTR', 'h10'), ('BODY', 'h11')]
x8 []
e13 [('ARG1', 'e14'), ('ARG2', 'x8')]
e14 [('ARG1', 'i15'), ('ARG2', 'x16')]
q16 [('RSTR', 'h18'), ('BODY', 'h19')]
e22 [('ARG1', 'x16')]
x16 []

Testing for and listing quantifiers also happens at the semantic
structure level as it is more reliable than testing individual
predications:

>>> m.is_quantifier('x3')
False
>>> m.is_quantifier('q3')  # use id, not intrinsic variable
True
>>> for p, q in m.quantification_pairs():
...     if q is None:  # unquantified predication
...         print('{}:{} (none)'.format(p.id, p.predicate))
...     else:
...         print('{}:{} ({}:{})'.format(p.id, p.predicate, q.id, q.predicate))
... 
x3:pron (q3:pronoun_q)
e2:_have_v_1 (none)
x8:_capital_n_1 (q8:_enough_q)
e13:with_p (none)
e14:_build_v_1 (none)
e22:ord (none)
x16:_factory_n_1 (q16:_a_q)

Morphosemantic properties can be retrieved by a predication's id:

>>> p = m.predications[2]
>>> m.properties(p.id)
{'SF': 'prop', 'TENSE': 'pres', 'MOOD': 'indicative', 'PROG': '-', 'PERF': '-'}

In :class:`~delphin.mrs.MRS`, they are also available via the
:attr:`~delphin.mrs.MRS.variables` attribute with the intrinsic
variable of an EP:

>>> m.variables[p.iv]
{'SF': 'prop', 'TENSE': 'pres', 'MOOD': 'indicative', 'PROG': '-', 'PERF': '-'}

:class:`~delphin.eds.EDS` and :class:`~delphin.dmrs.DMRS` objects also
implement the same attributes and methods (with their own relevant
additions).

>>> from delphin import eds
>>> e = eds.from_mrs(m)
>>> len(e.predications) == len(e.nodes)
True
>>> e.nodes[2].predicate
'_have_v_1'
>>> for id, args in e.arguments().items():
...     print(id, args)
x3 []
_1 [('BV', 'x3')]
e2 [('ARG1', 'x3'), ('ARG2', 'x8')]
_2 [('BV', 'x8')]
x8 []
e13 [('ARG1', 'e14'), ('ARG2', 'x8')]
e14 [('ARG2', 'x16')]
_3 [('BV', 'x16')]
e22 [('ARG1', 'x16')]
x16 []

Note that there may be some differences in identifier forms or special
role names (``BV`` above for quantifiers).


Scoping Semantic Structures
---------------------------

MRS and DMRS are scoping semantic representations, meaning they encode
the quantifier scope, although they do so rather differently. The
:class:`~delphin.sembase.ScopingSemanticStructure` class normalizes an
interface to the scoping information via some additional methods, such
as for inspecting the labeled scopes:

>>> top, scopes = m.scopes()
>>> top  # the label of the top scope, not the top handle (MRS.top)
'h1'
>>> for label, predications in scopes.items():
...     print(label, [p.predicate for p in predications])
... 
h4 ['pron']
h5 ['pronoun_q']
h1 ['_have_v_1']
h9 ['_enough_q']
h12 ['_capital_n_1', 'with_p', '_build_v_1']
h17 ['_a_q']
h20 ['ord', '_factory_n_1']

The scopal argument structure is also available:

>>> for id, args in m.scopal_arguments().items():
...     print(id, args)
... 
x3 []
q3 [('RSTR', 'qeq', 'h4')]
e2 []
q8 [('RSTR', 'qeq', 'h12')]
x8 []
e13 []
e14 []
q16 [('RSTR', 'qeq', 'h20')]
e22 []
x16 []

Note that unlike :meth:`~delphin.sembase.SemanticStructure.arguments`,
these return triples whose second member is the scopal relationship
between the id and the scope label.

DMRS works similarly:

>>> from delphin import dmrs
>>> d = dmrs.from_mrs(m)
>>> top, scopes = d.scopes()
>>> top
'h2'
>>> for label, predications in scopes.items():
...     print(label, [p.predicate for p in predications])
... 
h0 ['pron']
h1 ['pronoun_q']
h2 ['_have_v_1']
h3 ['_enough_q']
h6 ['_build_v_1', '_capital_n_1', 'with_p']
h7 ['_a_q']
h9 ['_factory_n_1', 'ord']

Because DMRS does not natively have scope labels, they are generated
by :meth:`DMRS.scopes <delphin.dmrs.DMRS.scopes>`. It is thus
recommended to pass these generated scopes to other methods rather
than generating them over again, both for computational efficiency and
consistency:

>>> for id, args in d.scopal_arguments(scopes=scopes).items():
...     print(id, args)
... 
10000 []
10001 [('RSTR', 'qeq', 'h8')]
10002 []
10003 [('RSTR', 'qeq', 'h8')]
10004 []
10005 []
10006 []
10007 [('RSTR', 'qeq', 'h8')]
10008 []
10009 []


Well-formed Structures
----------------------

While it is possible to manipulate and create
:class:`~delphin.mrs.MRS`, :class:`~delphin.eds.EDS`, and
:class:`~delphin.dmrs.DMRS` objects, there is no guarantee that these
actions result in a well-formed semantic structure. Well-formedness is
crucial for certain operations, such as realizing sentences with a
grammar or converting between representations. The :mod:`delphin.mrs`
module has a number of functions for testing various facets of
well-formedness:

>>> mrs.is_connected(m)
True
>>> mrs.has_intrinsic_variable_property(m)
True
>>> mrs.plausibly_scopes(m)
True
>>> mrs.is_well_formed(m)
True
