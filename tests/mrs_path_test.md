
# Unit tests for the `mrs.path` module

To run, do this at the command prompt:

    $ python3 -m doctest tests/mrs_path_test.md

Note: nothing will be shown if tests pass. You can add a verbose flag
(`-v`) to see all results.


## Loading the `mrs.path` module

The `mrs.path` module is a library of functions, not a script, so import it:

```python
>>> from delphin.mrs import path as mp

```


## Reading and Writing Paths

MRS Paths are a variableless, nodeid-less representation meant primarily
for serialization and deserialization.

First let's read and write some paths.

```python
>>> p1 = mp.read_path('abc')
>>> mp.format_path(p1)
'abc'
>>> p2 = mp.read_path('abc:ARG1/NEQ>def')
>>> mp.format_path(p2)
'abc:ARG1/NEQ>def'
>>> p3 = mp.read_path('abc:ARG1/NEQ>')
>>> mp.format_path(p3)
'abc:ARG1/NEQ>'
>>> mp.format_path(p3, trailing_connectors='never')
'abc'
>>> p4 = mp.read_path('def<ARG1/NEQ:abc')
>>> mp.format_path(p4)
'def<ARG1/NEQ:abc'
>>> p5 = mp.read_path('abc(:ARG1/NEQ>def & :ARG2/EQ>ghi)')
>>> mp.format_path(p5)
'abc(:ARG1/NEQ>def & :ARG2/EQ>ghi)'
>>> p6 = mp.read_path('abc(:ARG1/NEQ>def & <ARG1/EQ:ghi)')
>>> mp.format_path(p6)
'abc(:ARG1/NEQ>def & <ARG1/EQ:ghi)'
>>> p7 = mp.read_path('abc:ARG1/NEQ>def:ARG1/EQ>ghi')
>>> mp.format_path(p7)
'abc:ARG1/NEQ>def:ARG1/EQ>ghi'
>>> p8 = mp.read_path('abc:ARG1/NEQ>def:/EQ:ghi')
>>> mp.format_path(p8)
'abc:ARG1/NEQ>def:/EQ:ghi'

```

The path is a linked list. You can access the first node's properties:

```python
>>> p1.nodeid is None
True
>>> p1.pred.string
'abc'
>>> len(p1.links)
0
>>> p1.depth
0
>>> p1.distance
0

```

And for paths with links, you can traverse through the path:

```python
>>> len(p2.links)
1
>>> p2.links[':ARG1/NEQ>'].pred.string
'def'
>>> p2[':ARG1/NEQ>'].pred.string
'def'
>>> len(p2[':ARG1/NEQ>'].links)
0
>>> p7[':ARG1/NEQ>'][':ARG1/EQ>'].pred.string
'ghi'

```

Subpaths are paths, too:

```python
>>> mp.format_path(p7[':ARG1/NEQ>'])
'def:ARG1/EQ>ghi'

```

Depth is sensitive to the direction of the link, while distance is not:

```python
>>> p6.depth
0
>>> p6.distance
0
>>> p6[':ARG1/NEQ>'].depth
1
>>> p6[':ARG1/NEQ>'].distance
1
>>> p6['<ARG1/EQ:'].depth
-1
>>> p6['<ARG1/EQ:'].distance
1
>>> p7[':ARG1/NEQ>'][':ARG1/EQ>'].depth
2
>>> p7[':ARG1/NEQ>'][':ARG1/EQ>'].distance
2
>>> p8[':ARG1/NEQ>'].depth
1
>>> p8[':ARG1/NEQ>'].distance
1
>>> p8[':ARG1/NEQ>'][':/EQ:'].depth
1
>>> p8[':ARG1/NEQ>'][':/EQ:'].distance
2

```


## Generating Paths

Let's load some Xmrs objects to help with testing:

```python
>>> from delphin.mrs.simplemrs import loads_one
>>> it_rains = loads_one('''
... [ TOP: h0 INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
...   RELS: < [ "_rain_v_1_rel"<3:9> LBL: h1 ARG0: e2 ] >
...   HCONS: < h0 qeq h1 > ]''')
>>>
>>> the_large_dog_barks = loads_one('''
... [ TOP: h0 INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
...   RELS: < [ _the_q_rel<0:3> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: sg IND: + ] RSTR: h5 BODY: h6 ]
...           [ "_large_a_1_rel"<4:9> LBL: h7 ARG0: e8 [ e SF: prop TENSE: untensed MOOD: indicative ] ARG1: x3 ]
...           [ "_dog_n_1_rel"<10:13> LBL: h7 ARG0: x3 ]
...           [ "_bark_v_1_rel"<14:20> LBL: h1 ARG0: e2 ARG1: x3 ] >
...   HCONS: < h0 qeq h1 h5 qeq h7 > ]''')
>>>
>>> dogs_and_cats_sleep = loads_one('''
... [ TOP: h0 INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
...   RELS: < [ udef_q_rel<0:13> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: pl ] RSTR: h5 BODY: h6 ]
...           [ udef_q_rel<0:4> LBL: h7 ARG0: x8 [ x PERS: 3 NUM: pl IND: + ] RSTR: h9 BODY: h10 ]
...           [ "_dog_n_1_rel"<0:4> LBL: h11 ARG0: x8 ]
...           [ _and_c_rel<5:8> LBL: h12 ARG0: x3 L-INDEX: x8 R-INDEX: x13 [ x PERS: 3 NUM: pl IND: + ] ]
...           [ udef_q_rel<9:13> LBL: h14 ARG0: x13 RSTR: h15 BODY: h16 ]
...           [ "_cat_n_1_rel"<9:13> LBL: h17 ARG0: x13 ]
...           [ "_sleep_v_1_rel"<14:20> LBL: h1 ARG0: e2 ARG1: x3 ] >
...   HCONS: < h0 qeq h1 h5 qeq h12 h9 qeq h11 h15 qeq h17 > ]''')
>>>
>>> dogs_sleep_and_bark = loads_one('''
... [ TOP: h0 INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
...   RELS: < [ udef_q_rel<0:4> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: pl IND: + ] RSTR: h5 BODY: h6 ]
...           [ "_dog_n_1_rel"<0:4> LBL: h7 ARG0: x3 ]
...           [ "_sleep_v_1_rel"<5:10> LBL: h8 ARG0: e9 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ] ARG1: x3 ]
...           [ _and_c_rel<11:14> LBL: h1 ARG0: e2 L-INDEX: e9 R-INDEX: e10 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ] L-HNDL: h8 R-HNDL: h11 ]
...           [ "_bark_v_1_rel"<15:20> LBL: h11 ARG0: e10 ARG1: x3 ] >
...   HCONS: < h0 qeq h1 h5 qeq h7 > ]''')
>>>
>>> nearly_all_dogs_bark = loads_one('''
... [ TOP: h0 INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
...   RELS: < [ "_nearly_x_deg_rel"<0:6> LBL: h4 ARG0: e5 [ e SF: prop TENSE: untensed MOOD: indicative PROG: - PERF: - ] ARG1: u6 ]
...           [ _all_q_rel<7:10> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: pl IND: + ] RSTR: h7 BODY: h8 ]
...           [ "_dog_n_1_rel"<11:15> LBL: h9 ARG0: x3 ]
...           [ "_bark_v_1_rel"<16:21> LBL: h1 ARG0: e2 ARG1: x3 ] >
...   HCONS: < h0 qeq h1 h7 qeq h9 > ]''')
>>>
>>> the_dog_whose_tail_wagged_barks = loads_one('''
... [ TOP: h0 INDEX: e2 [ e SF: prop TENSE: past MOOD: indicative PROG: - PERF: - ]
...   RELS: < [ _the_q_rel<0:3> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: sg IND: + ] RSTR: h5 BODY: h6 ]
...           [ "_dog_n_1_rel"<4:7> LBL: h7 ARG0: x3 ]
...           [ def_explicit_q_rel<8:13> LBL: h8 ARG0: x9 [ x PERS: 3 NUM: sg IND: + ] RSTR: h10 BODY: h11 ]
...           [ poss_rel<8:13> LBL: h7 ARG0: e12 [ e SF: prop TENSE: untensed MOOD: indicative PROG: - PERF: - ] ARG1: x9 ARG2: x3 ]
...           [ "_tail_n_1_rel"<14:18> LBL: h13 ARG0: x9 ]
...           [ "_wag_v_1_rel"<19:25> LBL: h7 ARG0: e14 [ e SF: prop TENSE: past MOOD: indicative PROG: - PERF: - ] ARG1: x9 ]
...           [ "_bark_v_1_rel"<26:33> LBL: h1 ARG0: e2 ARG1: x3 ] >
...   HCONS: < h0 qeq h1 h5 qeq h7 h10 qeq h13 > ]''')

```

### Generating Directed Paths

Directed paths can only go in the direction of the arguments, so they
cannot "backtrack" to get quantifiers, modifiers, etc. from their heads.
On the other hand, they are simple tree structures of semantic subgraphs
which may be a useful property for some applications.

```python
>>> mp.find_paths(it_rains, method="directed", allow_eq=False)

```

### Generating Headed Paths