
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
>>> m.ltop  # doctest: +ELLIPSIS
<MrsVariable object (h0) ...>
>>> m.index  # doctest: +ELLIPSIS
<MrsVariable object (e2) ...>
>>> len(m.rels)
1
>>> m.rels[0].pred  # doctest: +ELLIPSIS
<Pred object "_rain_v_1_rel" ...>
>>> m.rels[0].intrinsic_variable  # doctest: +ELLIPSIS
<MrsVariable object (e2) ...>
>>> sorted(m.rels[0].intrinsic_variable.properties.items())
[('MOOD', 'indicative'), ('PERF', '-'), ('PROG', '-'), ('SF', 'prop'), ('TENSE', 'pres')]
>>> m.hcons  # doctest: +ELLIPSIS
[<HandleConstraint object (h0 qeq h1) ...>]

```

"Abrams sleeps".

```python
>>> m = next(simplemrs.loads('''[ LTOP: h0
... INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
... RELS: < [ proper_q_rel<0:6> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: sg IND: + ] RSTR: h5 BODY: h6 ]
...         [ named_rel<0:6> LBL: h7 CARG: "Abrams" ARG0: x3 ]
...         [ "_sleep_v_1_rel"<7:14> LBL: h1 ARG0: e2 ARG1: x3 ] >
... HCONS: < h0 qeq h1 h5 qeq h7 > ]'''))
>>> m.ltop  # doctest: +ELLIPSIS
<MrsVariable object (h0) ...>
>>> m.index  # doctest: +ELLIPSIS
<MrsVariable object (e2) ...>
>>> len(m.rels)
3
>>> m.rels[0].pred  # doctest: +ELLIPSIS
<Pred object proper_q_rel ...>
>>> m.rels[0].intrinsic_variable  # doctest: +ELLIPSIS
<MrsVariable object (x3) ...>
>>> sorted(m.rels[0].intrinsic_variable.properties.items())
[('IND', '+'), ('NUM', 'sg'), ('PERS', '3')]
>>> m.rels[1].pred  # doctest: +ELLIPSIS
<Pred object named_rel ...>
>>> m.rels[1].intrinsic_variable  # doctest: +ELLIPSIS
<MrsVariable object (x3) ...>
>>> m.rels[1].arg_value('CARG')
'"Abrams"'
>>> m.rels[2].pred  # doctest: +ELLIPSIS
<Pred object "_sleep_v_1_rel" ...>
>>> m.rels[2].intrinsic_variable  # doctest: +ELLIPSIS
<MrsVariable object (e2) ...>
>>> sorted(m.rels[2].intrinsic_variable.properties.items())
[('MOOD', 'indicative'), ('PERF', '-'), ('PROG', '-'), ('SF', 'prop'), ('TENSE', 'pres')]
>>> m.rels[2].arg_value('ARG1')  # doctest: +ELLIPSIS
<MrsVariable object (x3) ...>
>>> m.hcons  # doctest: +ELLIPSIS
[<HandleConstraint object (h0 qeq h1) ...>, <HandleConstraint object (h5 qeq h7) ...>]

```