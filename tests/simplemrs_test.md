
# Unit tests for the `simplemrs` module

To run, do this at the command prompt:

    $ python3 -m doctest tests/simplemrs_test.md

Note: nothing will be shown if tests pass. You can add a verbose flag
(`-v`) to see all results.

## Loading the `simplemrs` module

The `simplemrs` module is a library of functions, not a script, so import it:

```python
>>> from delphin.mrs import simplemrs

```

The Xmrs objects sacrifice some user-friendliness for performance, so
using the `components` module will help with inspecting objects.

```python
>>> from delphin.mrs.components import (
...     ElementaryPredication as EP,
...     HandleConstraint as Hcons,
...     IndividualConstraint as Icons
... )

```

## Tokenization

The `simplemrs.tokenize()` method breaks up streams of SimpleMRS text
into the logical units for parsing.

### Variables

Variables should be kept together, even if they are long:

```python
>>> list(simplemrs.tokenize('h1 e2 x3 p4 i5 u6'))
['h1', 'e2', 'x3', 'p4', 'i5', 'u6']
>>> list(simplemrs.tokenize('h123456'))
['h123456']
>>> list(simplemrs.tokenize(
...     'handle1 event2 ref-ind3 non_event4 individual5 semarg6'
... ))
['handle1', 'event2', 'ref-ind3', 'non_event4', 'individual5', 'semarg6']

```

### Strings

Strings may contain spaces or escaped quotes

```python
>>> list(simplemrs.tokenize('"double-quoted \\"string\\""'))
['"double-quoted \\"string\\""']
>>> list(simplemrs.tokenize("'single-quoted_\\'string"))
["'single-quoted_\\'string"]
>>> list(simplemrs.tokenize('i2"double-quoted \\"string\\""x5'))
['i2', '"double-quoted \\"string\\""', 'x5']

```

### Lnk values

Lnk values can take 4 forms in SimpleMRS:

```python
>>> list(simplemrs.tokenize('<0:15>'))
['<', '0', ':', '15', '>']
>>> list(simplemrs.tokenize('<0#15>'))
['<', '0', '#', '15', '>']
>>> list(simplemrs.tokenize('<@5>'))
['<', '@', '5', '>']
>>> list(simplemrs.tokenize('<1 2 3>'))
['<', '1', '2', '3', '>']

```

### Full MRSs

"It rains"---very simple structure.

```python
>>> list(simplemrs.tokenize('''[ LTOP: h0
... INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
... RELS: < [ "_rain_v_1_rel"<3:9> LBL: h1 ARG0: e2 ] >
... HCONS: < h0 qeq h1 > ]'''))
['[', 'LTOP', ':', 'h0', 'INDEX', ':', 'e2', '[', 'e', 'SF', ':', 'prop', 'TENSE', ':', 'pres', 'MOOD', ':', 'indicative', 'PROG', ':', '-', 'PERF', ':', '-', ']', 'RELS', ':', '<', '[', '"_rain_v_1_rel"', '<', '3', ':', '9', '>', 'LBL', ':', 'h1', 'ARG0', ':', 'e2', ']', '>', 'HCONS', ':', '<', 'h0', 'qeq', 'h1', '>', ']']

```

"Abrams sleeps"---still simple, but with CARG.

```python
>>> list(simplemrs.tokenize('''[ LTOP: h0
... INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
... RELS: < [ proper_q_rel<0:6> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: sg IND: + ] RSTR: h5 BODY: h6 ]
...         [ named_rel<0:6> LBL: h7 CARG: "Abrams" ARG0: x3 ]
...         [ "_sleep_v_1_rel"<7:14> LBL: h1 ARG0: e2 ARG1: x3 ] >
... HCONS: < h0 qeq h1 h5 qeq h7 > ]'''))
['[', 'LTOP', ':', 'h0', 'INDEX', ':', 'e2', '[', 'e', 'SF', ':', 'prop', 'TENSE', ':', 'pres', 'MOOD', ':', 'indicative', 'PROG', ':', '-', 'PERF', ':', '-', ']', 'RELS', ':', '<', '[', 'proper_q_rel', '<', '0', ':', '6', '>', 'LBL', ':', 'h4', 'ARG0', ':', 'x3', '[', 'x', 'PERS', ':', '3', 'NUM', ':', 'sg', 'IND', ':', '+', ']', 'RSTR', ':', 'h5', 'BODY', ':', 'h6', ']', '[', 'named_rel', '<', '0', ':', '6', '>', 'LBL', ':', 'h7', 'CARG', ':', '"Abrams"', 'ARG0', ':', 'x3', ']', '[', '"_sleep_v_1_rel"', '<', '7', ':', '14', '>', 'LBL', ':', 'h1', 'ARG0', ':', 'e2', 'ARG1', ':', 'x3', ']', '>', 'HCONS', ':', '<', 'h0', 'qeq', 'h1', 'h5', 'qeq', 'h7', '>', ']']

```

## Parsing

"It rains".

```python
>>> m = next(simplemrs.loads('''[ LTOP: h0
... INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
... RELS: < [ "_rain_v_1_rel"<3:9> LBL: h1 ARG0: e2 ] >
... HCONS: < h0 qeq h1 > ]'''))
>>> m.ltop
'h0'
>>> m.index
'e2'
>>> len(m.eps())
1
>>> m.eps()[0][1]  # doctest: +ELLIPSIS
<Pred object "_rain_v_1_rel" ...>
>>> EP(*m.eps()[0]).pred.string
'"_rain_v_1_rel"'
>>> EP(*m.eps()[0]).args['ARG0']
'e2'
>>> sorted(m.properties('e2').items())
[('MOOD', 'indicative'), ('PERF', '-'), ('PROG', '-'), ('SF', 'prop'), ('TENSE', 'pres')]
>>> len(m.hcons())
1
>>> hc = Hcons(*m.hcons()[0])
>>> hc.hi, hc.relation, hc.lo
('h0', 'qeq', 'h1')

```

Multiple MRSs can be parsed with `simplemrs.loads()`:

"It rains." and "It snows."

```python
>>> mrs_gen = simplemrs.loads('''[ LTOP: h0
... INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
... RELS: < [ "_rain_v_1_rel"<3:9> LBL: h1 ARG0: e2 ] >
... HCONS: < h0 qeq h1 > ] [ LTOP: h0
... INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
... RELS: < [ "_snow_v_1_rel"<3:9> LBL: h1 ARG0: e2 ] >
... HCONS: < h0 qeq h1 > ]''')
>>> next(mrs_gen)  # doctest: +ELLIPSIS
<Xmrs object (rain) at ...>
>>> next(mrs_gen)  # doctest: +ELLIPSIS
<Xmrs object (snow) at ...>

```

But requesting more than is available causes a `StopIteration` exception:

```python
>>> try:
...     next(mrs_gen)
... except StopIteration:
...     print('StopIteration caught!')
StopIteration caught!

```

"It rains", SimpleMRS 1.1 format without surface forms or a top LNK value.

```python
>>> m = next(simplemrs.loads('''[ TOP: h0
... INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
... RELS: < [ "_rain_v_1_rel"<3:9> LBL: h1 ARG0: e2 ] >
... HCONS: < h0 qeq h1 > ]'''))
>>> m.ltop
'h0'
>>> m.cfrom
-1
>>> m.cto
-1
>>> m.surface is None
True
>>> EP(*m.eps()[0]).surface is None
True

```

"It rains", SimpleMRS 1.1 format with surface forms and a top LNK value.

```python
>>> m = next(simplemrs.loads('''[ <0:9> "It rains." TOP: h0
... INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
... RELS: < [ "_rain_v_1_rel"<3:9> "rains." LBL: h1 ARG0: e2 ] >
... HCONS: < h0 qeq h1 > ]'''))
>>> m.cfrom
0
>>> m.cto
9
>>> m.surface
'It rains.'
>>> EP(*m.eps()[0]).surface
'rains.'

```

"It rains", SimpleMRS 1.1 format with everything including ICONS.

```python
>>> m = next(simplemrs.loads('''[ <0:9> "It rains." TOP: h0
... INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
... RELS: < [ "_rain_v_1_rel"<3:9> "rains." LBL: h1 ARG0: e2 ] >
... HCONS: < h0 qeq h1 >
... ICONS: < e2 focus e2 > ]'''))
>>> len(m.icons())
1
>>> ic = Icons(*m.icons()[0])
>>> ic.left
'e2'
>>> ic.right
'e2'
>>> ic.relation
'focus'

```

"Abrams sleeps".

```python
>>> m = next(simplemrs.loads('''[ LTOP: h0
... INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
... RELS: < [ proper_q_rel<0:6> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: sg IND: + ] RSTR: h5 BODY: h6 ]
...         [ named_rel<0:6> LBL: h7 CARG: "Abrams" ARG0: x3 ]
...         [ "_sleep_v_1_rel"<7:14> LBL: h1 ARG0: e2 ARG1: x3 ] >
... HCONS: < h0 qeq h1 h5 qeq h7 > ]'''))
>>> m.ltop
'h0'
>>> m.index
'e2'
>>> len(m.eps())
3
>>> ep = EP(*m.eps()[0])
>>> ep.pred  # doctest: +ELLIPSIS
<Pred object proper_q_rel ...>
>>> ep.intrinsic_variable
'x3'
>>> sorted(m.properties('x3').items())
[('IND', '+'), ('NUM', 'sg'), ('PERS', '3')]
>>> ep = EP(*m.eps()[1])
>>> ep.pred  # doctest: +ELLIPSIS
<Pred object named_rel ...>
>>> ep.intrinsic_variable
'x3'
>>> ep.args['CARG']
'Abrams'
>>> ep = EP(*m.eps()[2])
>>> ep.pred  # doctest: +ELLIPSIS
<Pred object "_sleep_v_1_rel" ...>
>>> ep.intrinsic_variable
'e2'
>>> sorted(m.properties('e2').items())
[('MOOD', 'indicative'), ('PERF', '-'), ('PROG', '-'), ('SF', 'prop'), ('TENSE', 'pres')]
>>> ep.args['ARG1']
'x3'
>>> [Hcons(*hc) for hc in sorted(m.hcons())]  # doctest: +ELLIPSIS
[<HandleConstraint object (h0 qeq h1) ...>, <HandleConstraint object (h5 qeq h7) ...>]

```


## Serializing

"It rains", SimpleMRS 1.1 format with everything including ICONS. By
default, version 1.1 is printed. Also, separately, by default, an MRS is
printed on one line (as it would be in an [incr tsdb()] profile).

```python
>>> m = next(simplemrs.loads('''[ <0:9> "It rains." TOP: h0
... INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
... RELS: < [ "_rain_v_1_rel"<3:9> "rains." LBL: h1 ARG0: e2 ] >
... HCONS: < h0 qeq h1 >
... ICONS: < e2 focus e2 > ]'''))
>>> print(simplemrs.dumps([m]))
[ <0:9> "It rains." TOP: h0 INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ] RELS: < [ "_rain_v_1_rel"<3:9> "rains." LBL: h1 ARG0: e2 ] > HCONS: < h0 qeq h1 > ICONS: < e2 focus e2 > ]

```

With the `pretty_print` parameter set to `True`, the MRS is indented
nicely.

```python
>>> print(simplemrs.dumps([m], pretty_print=True))
[ <0:9> "It rains."
  TOP: h0
  INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
  RELS: < [ "_rain_v_1_rel"<3:9> "rains." LBL: h1 ARG0: e2 ] >
  HCONS: < h0 qeq h1 >
  ICONS: < e2 focus e2 > ]

```

And by specifying the version to be 1.0, the extra information is not
printed, although for compatibility with ACE the ICONS list is printed.

```python
>>> print(simplemrs.dumps([m], pretty_print=True, version=1.0))
[ LTOP: h0
  INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
  RELS: < [ "_rain_v_1_rel"<3:9> LBL: h1 ARG0: e2 ] >
  HCONS: < h0 qeq h1 >
  ICONS: < e2 focus e2 > ]

```

## Parsing Robustness

"It rains", case-insensitivity

```python
>>> m = next(simplemrs.loads('''[ ltop: h0
... InDeX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
... Rels: < [ "_rain_v_1_rel"<3:9> lbl: h1 arg0: e2 ] >
... HCons: < h0 QEQ h1 > ]'''))
>>> m.ltop
'h0'
>>> m.index
'e2'
>>> len(m.eps())
1
>>> EP(*m.eps()[0]).label
'h1'
>>> EP(*m.eps()[0]).args['ARG0']
'e2'
>>> len(m.hcons())
1
>>> Hcons(*m.hcons()[0]).relation
'qeq'

```

Uncommon predicate forms:

```python
>>> m = next(simplemrs.loads('''[ RELS: <
... [ _<\sccil.org>/nn_u_unknown<40:51> LBL: h1 ARG0: x2 ]
... > ]'''))
 