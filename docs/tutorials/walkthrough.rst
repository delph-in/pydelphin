
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

I will use the `response` object from ACE to illustrate some other
features below.


\*MRS Inspection
----------------

The original motivation for PyDelphin and the area with the most work
is in modeling MRS representations.

>>> x = response.result(0).mrs()
>>> [ep.pred for ep in x.eps()]
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

.. seealso::
  - MRS isomorphism wiki: http://moin.delph-in.net/MrsIsomorphism
  - :mod:`delphin.mrs.compare` module
  - :mod:`delphin.mrs.query` module


\*MRS Conversion
----------------

Conversions between MRS and DMRS representations is seamless in
PyDelphin, making it easy to convert between many formats (note that
some outputs are abbreviated here):

>>> from delphin.mrs import simplemrs, mrx, dmrx
>>> print(simplemrs.dumps([x], pretty_print=True))
[ TOP: h0
  INDEX: e2 [ e SF: prop TENSE: past MOOD: indicative PROG: - PERF: - ]
  RELS: < [ proper_q<0:6> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: sg IND: + ] RSTR: h5 BODY: h6 ]
          [ named<0:6> LBL: h7 ARG0: x3 CARG: "Abrams" ]
          [ _chase_v_1<7:13> LBL: h1 ARG0: e2 ARG1: x3 ARG2: x9 [ x PERS: 3 NUM: sg IND: + ] ]
          [ proper_q<14:20> LBL: h10 ARG0: x9 RSTR: h11 BODY: h12 ]
          [ named<14:20> LBL: h13 ARG0: x9 CARG: "Browne" ] >
  HCONS: < h0 qeq h1 h5 qeq h7 h11 qeq h13 > ]
>>> print(mrx.dumps([x], pretty_print=True))
<mrs-list>
<mrs cfrom="-1" cto="-1"><label vid="0" /><var sort="e" vid="2">
[...]
</mrs>
</mrs-list>
>>> print(dmrx.dumps([x], pretty_print=True))
<dmrs-list>
<dmrs cfrom="-1" cto="-1" index="10002">
[...]
</dmrs>
</dmrs-list>

.. seealso::
  - Wiki of MRS formats: http://moin.delph-in.net/MrsRfc
  - :mod:`delphin.mrs.simplemrs` module
  - :mod:`delphin.mrs.mrx` module
  - :mod:`delphin.mrs.dmrx` module

Some formats are currently export-only:

>>> from delphin.mrs import prolog, simpledmrs
>>> print(prolog.dumps([x], pretty_print=True))
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
>>> print(simpledmrs.dumps([x], pretty_print=True))
dmrs {
  [top=10002 index=10002]
  10000 [proper_q<0:6> x PERS=3 NUM=sg IND=+];
  10001 [named<0:6>("Abrams") x PERS=3 NUM=sg IND=+];
  10002 [_chase_v_1<7:13> e SF=prop TENSE=past MOOD=indicative PROG=- PERF=-];
  10003 [proper_q<14:20> x PERS=3 NUM=sg IND=+];
  10004 [named<14:20>("Browne") x PERS=3 NUM=sg IND=+];
  10000:RSTR/H -> 10001;
  10002:ARG1/NEQ -> 10001;
  10002:ARG2/NEQ -> 10004;
  10003:RSTR/H -> 10004;
}

.. seealso::
  - :mod:`delphin.mrs.prolog` module
  - :mod:`delphin.mrs.simpledmrs` module

PyDelphin also handles basic conversion to Elementary Dependency
Structures (EDS). The conversion is lossy, so it's not currently
possible to convert from EDS to \*MRS. Unlike the export-only formats
shown above, however, it is possible to read EDS data and convert to
other EDS formats (see below).

>>> from delphin.mrs import eds
>>> print(eds.dumps([x], pretty_print=True))
{e2:
 _1:proper_q<0:6>[BV x3]
 x3:named<0:6>("Abrams")[]
 e2:_chase_v_1<7:13>[ARG1 x3, ARG2 x9]
 _2:proper_q<14:20>[BV x9]
 x9:named<14:20>("Browne")[]
}

.. seealso::
  - :mod:`delphin.mrs.eds` module

MRS, DMRS, and EDS all support `to_dict()` and `from_dict()` methods,
which make it easy to serialize to JSON.

>>> import json
>>> from delphin.mrs import Mrs, Dmrs
>>> print(json.dumps(Mrs.to_dict(x), indent=2))
{
  "relations": [
    {
      "label": "h4",
      "predicate": "proper_q",
[...]
}
>>> print(json.dumps(Dmrs.to_dict(x), indent=2))
{
  "nodes": [
    {
      "nodeid": 10000,
      "predicate": "proper_q",
[...]
}
>>> print(json.dumps(eds.Eds.from_xmrs(x).to_dict(), indent=2))
{
  "top": "e2",
  "nodes": {
    "_1": {
      "label": "proper_q",
      "edges": {
        "BV": "x3"
      },
[...]
}

.. seealso::
  - :class:`~delphin.mrs.xmrs.Mrs` class
  - :class:`~delphin.mrs.xmrs.Dmrs` class
  - :class:`~delphin.mrs.eds.Eds` class

And finally the dependency representations (DMRS and EDS) have
`to_triples()` and `from_triples()` methods, which aid in PENMAN
serialization.

>>> from delphin.mrs import penman
>>> print(penman.dumps([x], model=Dmrs))
(10002 / _chase_v_1
       :lnk "<7:13>"
       :ARG1-NEQ (10001 / named
                        :lnk "<0:6>"
                        :carg "Abrams"
                        :RSTR-H-of (10000 / proper_q
                                          :lnk "<0:6>"))
       :ARG2-NEQ (10004 / named
                        :lnk "<14:20>"
                        :carg "Browne"
                        :RSTR-H-of (10003 / proper_q
                                          :lnk "<14:20>")))
>>> print(penman.dumps([x], model=eds.Eds))
(e2 / _chase_v_1
    :lnk "<7:13>"
    :ARG1 (x3 / named
              :lnk "<0:6>"
              :carg "Abrams"
              :BV-of (_1 / proper_q
                         :lnk "<0:6>"))
    :ARG2 (x9 / named
              :lnk "<14:20>"
              :carg "Browne"
              :BV-of (_2 / proper_q
                         :lnk "<14:20>")))

.. seealso::
  - :mod:`delphin.mrs.penman` module


Tokens and Token Lattices
-------------------------

You can inspect the tokens as analyzed by the processor:

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


[incr tsdb()] TestSuites
------------------------

PyDelphin has full support for reading and writing [incr tsdb()]
testsuites:

>>> from delphin import itsdb
>>> ts = itsdb.TestSuite('erg/tsdb/gold/mrs')
>>> len(ts['item'])
107
>>> ts['item'][0]['i-input']
'It rained.'
>>> ts.write(tables=itsdb.tsdb_core_files, path='mrs-skeleton')

.. seealso::
  - [incr tsdb()] wiki: http://moin.delph-in.net/ItsdbTop
  - :mod:`delphin.itsdb` module
  - :doc:`itsdb` tutorial


TSQL Queries
------------

Partial support of the Test Suite Query Language (TSQL) allows for
easy selection of [incr tsdb()] TestSuite data.

>>> from delphin import itsdb, tsql
>>> ts = itsdb.TestSuite('erg/tsdb/gold/mrs')
>>> next(tsql.select('i-id i-input where i-length > 5 && readings > 0', ts))
[61, 'Abrams handed the cigarette to Browne.']

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
>>> r = repp.REPP.from_config('../../grammars/erg/pet/repp.set')
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
>>> for event, obj, lineno in tdl.iterparse('erg/lexicon.tdl'):
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

>>> from delphin.mrs import semi
>>> s = semi.load('../../grammars/erg/etc/erg.smi')
>>> list(s.variables)
['u', 'i', 'p', 'h', 'e', 'x']
>>> list(s.roles)
['ARG0', 'ARG1', 'ARG2', 'ARG3', 'ARG4', 'ARG', 'BODY', 'CARG', 'L-HNDL', 'L-INDEX', 'R-HNDL', 'R-INDEX', 'RSTR']
>>> s.roles['ARG3']
Role(rargname='ARG3', value='u', proplist=[], optional=False)
>>> list(s.properties)
['bool', '+', '-', 'tense', 'tensed', 'past', 'pres', 'fut', 'untensed', 'mood', 'subjunctive', 'indicative', 'gender', 'm-or-f', 'm', 'f', 'n', 'number', 'sg', 'pl', 'person', '1', '2', '3', 'pt', 'refl', 'std', 'zero', 'sf', 'prop-or-ques', 'prop', 'ques', 'comm']
>>> s.properties['fut']
Property(type='fut', supertypes=('tensed',))
>>> len(s.predicates)
22539
>>> s.predicates['_cactus_n_1']
Predicate(predicate='_cactus_n_1', supertypes=(), synopses=[(Role(rargname='ARG0', value='x', proplist=[('IND', '+')], optional=False),)])

.. seealso::
  - The SEM-I wiki: http://moin.delph-in.net/SemiRfc
  - :mod:`delphin.mrs.semi` module
