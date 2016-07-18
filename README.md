# pyDelphin <br/> Python libraries for DELPH-IN

| Branch | Status |
| ------ | ------ |
| [master](https://github.com/delph-in/pydelphin/tree/master)  | [![Build Status](https://travis-ci.org/delph-in/pydelphin.svg?branch=master)](https://travis-ci.org/delph-in/pydelphin) |
| [develop](https://github.com/delph-in/pydelphin/tree/develop) | [![Build Status](https://travis-ci.org/delph-in/pydelphin.svg?branch=develop)](https://travis-ci.org/delph-in/pydelphin) |

> NOTE for previous pyDelphin users: Recent versions of pyDelphin may
> have backwards-incompatible changes with prior versions. Please
> [file an issue](https://github.com/delph-in/pydelphin/issues) if you
> have trouble upgrading.

pyDelphin is a set of Python libraries for the
processing of [DELPH-IN](http://delph-in.net) data. It doesn't aim to
do heavy tasks like parsing or treebanking, but rather to provide Python
modules for loading a variety of DELPH-IN formats, such as [[incr
tsdb()]](http://www.delph-in.net/itsdb/) profiles or [Minimal Recursion
Semantics](http://moin.delph-in.net/RmrsTop) representations. These
modules offer a programmatic interface to the data to enable developers
or researchers to boostrap their own tools without having to re-invent
the wheel. pyDelphin also provides a [front-end tool][] for
accomplishing some tasks such as refreshing [incr tsdb()] profiles to a new
schema, creating sub-profiles, or converting between MRS representations
(SimpleMRS, MRS XML, DMRS, etc.).

* [Documentation](#documentation)
* [Usage Examples](#usage-examples)
* [Installation and Requirements](#installation-and-requirements)
* [Libraries](#sub-packages)

[front-end tool]: https://github.com/delph-in/pydelphin/wiki/Command-line-Tutorial

#### Documentation

API documentation is developing on the
[wiki](https://github.com/delph-in/pydelphin/wiki). Help is
appreciated!

#### Usage Examples

Here's a brief example of using the `itsdb` library:

```python
>>> from delphin import itsdb
>>> prof = itsdb.ItsdbProfile('~/logon/dfki/jacy/tsdb/gold/mrs')
>>> for row in prof.read_table('item'):
...     print(row.get('i-input'))
雨 が 降っ た ．
太郎 が 吠え た ．
窓 が 開い た ．
太郎 が 次郎 を 追っ た ．
[...]
>>> next(prof.read_table('result')).get('derivation')
'(utterance-root (91 utterance_rule-decl-finite -0.723739 0 4 (90 head_subj_rule -1.05796 0 4 (87 hf-complement-rule -0.50201 0 2 (86 quantify-n-rule -0.32216 0 1 (5 ame-noun 0 0 1 ("雨" 1 "\\"雨\\""))) (6 ga 0.531537 1 2 ("が" 2 "\\"が\\""))) (89 vstem-vend-rule -0.471785 2 4 (88 t-lexeme-c-stem-infl-rule 0.120963 2 3 (14 furu_1 0 2 3 ("降っ" 3 "\\"降っ\\""))) (24 ta-end -0.380719 3 4 ("た" 4 "\\"た\\""))))))'
```

Here's an example of loading a SimpleMRS representation:

```python
>>> from delphin.codecs import simplemrs
>>> m = simplemrs.loads_one('[ LTOP: h1 INDEX: e2 [ e TENSE: PAST MOOD: INDICATIVE PROG: - PERF: - SF: PROP ASPECT: DEFAULT_ASPECT PASS: - ] RELS: < [ udef_q_rel<0:1> LBL: h3 ARG0: x6 [ x PERS: 3 ] RSTR: h5 BODY: h4 ] [ "_ame_n_rel"<0:1> LBL: h7 ARG0: x6 ] [ "_furu_v_1_rel"<2:3> LBL: h8 ARG0: e2 ARG1: x6 ] > HCONS: < h5 qeq h7 > ]')
>>> m.ltop
'h1'
>>> for p in m.preds():
...     print('{}|{}|{}|{}'.format(p.string, p.lemma, p.pos, p.sense))
... 
udef_q_rel|udef|q|None
"_ame_n_rel"|ame|n|None
"_furu_v_1_rel"|furu|v|1
>>> print(simplemrs.dumps_one(m, pretty_print=True))
[ TOP: h1
  INDEX: e2 [ e TENSE: PAST MOOD: INDICATIVE PROG: - PERF: - SF: PROP ASPECT: DEFAULT_ASPECT PASS: - ]
  RELS: < [ udef_q_rel<0:1> LBL: h3 ARG0: x6 [ x PERS: 3 ] RSTR: h5 BODY: h4 ]
          [ "_ame_n_rel"<0:1> LBL: h7 ARG0: x6 ]
          [ "_furu_v_1_rel"<2:3> LBL: h8 ARG0: e2 ARG1: x6 ] >
  HCONS: < h5 qeq h7 > ]

```

Here is TDL introspection:

```python
>>> from delphin import tdl
>>> f = open('~/logon/lingo/erg/fundamentals.tdl', 'r')
>>> types = {t.identifier: t for t in tdl.parse(f)}
>>> types['basic_word'].supertypes
['word_or_infl_rule', 'word_or_punct_rule']
>>> types['basic_word'].features()
[('SYNSEM', <TdlDefinition object at 140559634120136>), ('TOKENS', <TdlDefinition object at 140559631479864>), ('ORTH', <TdlDefinition object at 140559631479000>)]
>>> types['basic_word'].coreferences
[('#rb', ['ORTH.RB', 'TOKENS.+LAST.+TRAIT.+RB']), ('#to', ['SYNSEM.LKEYS.KEYREL.CTO', 'ORTH.TO', 'TOKENS.+LAST.+TO']), ('#lb', ['ORTH.LB', 'TOKENS.+LIST.FIRST.+TRAIT.+LB']), ('#form', ['ORTH.FORM', 'TOKENS.+LIST.FIRST.+FORM']), ('#tl', ['SYNSEM.PHON.ONSET.--TL', 'TOKENS.+LIST']), ('#from', ['SYNSEM.LKEYS.KEYREL.CFROM', 'ORTH.FROM', 'TOKENS.+LIST.FIRST.+FROM']), ('#class', ['ORTH.CLASS', 'TOKENS.+LIST.FIRST.+CLASS'])]

```

And here's how to compile, parse, and generate with the ACE wrapper:

```python
>>> from delphin.interfaces import ace
>>> ace.compile('../jacy/ace/config.tdl', 'jacy.dat')
[...]
>>> response = ace.parse('jacy.dat', '犬 が 吠える')
>>> len(response.results())
1
>>> response.result(0).keys()
dict_keys(['DERIV', 'MRS'])
>>> response.result(0)['MRS']
'[ LTOP: h0 INDEX: e2 [ e TENSE: pres MOOD: indicative PROG: - PERF: - ASPECT: default_aspect PASS: - SF: prop ] RELS: < [ udef_q_rel<0:1> LBL: h4 ARG0: x3 [ x PERS: 3 ] RSTR: h5 BODY: h6 ]  [ "_inu_n_rel"<0:1> LBL: h7 ARG0: x3 ]  [ "_hoeru_v_1_rel"<4:7> LBL: h1 ARG0: e2 ARG1: x3 ] > HCONS: < h0 qeq h1 h5 qeq h7 > ]'
>>> response.result(0).mrs()
<Xmrs object (udef inu hoeru) at 140352613240112>
>>> ace.generate('jacy.dat', response.result(0)['MRS']).results()
[ParseResult({'SENT': '犬 が 吠える'})]
```


## Installation and Requirements

pyDelphin is developed for [Python 3](http://python.org/download/)
(3.3+), but it has also been tested to work with Python 2.7. Optional
requirements include:
  - [NetworkX](http://networkx.github.io/) for MRS isomorphism
    checking
  - [requests](http://requests.readthedocs.io/en/master/) for the
    REST client
  - [Pygments](http://pygments.org/) for TDL and SimpleMRS syntax
    highlighting
  - [tikz-dependency](https://www.ctan.org/pkg/tikz-dependency), while
    not a Python requirement, is needed for compiling LaTeX documents
    using exported DMRSs

pyDelphin itself does not need to be installed to be used. You can
[adjust `PYTHONPATH`](https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH)
to include the pyDelphin directory.

If you would rather install it, however, it is available on
[PyPI](https://pypi.python.org/pypi/pyDelphin):

```bash
$ pip install pydelphin
```

## Sub-packages

The following packages/modules are available:

- `derivation`: [Derivation trees](http://moin.delph-in.net/ItsdbDerivations)
- `itsdb`: [incr tsdb()] profiles
- `mrs`: Minimal Recursion Semantics
- `tdl`: Type-Description Language
- `tfs`: Typed-Feature Structures
- `tokens`: Token lattices
- `extra.highlight`: [Pygments](http://pygments.org/)-based syntax
  highlighting (currently just for TDL and SimpleMRS)
- `extra.latex`: Formatting for LaTeX (just DMRS)
- `interfaces.ace`: Python wrapper for common tasks using
  [ACE](http://sweaglesw.org/linguistics/ace/)
- `interfaces.rest`: Client for the RESTful web 
  [API](http://moin.delph-in.net/ErgApi)

## Contributors

- [Michael Wayne Goodman](https://github.com/goodmami/) (primary author)
- [T.J. Trimble](https://github.com/dantiston/) (packaging, derivations, ACE)
- [Guy Emerson](https://github.com/guyemerson/) (MRS)
- [Alex Kuhnle](https://github.com/AlexKuhnle/) (MRS, ACE)

## Related Software

* Parser/Generators (chronological order)
  - LKB: http://moin.delph-in.net/LkbTop
  - PET: http://moin.delph-in.net/PetTop
  - ACE: http://sweaglesw.org/linguistics/ace/
  - agree: http://moin.delph-in.net/AgreeTop
* Grammar profiling, testing, and analysis
  - [incr tsdb()]: http://www.delph-in.net/itsdb/
  - gDelta: https://github.com/ned2/gdelta
  - Typediff: https://github.com/ned2/typediff
  - gTest: https://github.com/goodmami/gtest
* Software libraries and repositories
  - LOGON: http://moin.delph-in.net/LogonTop
  - Ruby-DELPH-IN: https://github.com/wpm/Ruby-DELPH-IN
  - pydmrs: https://github.com/delph-in/pydmrs
* Also see (may have overlap with the above):
  - http://moin.delph-in.net/ToolsTop
  - http://moin.delph-in.net/DelphinApplications
