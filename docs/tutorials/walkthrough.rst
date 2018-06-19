
Walkthrough of PyDelphin Features
=================================

This tutorial provides a tour of the main features offered by
PyDelphin.

ACE and HTTP Interfaces
-----------------------

PyDelphin works with a number of data types, and a simple way to get
some data to play with is to parse a sentence. PyDelphin doesn't parse
things on its own, but it provides two interfaces to external
processors: one for the `ACE <http://sweaglesw.org/linguistics/ace/>`_
processor and another for the `HTTP-based "web API"
<http://moin.delph-in.net/ErgApi>`_. I'll first show the web API
as it's the simplest for parsing a single sentence:

>>> from delphin.interfaces import rest
>>> response = rest.parse('Abrams chased Browne', params={'mrs': 'json'})
>>> response.result(0).mrs()
<Mrs object (proper named chase proper named) at 139897112151488>

The response object returned by interfaces is a basic dictionary that
has been augmented with convenient access methods (such as `result()`
and `mrs()` above). Note that the web API is platform-neutral, and is
thus currently the only way to dynamically retrieve parses in PyDelphin
on a Windows machine.

.. seealso::
  - Wiki for the HTTP ("RESTful") API: http://moin.delph-in.net/ErgApi
  - Bottlenose server: https://github.com/delph-in/bottlenose
  - :mod:`delphin.interfaces.rest` module
  - :mod:`delphin.interfaces.ParseResponse` module

If you're on a Linux or Mac machine and have
`ACE <http://sweaglesw.org/linguistics/ace/>`_ installed and a grammar
image available, you can use the ACE interface, which is faster than
the web API and returns more complete response information.

>>> from delphin.interfaces import ace
>>> response = ace.parse('erg-1214-x86-64-0.9.27.dat', 'Abrams chased Browne')
NOTE: parsed 1 / 1 sentences, avg 2135k, time 0.01316s
>>> response.result(0).mrs()
<Mrs object (proper named chase proper named) at 139897048034552>

.. seealso::
  - ACE: http://sweaglesw.org/linguistics/ace/
  - :mod:`delphin.interfaces.ace` module
  - :doc:`ace` tutorial

Tokens and Token Lattices
-------------------------

I will use the `response` object from ACE to illustrate some other
features. First, you can inspect the tokens as analyzed by the
processor.

>>> response.tokens('initial')
<delphin.tokens.YyTokenLattice object at 0x7f3c55abdd30>
>>> print('\n'.join(map(str,response.tokens('initial').tokens)))
(1, 0, 1, <0:6>, 1, "Abrams", 0, "null", "NNP" 1.0000)
(2, 1, 2, <7:13>, 1, "chased", 0, "null", "NNP" 1.0000)
(3, 2, 3, <14:20>, 1, "Browne", 0, "null", "NNP" 1.0000)

.. seealso::
  - Wiki about YY tokens: http://moin.delph-in.net/PetInput
  - :mod:`delphin.tokens` module

Derivations
-----------

[incr tsdb()] derivations (unambiguous "recipes" for an analysis with a
specific grammar version) are fully modeled:

>>> d = response.result(0).derivation()
>>> d.derivation().entity
'sb-hd_mc_c'
>>> d.derivation().daughters
[<UdfNode object (900, hdn_bnp-pn_c, 0.093057, 0, 1) at 139897048235816>, <UdfNode object (904, hd-cmp_u_c, -0.846099, 1, 3) at 139897041227960>]
>>> d.derivation().terminals()
[<UdfTerminal object (abrams) at 139897041154360>, <UdfTerminal object (chased) at 139897041154520>, <UdfTerminal object (browne) at 139897041154680>]
>>> d.derivation().preterminals()
[<UdfNode object (71, abrams, 0.0, 0, 1) at 139897041214040>, <UdfNode object (52, chase_v1, 0.0, 1, 2) at 139897041214376>, <UdfNode object (70, browne, 0.0, 2, 3) at 139897041214712>]

.. seealso::
  - Wiki about derivations: http://moin.delph-in.net/ItsdbDerivations
  - :mod:`delphin.derivation` module

\*MRS Inspection
----------------

The original motivation for PyDelphin and the area with the most work
is in modeling MRS representations.

>>> x = response.result(0).mrs()
>>> [ep.pred.string for ep in x.eps()]
['proper_q', 'named', '_chase_v_1', 'proper_q', 'named']
>>> x.variables()
['h0', 'e2', 'h4', 'x3', 'h5', 'h6', 'h7', 'h1', 'x9', 'h10', 'h11', 'h12', 'h13']
>>> x.nodeid('x3')
10001
>>> x.ep(x.nodeid('x3'))
<ElementaryPredication object (named (x3)) at 140597926475360>
>>> x.ep(x.nodeid('x3', quantifier=True))
<ElementaryPredication object (proper_q (x3)) at 140597926475240>
>>> x.ep(x.nodeid('e2')).args
{'ARG0': 'e2', 'ARG1': 'x3', 'ARG2': 'x9'}
>>> [(hc.hi, hc.relation, hc.lo) for hc in x.hcons()]
[('h0', 'qeq', 'h1'), ('h5', 'qeq', 'h7'), ('h11', 'qeq', 'h13')]

.. seealso::
  - Wiki of MRS topics: http://moin.delph-in.net/RmrsTop
  - :mod:`delphin.mrs.xmrs` module

Beyond the basic modeling of semantic structures, there are a number of
additional functions for analyzing the structures, such as from the
:mod:`delphin.mrs.compare` and :mod:`delphin.mrs.query` modules:

>>> from delphin.mrs import compare
>>> compare.isomorphic(x, x)
True
>>> compare.isomorphic(x, response.result(1).mrs())
False
>>> from delphin.mrs import query
>>> query.select_eps(response.result(1).mrs(), pred='named')
[<ElementaryPredication object (named (x3)) at 140244783534752>, <ElementaryPredication object (named (x9)) at 140244783534272>]
>>> x.args(10000)
{'ARG0': 'x3', 'RSTR': 'h5', 'BODY': 'h6'}
>>> query.find_argument_target(x, 10000, 'RSTR')
10001
>>> for sg in query.find_subgraphs_by_preds(x, ['named', 'proper_q'], connected=True):
...     print(sg.nodeids())
... 
[10000, 10001]
[10003, 10004]


\*MRS Conversion
----------------



- itsdb
- semi
- tdl
- repp
