
Walkthrough of PyDelphin Features
=================================

This guide provides a tour of the main features offered by PyDelphin.


ACE and Web Interfaces
----------------------

PyDelphin works with a number of data types, and a simple way to get
some data to play with is to parse a sentence. PyDelphin doesn't parse
things on its own, but it provides two interfaces to external
processors: one for the `ACE <http://sweaglesw.org/linguistics/ace/>`_
processor and another for the `HTTP-based "Web API"
<http://moin.delph-in.net/ErgApi>`_. I'll first show the Web API
as it's the simplest for parsing a single sentence:

>>> from delphin.web import client
>>> response = client.parse('Abrams chased Browne', params={'mrs': 'json'})
>>> response.result(0).mrs()
<MRS object (proper_q named chase_v_1 proper_q named) at 139897112151488>

The response object returned by interfaces is a basic dictionary that
has been augmented with convenient access methods (such as `result()`
and `mrs()` above). Note that the Web API is platform-neutral, and is
thus currently the only way to dynamically retrieve parses in PyDelphin
on a Windows machine.

.. seealso::
  - Wiki for the Web API: http://moin.delph-in.net/ErgApi
  - Bottlenose server: https://github.com/delph-in/bottlenose
  - :mod:`delphin.web` module
  - :mod:`delphin.interface` module

If you're on a Linux or Mac machine and have
`ACE <http://sweaglesw.org/linguistics/ace/>`_ installed and a grammar
image available, you can use the ACE interface, which is faster than
the Web API and returns more complete response information.

>>> from delphin import ace
>>> grm = '~/grammars/erg-2018-x86-64-0.9.30.dat'
>>> response = ace.parse(grm, 'Abrams chased Browne')
NOTE: parsed 1 / 1 sentences, avg 2135k, time 0.01316s
>>> response.result(0).mrs()
<MRS object (proper_q named chase_v_1 proper_q named) at 139897048034552>

.. seealso::
  - ACE: http://sweaglesw.org/linguistics/ace/
  - :mod:`delphin.ace` module
  - :doc:`ace`

I will use the `response` object from ACE to illustrate some other
features below.


Inspecting Semantic Structures
------------------------------

The original motivation for PyDelphin and the area with the most work
is in modeling DELPH-IN Semantics representations such as MRS.

>>> m = response.result(0).mrs()
>>> [ep.predicate for ep in m.rels]
['proper_q', 'named', '_chase_v_1', 'proper_q', 'named']
>>> list(m.variables)
['h0', 'e2', 'h4', 'x3', 'h5', 'h6', 'h7', 'h1', 'x9', 'h10', 'h11', 'h12', 'h13']
>>> # get an EP by its ID (generally its intrinsic variable)
>>> m['x3']
<EP object (h7:named(CARG Abrams, ARG0 x3)) at 140709661206856>
>>> # quantifier IDs generally just replace 'x' with 'q'
>>> m['q3']
<EP object (h4:proper_q(ARG0 x3, RSTR h5, BODY h6)) at 140709661206760>
>>> # but if you want to be more careful you can do this...
>>> qmap = {p.iv: q for p, q in m.quantification_pairs()}
>>> qmap['x3']
<EP object (h4:proper_q(ARG0 x3, RSTR h5, BODY h6)) at 140709661206760>
>>> # EP arguments are available on the EPs
>>> m['e2'].args
{'ARG0': 'e2', 'ARG1': 'x3', 'ARG2': 'x9'}
>>> # While HCONS are available on the MRS
>>> [(hc.hi, hc.relation, hc.lo) for hc in m.hcons]
[('h0', 'qeq', 'h1'), ('h5', 'qeq', 'h7'), ('h11', 'qeq', 'h13')]

.. seealso::
  - Wiki of MRS topics: http://moin.delph-in.net/RmrsTop
  - :mod:`delphin.mrs` module
  - :doc:`semantics`

Beyond the basic modeling of semantic structures, there are some
semantic operations defined in the :mod:`delphin.mrs` module.

>>> from delphin import mrs
>>> mrs.is_isomorphic(m, m)
True
>>> mrs.is_isomorphic(m, response.result(1).mrs())
False
>>> mrs.has_intrinsic_variable_property(m)
True
>>> mrs.is_connected(m)
True

.. seealso::
  - MRS isomorphism wiki: http://moin.delph-in.net/MrsIsomorphism

Scoping semantic structures such as MRS and DMRS can make use of the
:mod:`delphin.scope` module, which allows for inspection of the scope
structures:

>>> from delphin import scope
>>> _response = ace.parse(grm, "Kim didn't think that Sandy left.")
>>> descendants = scope.descendants(_response.result(0).mrs())
>>> for id, ds in descendants.items():
...     print(m[id].predicate, [d.predicate for d in ds])
... 
proper_q ['named']
named []
neg ['_think_v_1', '_leave_v_1']
_think_v_1 ['_leave_v_1']
_leave_v_1 []
proper_q ['named']
named []

.. seealso::
  - :mod:`delphin.scope` module


Converting Semantic Representations
-----------------------------------

Conversions between MRS, DMRS, and EDS representations are a single
function call in PyDelphin. The converted representation has its own
data structures so it can be inspected and manipulated in a natural
way for the respective formalism. Here is DMRS conversion from MRS:

>>> from delphin import dmrs
>>> dmrs.from_mrs(m)
<DMRS object (proper_q named _chase_v_1 proper_q named) at 140709655360704>

And EDS conversion from MRS:

>>> from delphin import eds
>>> eds.from_mrs(m)
<EDS object (proper_q named _chase_v_1 proper_q named) at 140709655349560>

It is also possible to convert to MRS from DMRS.


Serializing Semantic Representations
------------------------------------

The DELPH-IN community has designed many serialization formats of the
semantic representations for various uses. For instance, the JSON
formats are used in the Web API, and the PENMAN formats are sometimes
used in machine learning applications. PyDelphin implements almost all
of these formats, available in the :doc:`../api/delphin.codecs`
namespace.

>>> from delphin.codecs import simplemrs, mrx
>>> print(simplemrs.encode(m, indent=True))
[ TOP: h0
  INDEX: e2 [ e SF: prop TENSE: past MOOD: indicative PROG: - PERF: - ]
  RELS: < [ proper_q<0:6> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: sg IND: + ] RSTR: h5 BODY: h6 ]
          [ named<0:6> LBL: h7 ARG0: x3 CARG: "Abrams" ]
          [ _chase_v_1<7:13> LBL: h1 ARG0: e2 ARG1: x3 ARG2: x9 [ x PERS: 3 NUM: sg IND: + ] ]
          [ proper_q<14:20> LBL: h10 ARG0: x9 RSTR: h11 BODY: h12 ]
          [ named<14:20> LBL: h13 ARG0: x9 CARG: "Browne" ] >
  HCONS: < h0 qeq h1 h5 qeq h7 h11 qeq h13 > ]
>>> print(mrx.encode(m, indent=True))
<mrs cfrom="-1" cto="-1"><label vid="0" /><var sort="e" vid="2">
[...]
</mrs>

To serialize a different representation you must convert it first:

>>> d = dmrs.from_mrs(m)
>>> from delphin.codecs import dmrx
>>> print(dmrx.encode(d, indent=True))
<dmrs cfrom="-1" cto="-1" index="10002">
[...]
</dmrs>
>>> e = eds.from_mrs(m)
>>> from delphin.codecs import eds as edsnative  # avoid name collision
>>> print(edsnative.encode(e, indent=True))
{e2:
 _1:proper_q<0:6>[BV x3]
 x3:named<0:6>("Abrams")[]
 e2:_chase_v_1<7:13>[ARG1 x3, ARG2 x9]
 _2:proper_q<14:20>[BV x9]
 x9:named<14:20>("Browne")[]
}


.. seealso::
  - Wiki of MRS formats: http://moin.delph-in.net/MrsRfc
  - :doc:`../api/delphin.codecs` namespace

Some formats are currently export-only:

>>> from delphin.codecs import mrsprolog
>>> print(mrsprolog.encode(m, indent=True))
psoa(h0,e2,
  [rel('proper_q',h4,
       [attrval('ARG0',x3),
        attrval('RSTR',h5),
        attrval('BODY',h6)]),
   rel('named',h7,
       [attrval('CARG','Abrams'),
        attrval('ARG0',x3)]),
   rel('_chase_v_1',h1,
       [attrval('ARG0',e2),
        attrval('ARG1',x3),
        attrval('ARG2',x9)]),
   rel('proper_q',h10,
       [attrval('ARG0',x9),
        attrval('RSTR',h11),
        attrval('BODY',h12)]),
   rel('named',h13,
       [attrval('CARG','Browne'),
        attrval('ARG0',x9)])],
  hcons([qeq(h0,h1),qeq(h5,h7),qeq(h11,h13)]))


Tokens and Token Lattices
-------------------------

The Response object from the interface can return both the initial
(string-level tokenization) and internal (token-mapped) tokens:

>>> response.tokens('initial')
<delphin.tokens.YYTokenLattice object at 0x7f3c55abdd30>
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
[<UDFNode object (900, hdn_bnp-pn_c, 0.093057, 0, 1) at 139897048235816>, <UDFNode object (904, hd-cmp_u_c, -0.846099, 1, 3) at 139897041227960>]
>>> d.derivation().terminals()
[<UDFTerminal object (abrams) at 139897041154360>, <UDFTerminal object (chased) at 139897041154520>, <UDFTerminal object (browne) at 139897041154680>]
>>> d.derivation().preterminals()
[<UDFNode object (71, abrams, 0.0, 0, 1) at 139897041214040>, <UDFNode object (52, chase_v1, 0.0, 1, 2) at 139897041214376>, <UDFNode object (70, browne, 0.0, 2, 3) at 139897041214712>]

.. seealso::
  - Wiki about derivations: http://moin.delph-in.net/ItsdbDerivations
  - :mod:`delphin.derivation` module


[incr tsdb()] TestSuites
------------------------

PyDelphin has full support for reading and writing [incr tsdb()]
testsuites:

>>> from delphin import itsdb
>>> ts = itsdb.TestSuite('~/grammars/erg/tsdb/gold/mrs')
>>> len(ts['item'])
107
>>> ts['item'][0]['i-input']
'It rained.'
>>> # modify a test suite in-memory
>>> ts['item'].update(0, {'i-input': 'It snowed.'})
>>> ts['item'][0]['i-input']
'It snowed.'
>>> # TestSuite.commit() writes changes to disk
>>> ts.commit()
>>> # TestSuites can be parsed with a processor like ACE
>>> from delphin import ace
>>> with ace.ACEParser('~/grammars/erg-2018-x86-64-0.9.30.dat') as cpu:
...     ts.process(cpu)
... 
NOTE: parsed 107 / 107 sentences, avg 4744k, time 2.93924s

.. seealso::
  - [incr tsdb()] wiki: http://moin.delph-in.net/ItsdbTop
  - :mod:`delphin.itsdb` module
  - :mod:`delphin.tsdb` module, for a low-level API
  - :doc:`itsdb`


TSQL Queries
------------

Partial support of the Test Suite Query Language (TSQL) allows for
easy selection of [incr tsdb()] test suite data.

>>> from delphin import tsql
>>> selection = tsql.select('i-id i-input where i-length > 5 && readings > 0', ts)
>>> next(iter(selection))
(61, 'Abrams handed the cigarette to Browne.')

.. seealso::
  - TSQL documentation: http://www.delph-in.net/tsnlp/ftp/manual/volume2.ps.gz
  - :mod:`delphin.tsql` module


Regular Expression Preprocessors (REPP)
---------------------------------------

PyDelphin provides a full implementation of Regular Expression
Preprocessors (REPP), including correct characterization and the
loading from `PET <http://moin.delph-in.net/PetTop>`_ configuration
files. Unique to PyDelphin (I think) is the ability to trace through
an application of the tokenization rules.

>>> from delphin import repp
>>> r = repp.REPP.from_config('~/grammars/erg/pet/repp.set')
>>> for tok in r.tokenize("Abrams didn't chase Browne.").tokens:
...     print(tok.form, tok.lnk)
... 
Abrams <0:6>
did <7:10>
n’t <10:13>
chase <14:19>
Browne <20:26>
. <26:27>
>>> for step in r.trace("Abrams didn't chase Browne."):
...     if isinstance(step, repp.REPPStep):
...         print('{}\t-> {}\t{}'.format(step.input, step.output, step.operation))
... 
Abrams didn't chase Browne.	->  Abrams didn't chase Browne. 	!^(.+)$		 \1 
 Abrams didn't chase Browne. 	->  Abrams didn’t chase Browne. 	!'		’
 Abrams didn't chase Browne. 	->  Abrams didn’t chase Browne. 	Internal group #1
 Abrams didn't chase Browne. 	->  Abrams didn’t chase Browne. 	Internal group #1
 Abrams didn't chase Browne. 	->  Abrams didn’t chase Browne. 	Module quotes
 Abrams didn’t chase Browne. 	->   Abrams didn’t chase Browne.  	!^(.+)$		 \1 
  Abrams didn’t chase Browne.  	->  Abrams didn’t chase Browne. 	!  +		 
 Abrams didn’t chase Browne. 	->  Abrams didn’t chase Browne . 	!([^ ])(\.) ([])}”"’'… ]*)$		\1 \2 \3
 Abrams didn’t chase Browne. 	->  Abrams didn’t chase Browne . 	Internal group #1
 Abrams didn’t chase Browne. 	->  Abrams didn’t chase Browne . 	Internal group #1
 Abrams didn’t chase Browne . 	->  Abrams did n’t chase Browne . 	!([^ ])([nN])[’']([tT]) 		\1 \2’\3 
Abrams didn't chase Browne.	->  Abrams did n’t chase Browne . 	Module tokenizer

Note that the trace shows the sequential order of rule applications,
but not the tree-like branching of REPP modules.

.. seealso::
  - REPP wiki: http://moin.delph-in.net/ReppTop
  - Wiki for PET's REPP configuration: http://moin.delph-in.net/ReppPet
  - :mod:`delphin.repp` module


Type Description Language (TDL)
-------------------------------

The TDL language is fairly simple, but the interpretation of type
hierarchies (feature inheritance, re-entrancies, unification and
subsumption) can be very complex. PyDelphin has partial support for
reading TDL files. It can read nearly any kind of TDL in a DELPH-IN
grammar (type definitions, lexicons, transfer rules, etc.), but it does
not do any interpretation. It can be useful for static code analysis.

>>> from delphin import tdl
>>> lex = {}
>>> for event, obj, lineno in tdl.iterparse('~/grammars/erg/lexicon.tdl'):
...     if event == 'TypeDefinition':
...         lex[obj.identifier] = obj
... 
>>> len(lex)
40234
>>> lex['cactus_n1']
<TypeDefinition object 'cactus_n1' at 140226925196400>
>>> lex['cactus_n1'].supertypes
[<TypeIdentifier object (n_-_c_le) at 140226925284232>]
>>> lex['cactus_n1'].features()
[('ORTH', <ConsList object at 140226925534472>), ('SYNSEM', <AVM object at 140226925299464>)]
>>> lex['cactus_n1']['ORTH'].features()
[('FIRST', <String object (cactus) at 140226925284352>), ('REST', None)]
>>> lex['cactus_n1']['ORTH'].values()
[<String object (cactus) at 140226925284352>]
>>> lex['cactus_n1']['ORTH.FIRST']
<String object (cactus) at 140226925284352>
>>> print(tdl.format(lex['cactus_n1']))
cactus_n1 := n_-_c_le &
  [ ORTH < "cactus" >,
    SYNSEM [ LKEYS.KEYREL.PRED "_cactus_n_1_rel",
             LOCAL.AGR.PNG png-irreg,
             PHON.ONSET con ] ].

.. seealso::
  - A semi-formal specification of TDL: http://moin.delph-in.net/TdlRfc
  - A grammar-engineering FAQ about TDL: http://moin.delph-in.net/GeFaqTdlSyntax
  - :mod:`delphin.tdl` module


Semantic Interfaces (SEM-I)
---------------------------

A grammar's semantic model is encoded in the predicate inventory and
constraints of the grammar, but as the interpretation of a grammar is
non-trivial (see `Type Description Language (TDL)`_ above), using the
grammar to validate semantic representations is a significant burden. A
semantic interface (SEM-I) is a distilled and simplified representation
of a grammar's semantic model, and is thus a useful way to ensure that
grammar-external semantic representations are valid with respect to the
grammar. PyDelphin supports the reading and inspection of SEM-Is.

>>> from delphin import semi
>>> s = semi.load('~/grammars/erg/etc/erg.smi')
>>> list(s.variables)
['u', 'i', 'p', 'h', 'e', 'x']
>>> list(s.roles)
['ARG0', 'ARG1', 'ARG2', 'ARG3', 'ARG4', 'ARG', 'RSTR', 'BODY', 'CARG']
>>> s.roles['ARG2']
'u'
>>> list(s.properties)
['bool', 'tense', 'mood', 'gender', 'number', 'person', 'pt', 'sf', '+', '-', 'tensed', 'untensed', 'subjunctive', 'indicative', 'm-or-f', 'n', 'sg', 'pl', '1', '2', '3', 'refl', 'std', 'zero', 'prop-or-ques', 'comm', 'past', 'pres', 'fut', 'm', 'f', 'prop', 'ques']
>>> s.properties.children('tense')
{'untensed', 'tensed'}
>>> s.properties.descendants('tense')
{'past', 'untensed', 'tensed', 'fut', 'pres'}
>>> len(s.predicates)
23403
>>> s.predicates['_cactus_n_1']
[Synopsis([SynopsisRole(ARG0, x, {'IND': '+'}, False)])]
>>> s.predicates.descendants('some_q')
{'_what+a_q', '_some_q_indiv', '_an+additional_q', '_another_q', '_many+a_q', '_a_q', '_some_q', '_such+a_q'}

.. seealso::
  - The SEM-I wikis:

    - http://moin.delph-in.net/SemiRfc
    - http://moin.delph-in.net/RmrsSemi

  - :mod:`delphin.semi` module
