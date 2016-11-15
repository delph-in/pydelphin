
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


## Reading and Writing Basic Paths

MRS Paths are a variableless, nodeid-less representation meant primarily
for serialization and deserialization.

First let's read and write some paths. Basic paths have predicates with axes
that point to other predicates (or to nothing).

The `read_path()` function parses a string into an `XmrsPathNode` object,
while `format()` serializes an `XmrsPathNode` object to a string.

```python
>>> p1 = mp.read_path('abc')
>>> mp.format(p1)
'abc'
>>> p2 = mp.read_path('abc:ARG1/NEQ>def')
>>> mp.format(p2)
'abc:ARG1/NEQ>def'
>>> p3 = mp.read_path('abc:ARG1/NEQ>')
>>> mp.format(p3)
'abc:ARG1/NEQ>'

```

Some more complicated paths have reversed axes, multiple axes, undirected
axes, or compound axes (when two or more axes point to the same target pred).

```
>>> p4 = mp.read_path('def<ARG1/NEQ:abc')
>>> mp.format(p4)
'def<ARG1/NEQ:abc'
>>> p5 = mp.read_path('abc(:ARG1/NEQ>def & :ARG2/EQ>ghi)')
>>> mp.format(p5)
'abc(:ARG1/NEQ>def & :ARG2/EQ>ghi)'
>>> p6 = mp.read_path('abc(:ARG1/NEQ>def & <ARG1/EQ:ghi)')
>>> mp.format(p6)
'abc(:ARG1/NEQ>def & <ARG1/EQ:ghi)'
>>> p7 = mp.read_path('abc:ARG1/NEQ>def:ARG1/EQ>ghi')
>>> mp.format(p7)
'abc:ARG1/NEQ>def:ARG1/EQ>ghi'
>>> p8 = mp.read_path('abc:ARG1/NEQ>def:/EQ:ghi')
>>> mp.format(p8)
'abc:ARG1/NEQ>def:/EQ:ghi'
>>> p9 = mp.read_path('abc:ARG1/NEQ&ARG2/NEQ>def')
>>> mp.format(p9)
'abc:ARG1/NEQ&ARG2/NEQ>def'

```


## Rich Paths and Flags

Beyond predicates and axes, paths can have other kinds of information:

* nodeids
* context
  - variable sorts
  - variable properties
  - contextual subpaths
* constant arguments
* underspecified (star \*) predicates

In order to customize what values are stored or printed, flags may be used.
Here is a table of flags:

| Flag             | Short form | Description/Example                         |
| ---------------- | ---------- | ------------------------------------------- |
| `NODEID`         | `NID`      | `pred#123`                                  |
| `PRED`           | `P`        | `pred`                                      |
| `VARSORT`        | `VS`       | `pred[x]`                                   |
| `VARPROPS`       | `VP`       | `pred[PROP=val]`                            |
| `OUTAXES`        | `OUT`      | `pred:ARG1/NEQ>`                            |
| `INAXES`         | `IN`       | `pred<ARG1/EQ:`                             |
| `UNDIRECTEDAXES` | `UND`      | `pred:/EQ:`                                 |
| `SUBPATHS`       | `SP`       | `pred:ARG1/NEQ>pred2`                       |
| `CARG`           | `C`        | `pred:CARG>"constant"`                      |
| `BALANCED`       | `B`        | all AXES on a pred have subpaths or none do |

There are also some convenient composed flags:

| Flag      | Unification                 |
| --------- | --------------------------- |
| `CONTEXT` | `VS|VP|SP`                  |
| `ALLAXES` | `OUT|IN|UND`                |
| `DEFAULT` | `P|VS|VP|OUT|IN|SP`         |
| `ALL`     | `NID|P|VS|VP|OUT|IN|UND|SP` |

Note that `SUBPATHS` is used both for context and regular subpaths.

Nodeids occur after, or instead of, a predicate. Note that nodeids are not
output by default.

```python
>>> p10 = mp.read_path('abc#1')
>>> mp.format(p10)
'abc'
>>> mp.format(p10, flags=mp.ALL)
'abc#1'
>>> p11 = mp.read_path('#1')
>>> mp.format(p11)
'*'
>>> mp.format(p11, flags=mp.ALL)
'#1'

```

Variable sorts and properties appear in square brackets after the pred and/or
nodeid, but before the axes. Property names must be prefixed with `@`.
Conjunctions of variable sort and/or properties is done with `&` as with
subpaths.

```python
>>> p12 = mp.read_path('abc[x]')
>>> mp.format(p12)
'abc[x]'
>>> p13 = mp.read_path('abc#1[x & @ATTR=val & @PROP=val]')
>>> mp.format(p13, flags=mp.ALL)
'abc#1[x & @ATTR=val & @PROP=val]'
>>> mp.format(p13, flags=mp.DEFAULT - mp.VS)
'abc[@ATTR=val & @PROP=val]'
>>> mp.format(p13, flags=mp.DEFAULT - mp.VP)
'abc[x]'
>>> mp.format(p13, flags=mp.DEFAULT - mp.CONTEXT)
'abc'
>>> p14 = mp.read_path('abc[@ATTR=val]:ARG1/NEQ>def')
>>> mp.format(p14)
'abc[@ATTR=val]:ARG1/NEQ>def'
>>> mp.format(p14, flags=mp.DEFAULT - mp.SP)
'abc[@ATTR=val]:ARG1/NEQ>'
>>> mp.format(p14, flags=mp.DEFAULT - mp.OUT)
'abc[@ATTR=val]:ARG1/NEQ>def'
>>> mp.format(p14, flags=mp.DEFAULT - mp.SP - mp.OUT)
'abc[@ATTR=val]'

```

## Properties of XmrsPathNodes

Paths have an order and depth; order is the number of predicates in a
path, while depth is the largest number of steps from the top to a leaf.

```python
>>> p1.order(), p1.depth()
(1, 0)
>>> p2.order(), p2.depth()
(2, 1)
>>> p3.order(), p3.depth()
(1, 0)
>>> p4.order(), p4.depth()
(2, 1)
>>> p5.order(), p5.depth()
(3, 1)
>>> p6.order(), p6.depth()
(3, 1)
>>> p7.order(), p7.depth()
(3, 2)
>>> p8.order(), p8.depth()
(3, 2)
>>> p9.order(), p9.depth()
(2, 1)

```

Each path is like a linked list (linked tree, rather), so the objects returned
from `read_path()` are nodes, and the `links` attribute on each node connect
it to other nodes. Key access on the node itself acts like querying the links.
This makes it convenient for traversing through the path.

```python
>>> str(p1.pred)
'abc'
>>> len(p1.links)
0
>>> len(p2.links)
1
>>> str(p2.links[':ARG1/NEQ>'].pred)
'def'
>>> str(p2[':ARG1/NEQ>'].pred)
'def'
>>> str(p6['<ARG1/EQ:'].pred)
'ghi'
>>> str(p7[':ARG1/NEQ>'][':ARG1/EQ>'].pred)
'ghi'

```


## Generating Paths

For simplicity, only the preds, axes, and subpaths are printed below:

```python
>>> SIMPLEFLAGS = mp.PRED | mp.SUBPATHS | mp.OUTAXES

```

First let's load some Xmrs objects to help with testing:

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

### Generating Top-down Paths

Top-down paths can only go in the direction of the arguments, so they
cannot "backtrack" to get quantifiers, modifiers, etc. from their heads.
On the other hand, they are simple tree structures of semantic subgraphs
which may be a useful property for some applications.

```python
>>> def topdown_paths(x):
...     for p in mp.explore(x, method='top-down'):
...         yield mp.format(p, flags=SIMPLEFLAGS)
... 
>>> for path in sorted(topdown_paths(it_rains)):
...     print(path)
"_rain_v_1_rel"
TOP:/H>"_rain_v_1_rel"
>>>
>>> for path in sorted(topdown_paths(the_large_dog_barks)):
...     print(path)
"_bark_v_1_rel":ARG1/NEQ>
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"
"_dog_n_1_rel"
"_large_a_1_rel":ARG1/EQ>
"_large_a_1_rel":ARG1/EQ>"_dog_n_1_rel"
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"
_the_q_rel:RSTR/H>
_the_q_rel:RSTR/H>"_dog_n_1_rel"
>>>
>>> for path in sorted(topdown_paths(nearly_all_dogs_bark)):
...     print(path)
"_bark_v_1_rel":ARG1/NEQ>
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"
"_dog_n_1_rel"
"_nearly_x_deg_rel":MOD/EQ>
"_nearly_x_deg_rel":MOD/EQ>_all_q_rel:RSTR/H>
"_nearly_x_deg_rel":MOD/EQ>_all_q_rel:RSTR/H>"_dog_n_1_rel"
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"
_all_q_rel:RSTR/H>
_all_q_rel:RSTR/H>"_dog_n_1_rel"

```


```python
>>> def topdown_paths_with_eq(x):
...     for p in mp.explore(x, method='top-down', flags=mp.DEFAULT|mp.UND):
...         yield mp.format(p, flags=SIMPLEFLAGS)
... 
>>> for path in sorted(topdown_paths_with_eq(nearly_all_dogs_bark)):
...     print(path)
"_bark_v_1_rel":ARG1/NEQ>
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"
"_dog_n_1_rel"
"_nearly_x_deg_rel":MOD/EQ>
"_nearly_x_deg_rel":MOD/EQ>_all_q_rel:RSTR/H>
"_nearly_x_deg_rel":MOD/EQ>_all_q_rel:RSTR/H>"_dog_n_1_rel"
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"
_all_q_rel:RSTR/H>
_all_q_rel:RSTR/H>"_dog_n_1_rel"
>>>
>>> for path in sorted(topdown_paths_with_eq(the_dog_whose_tail_wagged_barks)):
...     print(path)
"_bark_v_1_rel":ARG1/NEQ>
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"
"_dog_n_1_rel"
"_tail_n_1_rel"
"_wag_v_1_rel"(:ARG1/NEQ> & :MOD/EQ>"_dog_n_1_rel")
"_wag_v_1_rel"(:ARG1/NEQ> & :MOD/EQ>)
"_wag_v_1_rel"(:ARG1/NEQ>"_tail_n_1_rel" & :MOD/EQ>"_dog_n_1_rel")
"_wag_v_1_rel"(:ARG1/NEQ>"_tail_n_1_rel" & :MOD/EQ>)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"
_the_q_rel:RSTR/H>
_the_q_rel:RSTR/H>"_dog_n_1_rel"
def_explicit_q_rel:RSTR/H>
def_explicit_q_rel:RSTR/H>"_tail_n_1_rel"
poss_rel(:ARG1/NEQ> & :ARG2/EQ>"_dog_n_1_rel")
poss_rel(:ARG1/NEQ> & :ARG2/EQ>)
poss_rel(:ARG1/NEQ>"_tail_n_1_rel" & :ARG2/EQ>"_dog_n_1_rel")
poss_rel(:ARG1/NEQ>"_tail_n_1_rel" & :ARG2/EQ>)

```

### Generating Bottom-up Paths

```python
>>> def bottomup_paths(x):
...     for p in mp.explore(x, method='bottom-up'):
...         yield mp.format(p, flags=SIMPLEFLAGS)
... 
>>> for path in sorted(bottomup_paths(it_rains)):
...     print(path)
"_rain_v_1_rel"
"_rain_v_1_rel"</H:TOP
>>>
>>> for path in sorted(bottomup_paths(the_large_dog_barks)):
...     print(path)
"_bark_v_1_rel"
"_bark_v_1_rel"</H:TOP
"_dog_n_1_rel"
"_dog_n_1_rel"(<ARG1/EQ:"_large_a_1_rel" & <ARG1/NEQ:"_bark_v_1_rel" & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG1/EQ:"_large_a_1_rel" & <ARG1/NEQ:"_bark_v_1_rel")
"_dog_n_1_rel"(<ARG1/EQ:"_large_a_1_rel" & <ARG1/NEQ:"_bark_v_1_rel"</H:TOP & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG1/EQ:"_large_a_1_rel" & <ARG1/NEQ:"_bark_v_1_rel"</H:TOP)
"_dog_n_1_rel"(<ARG1/EQ:"_large_a_1_rel" & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG1/NEQ:"_bark_v_1_rel" & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG1/NEQ:"_bark_v_1_rel"</H:TOP & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"<ARG1/EQ:"_large_a_1_rel"
"_dog_n_1_rel"<ARG1/NEQ:"_bark_v_1_rel"
"_dog_n_1_rel"<ARG1/NEQ:"_bark_v_1_rel"</H:TOP
"_dog_n_1_rel"<RSTR/H:_the_q_rel
"_large_a_1_rel"
_the_q_rel

```

### Generating Headed Paths

DMRS links for modifiers and quantifiers go TO the noun, not from, so
it's not possible to get a strictly top-down path from the TOP to a
quantifier or modifier. Headed paths make quantifiers and modifiers go
backwards, while all others go forwards, in order to capture these
structures.

```python
>>> def headed_paths(x):
...     for p in mp.explore(x, method='headed'):
...         yield mp.format(p, flags=SIMPLEFLAGS)
... 
>>> for path in sorted(headed_paths(the_large_dog_barks)):
...     print(path)
"_bark_v_1_rel":ARG1/NEQ>
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG1/EQ:"_large_a_1_rel" & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<ARG1/EQ:"_large_a_1_rel"
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<RSTR/H:_the_q_rel
"_dog_n_1_rel"
"_dog_n_1_rel"(<ARG1/EQ:"_large_a_1_rel" & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"<ARG1/EQ:"_large_a_1_rel"
"_dog_n_1_rel"<RSTR/H:_the_q_rel
"_large_a_1_rel"
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG1/EQ:"_large_a_1_rel" & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<ARG1/EQ:"_large_a_1_rel"
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<RSTR/H:_the_q_rel
_the_q_rel
>>>
>>> for path in sorted(headed_paths(the_dog_whose_tail_wagged_barks)):
...     print(path)
"_bark_v_1_rel":ARG1/NEQ>
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel")
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel")
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel")
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<ARG2/EQ:poss_rel:ARG1/NEQ>
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<RSTR/H:_the_q_rel
"_dog_n_1_rel"
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel")
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel")
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel")
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"<ARG2/EQ:poss_rel:ARG1/NEQ>
"_dog_n_1_rel"<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"
"_dog_n_1_rel"<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel
"_dog_n_1_rel"<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>
"_dog_n_1_rel"<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"
"_dog_n_1_rel"<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel
"_dog_n_1_rel"<RSTR/H:_the_q_rel
"_tail_n_1_rel"
"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel
"_wag_v_1_rel":ARG1/NEQ>
"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"
"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel")
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel")
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel")
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<ARG2/EQ:poss_rel:ARG1/NEQ>
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<RSTR/H:_the_q_rel
_the_q_rel
def_explicit_q_rel
poss_rel:ARG1/NEQ>
poss_rel:ARG1/NEQ>"_tail_n_1_rel"
poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel

```

Using `UNDIRECTEDAXES` on `explore()` with headed paths can sometimes yield
many many paths:

```python
>>> def headed_paths_with_eq(x):
...     for p in mp.explore(x, method='headed', flags=mp.DEFAULT|mp.UND):
...         yield mp.format(p, flags=SIMPLEFLAGS)
... 
>>> for path in sorted(headed_paths_with_eq(the_dog_whose_tail_wagged_barks)):
...     print(path)
"_bark_v_1_rel":ARG1/NEQ>
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel")
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel")
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel")
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<ARG2/EQ:poss_rel:ARG1/NEQ>
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<RSTR/H:_the_q_rel
"_dog_n_1_rel"
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel")
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel")
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel")
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"<ARG2/EQ:poss_rel:ARG1/NEQ>
"_dog_n_1_rel"<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"
"_dog_n_1_rel"<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel
"_dog_n_1_rel"<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>
"_dog_n_1_rel"<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"
"_dog_n_1_rel"<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel
"_dog_n_1_rel"<RSTR/H:_the_q_rel
"_tail_n_1_rel"
"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel
"_wag_v_1_rel":ARG1/NEQ>
"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"
"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel")
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel")
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel")
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<ARG2/EQ:poss_rel:ARG1/NEQ>
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"<RSTR/H:_the_q_rel
_the_q_rel
def_explicit_q_rel
poss_rel:ARG1/NEQ>
poss_rel:ARG1/NEQ>"_tail_n_1_rel"
poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel

```

Using the `BALANCED` flag can cut down some of the variants:

```python
>>> def balanced_headed_paths_with_eq(x):
...     for p in mp.explore(x, method='headed', flags=mp.DEFAULT|mp.UND|mp.B):
...         yield mp.format(p, flags=SIMPLEFLAGS)
... 
>>> for path in sorted(balanced_headed_paths_with_eq(the_dog_whose_tail_wagged_barks)):
...     print(path)
"_bark_v_1_rel":ARG1/NEQ>
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
"_tail_n_1_rel"
"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel
"_wag_v_1_rel":ARG1/NEQ>
"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"
"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ> & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel" & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ> & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel" & <RSTR/H:_the_q_rel)
TOP:/H>"_bark_v_1_rel":ARG1/NEQ>"_dog_n_1_rel"(<ARG2/EQ:poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <MOD/EQ:"_wag_v_1_rel":ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel & <RSTR/H:_the_q_rel)
_the_q_rel
def_explicit_q_rel
poss_rel:ARG1/NEQ>
poss_rel:ARG1/NEQ>"_tail_n_1_rel"
poss_rel:ARG1/NEQ>"_tail_n_1_rel"<RSTR/H:def_explicit_q_rel

```
