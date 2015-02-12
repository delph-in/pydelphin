# pyDelphin <br/> Python libraries for DELPH-IN

pyDelphin is a set of Python libraries for the
processing of [DELPH-IN](http://delph-in.net) data. It doesn't aim to
do heavy tasks like parsing or treebanking, but rather to provide Python
modules for loading a variety of DELPH-IN formats, such as [[incr
tsdb()]](http://www.delph-in.net/itsdb/) profiles or [Minimal Recursion
Semantics](http://moin.delph-in.net/RmrsTop) representations. These
modules offer a programmatic interface to the data to enable developers
or researchers to boostrap their own tools without having to re-invent
the wheel. pyDelphin also provides a [front-end tool](#pydelphin-tool) for
accomplishing some tasks such as refreshing [incr tsdb()] profiles to a new
schema, creating sub-profiles, or converting between MRS representations
(SimpleMRS, MRS XML, DMRS, etc.).

* [Documentation](#documentation)
* [Usage Examples](#usage-examples)
* [Installation and Requirements](#installation-and-requirements)
* [Libraries](#sub-packages)

#### Documentation

API documentation is available here: http://pydelphin.readthedocs.org

#### Usage Examples

Here's a brief example of using the `itsdb` library:

```python3
>>> from delphin import itsdb
>>> prof = itsdb.ItsdbProfile('/home/goodmami/logon/dfki/jacy/tsdb/gold/mrs')
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

```python3
>>> from delphin.codecs import simplemrs
>>> m = simplemrs.loads_one('[ LTOP: h1 INDEX: e2 [ e TENSE: PAST MOOD: INDICATIVE PROG: - PERF: - SF: PROP ASPECT: DEFAULT_ASPECT PASS: - ] RELS: < [ udef_q_rel<0:1> LBL: h3 ARG0: x6 [ x PERS: 3 ] RSTR: h5 BODY: h4 ] [ "_ame_n_rel"<0:1> LBL: h7 ARG0: x6 ] [ "_furu_v_1_rel"<2:3> LBL: h8 ARG0: e2 ARG1: x6 ] > HCONS: < h5 qeq h7 > ]')
>>> m.ltop
MrsVariable(h1)
>>> for r in m.rels:
...     print(r.pred)
... 
udef_q_rel
"_ame_n_rel"
"_furu_v_1_rel"
>>> print(simplemrs.dumps_one(m, pretty_print=True))
[ LTOP: h1 INDEX: e2 [ e TENSE: PAST MOOD: INDICATIVE PROG: - PERF: - SF: PROP ASPECT: DEFAULT_ASPECT PASS: - ]
  RELS: < [ udef_q_rel<0:1> LBL: h3 ARG0: x6 [ x PERS: 3 ] RSTR: h5 BODY: h4 ]
          [ "_ame_n_rel"<0:1> LBL: h7 ARG0: x6 ]
          [ "_furu_v_1_rel"<2:3> LBL: h8 ARG0: e2 ARG1: x6 ] >
  HCONS: < h5 qeq h7 > ]
```

Here is the TDL lexer:

```python3
>>> from delphin import tdl
>>> list(tdl.lex(['identifier := supertype & [ ATTR.SUBATTR value ].']))
[(1, 'TYPEDEF', ['identifier', ':=', 'supertype', '&', '[', 'ATTR', '.', 'SUBATTR', 'value', ']', '.'])]
```

And here is how to use the TDL syntax highlighter:

```python3
>>> from delphin.extra.highlight import TdlLexer
>>> from pygments import highlight
>>> from pygments.formatters import HtmlFormatter
>>> highlight('identifier := supertype & [ ATTR.SUBATTR value ].', TdlLexer(), HtmlFormatter())
'<div class="highlight"><pre><span class="nc">identifier</span> <span class="o">:=</span> <span class="n">supertype</span> <span class="o">&amp;</span> <span class="p">[</span> <span class="na">ATTR.SUBATTR</span> <span class="n">value</span> <span class="p">].</span>\n</pre></div>\n'
```

And here's how to compile, parse, and generate with the ACE wrapper:

```python3
>>> from delphin.interfaces import ace
>>> ace.compile('../jacy/ace/config.tdl', 'jacy.dat')
[...]
>>> ace.parse('jacy.dat', '犬 が 吠える')
{'SENT': '犬 が 吠える', 'NOTES': ['1 readings, added 183 / 54 edges to chart (22 fully instantiated, 26 actives used, 11 passives used)\tRAM: 730k'], 'WARNINGS': [], 'RESULTS': [{'DERIV': '(267 utterance_rule-decl-finite 4.367251 0 3 (266 head_subj_rule 2.906826 0 3 (263 hf-complement-rule -0.956762 0 2 (262 quantify-n-rule 0.215732 0 1 (10 inu-noun 0.049650 0 1 ("犬" 7 "token [ +FORM \\"犬\\" +FROM \\"0\\" +TO \\"1\\" +ID diff-list [ LIST list LAST list ] +POS pos [ +TAGS null +PRBS null ] +CLASS non_ne [ +INITIAL luk ] +TRAIT token_trait +PRED predsort +CARG \\"犬\\" ]"))) (17 ga 0.150269 1 2 ("が" 8 "token [ +FORM \\"が\\" +FROM \\"2\\" +TO \\"3\\" +ID diff-list [ LIST list LAST list ] +POS pos [ +TAGS null +PRBS null ] +CLASS non_ne [ +INITIAL luk ] +TRAIT token_trait +PRED predsort +CARG \\"が\\" ]"))) (265 unary-vstem-vend-rule 3.336552 2 3 (264 ru-lexeme-infl-rule 2.257695 2 3 (18 hoeru_1 0.000000 2 3 ("吠える" 9 "token [ +FORM \\"吠える\\" +FROM \\"4\\" +TO \\"7\\" +ID diff-list [ LIST list LAST list ] +POS pos [ +TAGS null +PRBS null ] +CLASS non_ne [ +INITIAL luk ] +TRAIT token_trait +PRED predsort +CARG \\"吠える\\" ]"))))))', 'MRS': '[ LTOP: h0 INDEX: e2 [ e TENSE: pres MOOD: indicative PROG: - PERF: - ASPECT: default_aspect PASS: - SF: prop ] RELS: < [ udef_q_rel<0:1> LBL: h4 ARG0: x3 [ x PERS: 3 ] RSTR: h5 BODY: h6 ]  [ "_inu_n_rel"<0:1> LBL: h7 ARG0: x3 ]  [ "_hoeru_v_1_rel"<4:7> LBL: h1 ARG0: e2 ARG1: x3 ] > HCONS: < h0 qeq h1 h5 qeq h7 > ]'}], 'ERRORS': []}
>>> res1 = ace.parse('jacy.dat', '犬 が 吠える')['RESULTS'][0]['MRS']
>>> ace.generate('jacy.dat', res1)
{'WARNING': None, 'ERROR': None, 'SENT': None, 'NOTE': None, 'RESULTS': ['犬 が 吠える']}
```

#### pyDelphin Tool

The provided `pyDelphin` top-level script enables you to perform some
actions at the command-line instead of programmatically through the API.
With `pyDelphin`, you can filter and select from [incr tsdb()] profiles,
write sub-profiles, and apply operations to the data. The pyDelphin
code takes care of filling in default values and escaping delimiters for
you. For example, to select the `i-id` and `i-input` fields from the
`item` table and print them to stdout, use the select sub-command:

```bash
$ ./pyDelphin --input ~/logon/dfki/jacy/tsdb/gold/mrs \
              select item:i-id@i-input
11@雨 が 降っ た ．
21@太郎 が 吠え た ．
[..]
```

The `pyDelphin` script has several sub-commands with their own options,
similar to how Subversion has `svn commit` and `svn update`. The
current set of sub-commands is:

  * select  : selecting and printing data from an [incr tsdb()] profile
  * mkprof  : output a new [incr tsdb()] profile or skeleton
  * compare : compare bags of MRSs (a lightweight way to see if
              performance has changed in a profile)

Some options of pyDelphin work for all sub-commands, while others work
only for a specific command. Try running `pyDelphin -h` to get global
help, and `pyDelphin {command} -h` to get help specific to a `{command}`.

If you want to, for example, remove the spaces in i-input, you can
use `--apply` to apply a Python expression to the field. The
expression is applied on every column specified, and the variable
`x` is the value at the current column.

```bash
$ ./pyDelphin --input ~/logon/dfki/jacy/tsdb/gold/mrs \
              --apply item:i-input "x.replace(' ','')" \
              select item:i-id@i-input
11@雨が降った．
21@太郎が吠えた．
[..]
```

The variable `row` is also available in the expression if a column
specifier is provided. It is a dictionary containing all data in the
row, so this is equivalent to the previous:

```bash
$ ./pyDelphin --input ~/logon/dfki/jacy/tsdb/gold/mrs \
              --apply item:i-input "row['i-input'].replace(' ','')" \
              select item:i-id@i-input
11@雨が降った．
21@太郎が吠えた．
[..]
```

The `--filter` option is defined much like `--apply`, but instead of
changing the value of a cell, it filters the results that are returned.
The expression should, therefore, return a value that can be evaluated
as True or False. The command below finds all items that have the word
"雨":

```bash
$ ./pyDelphin --input ~/logon/dfki/jacy/tsdb/gold/mrs \
              --filter item:i-input "'雨' in x" \
              select item:i-id@i-input
11@雨 が 降っ た ．
71@太郎 が タバコ を 次郎 に 雨 が 降る と 賭け た ．
81@太郎 が 雨 が 降っ た こと を 知っ て い た ．
```

The `--cascade-filters` option, if set, filters rows in tables that
depend on a filtered table. For example, we can select the MRSs of
items whose i-input contains the word "雨":

```bash
$ ./pyDelphin --input ~/logon/dfki/jacy/tsdb/gold/mrs \
              --filter item:i-input "'雨' in x" --cascade-filters \
              select result:mrs
[ LTOP: h1 INDEX: e2 [ e TENSE: PAST MOOD: INDICATIVE PROG: - PERF: - SF: PROP ASPECT: DEFAULT_ASPECT PASS: - ] RELS: < [ udef_q_rel<0:1> LBL: h3 ARG0: x6 [ x PERS: 3 ] RSTR: h5 BODY: h4 ] [ "_ame_n_rel"<0:1> LBL: h7 ARG0: x6 ] [ "_furu_v_1_rel"<2:3> LBL: h8 ARG0: e2 ARG1: x6 ] > HCONS: < h5 qeq h7 > ]
[ LTOP: h1 INDEX: e2 [ e TENSE: PAST MOOD: INDICATIVE PROG: + PERF: - SF: PROP ASPECT: DEFAULT_ASPECT PASS: - ] RELS: < [ def_q_rel<0:1> LBL: h3 ARG0: x4 RSTR: h5 BODY: h6 ] [ named_rel<0:1> LBL: h7 ARG0: x4 CARG: "tarou_2" ] [ udef_q_rel<2:3> LBL: h8 ARG0: x11 [ x PERS: 3 ] RSTR: h10 BODY: h9 ] [ "_ame_n_rel"<2:3> LBL: h12 ARG0: x11 ] [ "_furu_v_1_rel"<4:5> LBL: h13 ARG0: e14 [ e TENSE: PAST MOOD: INDICATIVE PROG: - PERF: - SF: PROP ASPECT: DEFAULT_ASPECT PASS: - ] ARG1: x11 ] [ "_koto_n_nom_rel"<6:7> LBL: h15 ARG0: x16 ARG1: h17 ] [ udef_q_rel<6:7> LBL: h18 ARG0: x16 RSTR: h20 BODY: h19 ] [ "_shiru_v_1_rel"<8:9> LBL: h21 ARG0: e2 ARG1: x4 ARG2: x16 ] > HCONS: < h5 qeq h7 h10 qeq h12 h20 qeq h15 h17 qeq h13 > ]
```

Rather than selecting data to send to stdout, you can also output a
new [incr tsdb()] profile with the `mkprof` sub-command. The new profile
contains the tables and rows of the input profile after filters and
applications have been used. By default, the relations file of the
input profile is copied, but it is possible to use a different one
with the `--relations` option. For example, the following command
refreshes a profile to a new relations file:

```bash
$ ./pyDelphin --input ~/logon/dfki/jacy/tsdb/gold/mrs \
              mkprof ~/logon/dfki/jacy/tsdb/gold/mrs-refreshed \
              --relations ~/logon/lingo/lkb/src/tsdb/skeletons/english/Relations
```

Using filters, sub-profiles can be created, which may be useful for
testing different parameters. For example, to create a sub-profile
with only items whose i-length is less than 10, do this:

```bash
$ ./pyDelphin --input ~/logon/dfki/jacy/tsdb/gold/mrs \
              --filter item:i-length "int(x) < 10"
              mkprof ~/logon/dfki/jacy/tsdb/gold/mrs-short
```


## Installation and Requirements

pyDelphin is developed for [Python 3](http://python.org/download/). The
[NetworkX](http://networkx.github.io/) library is necessary for the MRS
package. [Pygments](http://pygments.org/) is required for TDL syntax
highlighting.

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

## Sub-packages

The following packages/modules are available:

- `itsdb`: [incr tsdb()] profiles
- `mrs`: Minimal Recursion Semantics
- `tdl`: Type-Description Language (currently just lexing)
- `extra.highlight`: [Pygments](http://pygments.org/)-based syntax
  highlighting (currently just for TDL)
- `interfaces.ace`: Python wrapper for common tasks using
  [ACE](http://sweaglesw.org/linguistics/ace/)

And the following libraries are planned:

- A module for working with derivation trees
- A SEM-I processor

## Contributors

- [T.J. Trimble](https://github.com/dantiston/)
