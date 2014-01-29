# pyDelphin <br/> Python libraries for DELPH-IN

pyDelphin is a (slowly growing) collection of Python software for the
processing of [DELPH-IN](http://delph-in.net) data. It doesn't aim to
do heavy tasks like parsing or treebanking, but rather provides Python
modules for loading a variety of DELPH-IN formats, such as [[incr
tsdb()]](http://www.delph-in.net/itsdb/) profiles or [Minimal Recursion
Semantics](http://moin.delph-in.net/RmrsTop) representations. These
modules offer a programmatic interface to the data to enable developers
or researchers to boostrap their own tools without having to re-invent
the wheel. pyDelphin also provides some basic front-end scripts for
tasks such as refreshing [incr tsdb()] profiles to a new schema or
converting between MRS representations (SimpleMRS, MRS XML, DMRS, etc.).

* [Usage Examples](#usage-examples)
* [Installation and Requirements](#installation-and-requirements)
* [Libraries](#libraries)

#### Usage Examples

Here's a brief example of using the `itsdb` library:

```python3
>>> from delphin import itsdb
>>> profile = itsdb.TsdbProfile('jacy/tsdb/gold/mrs/')
>>> print(next(profile.get_table('result').rows())['derivation'])
(utterance-root (91 utterance_rule-decl-finite -0.723739 0 4 (90 head_subj_rule -1.05796 0 4 (87 hf-complement-rule -0.50201 0 2 (86 quantify-n-rule -0.32216 0 1 (5 ame-noun 0 0 1 ("雨" 1 "\\"雨\\""))) (6 ga 0.531537 1 2 ("が" 2 "\\"が\\""))) (89 vstem-vend-rule -0.471785 2 4 (88 t-lexeme-c-stem-infl-rule 0.120963 2 3 (14 furu_1 0 2 3 ("降っ" 3 "\\"降っ\\""))) (24 ta-end -0.380719 3 4 ("た" 4 "\\"た\\""))))))
```

And here's an example of loading a SimpleMRS representation:

```python3
>>> from delphin.codecs import simplemrs
>>> m = simplemrs.loads('[ LTOP: h1 INDEX: e2 [ e TENSE: PAST MOOD: INDICATIVE PROG: - PERF: - SF: PROP ASPECT: DEFAULT_ASPECT PASS: - ] RELS: < [ udef_q_rel<0:1> LBL: h3 ARG0: x6 [ x PERS: 3 ] RSTR: h5 BODY: h4 ] [ "_ame_n_rel"<0:1> LBL: h7 ARG0: x6 ] [ "_furu_v_1_rel"<2:3> LBL: h8 ARG0: e2 ARG1: x6 ] > HCONS: < h5 qeq h7 > ]')
>>> m.ltop
MrsVariable(h1)
>>> for r in m.rels:
...     print(r.pred)
... 
udef_q_rel
"_ame_n_rel"
"_furu_v_1_rel"
>>> print(simplemrs.dumps(m, pretty_print=True))
[ LTOP: h1 INDEX: e2 [ e TENSE: PAST MOOD: INDICATIVE PROG: - PERF: - SF: PROP ASPECT: DEFAULT_ASPECT PASS: - ]
  RELS: < [ udef_q_rel<0:1> LBL: h3 ARG0: x6 [ x PERS: 3 ] RSTR: h5 BODY: h4 ]
          [ "_ame_n_rel"<0:1> LBL: h7 ARG0: x6 ]
          [ "_furu_v_1_rel"<2:3> LBL: h8 ARG0: e2 ARG1: x6 ] >
  HCONS: < h5 qeq h7 > ]
```

## Installation and Requirements

pyDelphin is developed for [Python 3](http://python.org/download/). At
this time, no third-party libraries are necessary.

Likely pyDelphin does not need to be installed to be used. You can
adjust `PYTHONPATH` to include the pyDelphin directory, or copy the
`delphin/` subdirectory into your project's main directory.

If you want to have the `delphin` packages generally available for
importing, you can use the provided `setup.py` script to install (you
may need to run the following as root):

```bash
$ ./setup.py install
```

The `setup.py` script, unfortunately, does not have an
uninstall/remove option, so in order to remove an installed pyDelphin,
you'll need to track down and remove the files that were installed (in
your Python site packages).

## Libraries

The following libraries are available:

- `itsdb`: [incr tsdb()] profiles
- `mrs`: Minimal Recursion Semantics

And the following libraries are planned:

- `tdl`: Type-Description Language
- A module for working with derivation trees
