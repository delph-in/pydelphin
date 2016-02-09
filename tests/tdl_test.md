
# Unit tests for the `tdl` module

To run, do this at the command prompt:

    $ python3 -m doctest tests/tdl_test.md

Note: nothing will be shown if tests pass. You can add a verbose flag
(`-v`) to see all results.

## Loading the `tdl` module

The `tdl` module is a library of functions, not a script, so import it:

```python
>>> from delphin import tdl

```

## String Operations

### Tokenization

The `tdl.tokenize()` method breaks up streams of TDL text into the
logical units for parsing.

##### Types and Features

Basic atoms should be tokenized. Some kinds of punctuation are allowed.

```python
>>> list(tdl.tokenize('*top* type-name FEATURE + -'))
['*top*', 'type-name', 'FEATURE', '+', '-']

```

##### Strings

Strings should be kept together until the terminating quote is found
(for double-quoted strings), or until a space or breakable punctuation
is found (for single-open-quoted strings), even if escaped quotation
characters are inside the quote.

```python
>>> list(tdl.tokenize('"string with spaces and \\"quotes\\""'))
['"string with spaces and \\"quotes\\""']
>>> list(tdl.tokenize("'single-open-quote\\'string"))
["'single-open-quote\\'string"]

```

##### Lists

```python
>>> list(tdl.tokenize('< list, items >'))
['<', 'list', ',', 'items', '>']
>>> list(tdl.tokenize('<! diff-list, items !>'))
['<!', 'diff-list', ',', 'items', '!>']
>>> list(tdl.tokenize('< [], ... >'))
['<', '[', ']', ',', '...', '>']
>>> list(tdl.tokenize('< [] . #rest >'))
['<', '[', ']', '.', '#rest', '>']

```

##### Basic Type Definitions

There are at least three assignment operators (`:=`, `:+`, and `:<`).

```python
>>> list(tdl.tokenize('type-name := supertype1.'))
['type-name', ':=', 'supertype1', '.']
>>> list(tdl.tokenize('type-name :+ supertype1.'))
['type-name', ':+', 'supertype1', '.']
>>> list(tdl.tokenize('type-name :< supertype1.'))
['type-name', ':<', 'supertype1', '.']

```

##### Features

Feature paths can be delimited using dots (`.`) or with open brackets
(`[`). In the latter case, a closing bracket (`]`) must terminate the
group of sub-features that share the path prefix:

```python
>>> list(tdl.tokenize('FEATURE [ SUBFEAT val ]'))
['FEATURE', '[', 'SUBFEAT', 'val', ']']
>>> list(tdl.tokenize('FEATURE.SUBFEAT val'))
['FEATURE', '.', 'SUBFEAT', 'val']
>>> list(tdl.tokenize('[ FEATURE [ SUBFEAT1 value, SUBFEAT2 value ] ]'))
['[', 'FEATURE', '[', 'SUBFEAT1', 'value', ',', 'SUBFEAT2', 'value', ']', ']']

```

##### Conjunctions

```python
>>> list(tdl.tokenize('supertype1 & supertype2'))
['supertype1', '&', 'supertype2']
>>> list(tdl.tokenize('supertype1 & [ ATTR val ]'))
['supertype1', '&', '[', 'ATTR', 'val', ']']
>>> list(tdl.tokenize('[ FEATURE < type & [ FEAT + ] > ]'))
['[', 'FEATURE', '<', 'type', '&', '[', 'FEAT', '+', ']', '>', ']']

```

##### Coreference

While it was mostly an arbitrary decision, I chose to keep the hash
character (`#`) on the identifier of the coreference to keep it distinct
from similar type names.

```python
>>> list(tdl.tokenize('#coref'))
['#coref']
>>> list(tdl.tokenize('#coref-tag'))
['#coref-tag']

```

##### Inflectional Rules

Similarly, I chose to keep the bang/exclamation character (`!`) on the
letterset macro:

```python
>>> list(tdl.tokenize('%(letter-set (!v aeiou))'))
['%', '(', 'letter-set', '(', '!v', 'aeiou', ')', ')']

```


## File Operations

TDL code is stored in grammar files, so the more sophisticated parsing
functions, like `tdl.lex()` and `tdl.parse()`, work on file-like
objects. Normally this is an open file:

```python
grammar = tdl.parse(open('mygrammar.tdl', 'r'))
```

Sometimes you may have a string you want to use with these functions.
For example, when running this file as a doctest, or if the code is
being filtered by a program, etc. Python's `io.StringIO()` and
`io.BytesIO()` functions make this easy. Use `io.StringIO()` for
unicode data (regular strings in Python 3 or `unicode` objects in
Python 2), and `io.BytesIO()` for byte strings (`bytes` objects in
Python 3 or `str` objects in Python 2). To help this file run as a
doctest for both Python 2 and 3, I define the following function:

```python
>>> from io import StringIO, BytesIO
>>> from delphin.lib.six import PY3
>>> file_from_string = StringIO if PY3 else BytesIO

```

### Lexing

After tokenization, the next step is to group related tokens
and classify the group by its purpose. The `tdl.lex()` function does
that.

For convenience:

```python
>>> def lex(s): return list(tdl.lex(file_from_string(s)))

```

##### Type Definitions

Type definitions can be simple type hierarchies, type and feature
definitions, type addenda, or affixing inflectional rules.

```python
>>> lex('type-name := supertype.')
[(1, 'TYPEDEF', ['type-name', ':=', 'supertype', '.'])]
>>> lex('''t := st &
...   [ X v ].''')
[(1, 'TYPEDEF', ['t', ':=', 'st', '&', '[', 'X', 'v', ']', '.'])]
>>> lex('''t := st &
...   [ X.Y v ].''')
[(1, 'TYPEDEF', ['t', ':=', 'st', '&', '[', 'X', '.', 'Y', 'v', ']', '.'])]
>>> lex('t :+ [ X v ].')
[(1, 'TYPEDEF', ['t', ':+', '[', 'X', 'v', ']', '.'])]
>>> lex('''ir :=
...   %suffix (a b)
...   st & [ X.Y v ].''')  # doctest: +NORMALIZE_WHITESPACE
[(1, 'TYPEDEF', ['ir', ':=', '%suffix', '(', 'a', 'b', ')', 'st', '&',
 '[', 'X', '.', 'Y', 'v', ']', '.'])]

```

##### Comments

Comments can be on a single line or span multiple lines:

```python
>>> lex('; semicolon comment')
[(1, 'LINECOMMENT', '; semicolon comment')]
>>> lex('#| block comment |#')
[(1, 'BLOCKCOMMENT', '#| block comment |#')]
>>> lex('''#| multiline
... contained
... comment |#''')
[(1, 'BLOCKCOMMENT', '#| multiline\ncontained\ncomment |#')]

```

##### Lettersets

Letter sets function like macros for affixing rules.

```python
>>> lex('%(letter-set (!v aeiou))')
[(1, 'LETTERSET', ['%', '(', 'letter-set', '(', '!v', 'aeiou', ')', ')'])]

```


## Type Parsing

The `tdl.parse()` function will take an open file of TDL code and
produce an in-memory representation of the data structures. The basic
data structure is a `TdlDefinition` object, which only contains a list
of supertypes and features. The values of features are often other
`TdlDefinition` objects. A `TdlType` object is a special kind of
`TdlDefinition` that has an identifier, a list of coreferences, and
possibly a comment (from a docstring). The `tdl.parse()` function will
return a `TdlType` object for every type definition in the file.

For convenience:

```python
>>> def parsetdl(s): return next(tdl.parse(file_from_string(s)))

```

##### Basic Subtyping

```python
>>> t = parsetdl('type-name := supertype.')
>>> t.identifier
'type-name'
>>> t.supertypes
['supertype']
>>> t = parsetdl('type := super1 & super2.')
>>> t.identifier
'type'
>>> t.supertypes
['super1', 'super2']

```

##### Basic Features

An AVM with no features:

```python
>>> t = parsetdl('type := super & [].')
>>> list(t.features())  # doctest: +ELLIPSIS
[]

```

Simple feature and value; attribute names are case-insensitive:

```python
>>> t = parsetdl('type := super & [ ATTR val ].')
>>> list(t.features())  # doctest: +ELLIPSIS
[('ATTR', <TdlDefinition object ...>)]
>>> t['ATTR'].supertypes
['val']
>>> t['attr'].supertypes
['val']

```

String values are primitives:

```python
>>> t = parsetdl('type := super & [ ATTR "val" ].')
>>> list(t.features())  # doctest: +ELLIPSIS
[('ATTR', '"val"')]
>>> t = parsetdl("type := super & [ ATTR 'val ].")
>>> list(t.features())  # doctest: +ELLIPSIS
[('ATTR', "'val")]

```

Integer values, however, are not primitives:

```python
>>> t = parsetdl('type := super & [ ATTR 1 ].')
>>> list(t.features())  # doctest: +ELLIPSIS
[('ATTR', <TdlDefinition object ...>)]

```

Dot-delimited feature nesting; `features()` and `local_constraints()` do
the same thing when feature values are simple; and sub-features can be
retrieved using either dot-notation or as separate keys:

```python
>>> t = parsetdl('type := super & [ ATTR.SUB val ].')
>>> list(t.features())  # doctest: +ELLIPSIS
[('ATTR.SUB', <TdlDefinition object ...>)]
>>> list(t.local_constraints())  # doctest: +ELLIPSIS
[('ATTR.SUB', <TdlDefinition object ...>)]
>>> list(t['ATTR'].features())  # doctest: +ELLIPSIS
[('SUB', <TdlDefinition object ...>)]
>>> t['ATTR'].supertypes
[]
>>> t['ATTR.SUB'].supertypes
['val']
>>> t['ATTR']['SUB'].supertypes
['val']

```

Sub-AVM feature nesting; again, `features()` and `local_constraints()`
do the same thing when the feature values are simple:

```python
>>> t = parsetdl('type := super & [ ATTR [ SUB val ] ].')
>>> list(t.features())  # doctest: +ELLIPSIS
[('ATTR.SUB', <TdlDefinition object ...>)]
>>> list(t.local_constraints())  # doctest: +ELLIPSIS
[('ATTR.SUB', <TdlDefinition object ...>)]
>>> list(t['ATTR'].features())  # doctest: +ELLIPSIS
[('SUB', <TdlDefinition object ...>)]
>>> t['ATTR'].supertypes
[]
>>> t['ATTR.SUB'].supertypes
['val']
>>> t['ATTR']['SUB'].supertypes
['val']

```

Multiple features on an AVM:

```python
>>> t = parsetdl('type := super & [ ATTR1 val1, ATTR2 val2 ].')
>>> sorted(t.features())  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
[('ATTR1', <TdlDefinition object ...>),
 ('ATTR2', <TdlDefinition object ...>)]

```

Multiple features on a sub-AVM only returns the top level:

```python
>>> t = parsetdl('type := super & [ ATTR [ SUB1 val1, SUB2 val2 ] ].')
>>> sorted(t.features())  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
[('ATTR', <TdlDefinition object ...>)]

```

The `in` operator works with keys, even dot-delimited ones, but not
for supertypes:

```python
>>> t = parsetdl('type := super & [ ATTR.SUB val ].')
>>> 'ATTR' in t
True
>>> 'ATTR.SUB' in t
True
>>> 'SUB' in t
False
>>> 'SUB' in t['ATTR']
True
>>> 'super' in t
False

```

Features can be set with the standard Python syntax:

```python
>>> t = parsetdl('type := super & [ ATTR val ].')
>>> t['ATTR'].supertypes
['val']
>>> t['ATTR'] = "string"
>>> t['ATTR']
'string'
>>> t['ATTR1.ATTR2'] = "string"
>>> t['ATTR1']  # doctest: +ELLIPSIS
<TdlDefinition object...>
>>> t['ATTR1.ATTR2']
'string'

```

##### Features with Supertypes

The `features()` function stops when a value with a supertype is found,
but the `local_constraints()` function retrieves the full paths of all
constraints on the type:

```python
>>> t = parsetdl('type := super & [ ATTR t & [ SUB val ] ].')
>>> t.supertypes
['super']
>>> t['ATTR'].supertypes
['t']
>>> t['ATTR.SUB'].supertypes
['val']
>>> list(t.features())  # doctest: +ELLIPSIS
[('ATTR', <TdlDefinition object ...>)]
>>> list(t.local_constraints())  # doctest: +ELLIPSIS
[('ATTR.SUB', <TdlDefinition object ...>)]

```

##### Normal Lists

Empty lists return `None` (an thus cannot be further specified with
values later):

```python
>>> t = parsetdl('type := super & [ ATTR < > ].')
>>> list(t.features())
[('ATTR', None)]
>>> list(t.local_constraints())
[('ATTR', None)]
>>> t['ATTR'] is None
True

```

Single, bounded (terminated) list---the last item is `None`:

```python
>>> t = parsetdl('type := super & [ ATTR < a > ].')
>>> sorted(t['ATTR'].features())  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
[('FIRST', <TdlDefinition object ...>),
 ('REST', None)]

```

Single list item with features:

```python
>>> t = parsetdl('type := super & [ ATTR < a & [ SUB val ] > ].')
>>> sorted(t['ATTR'].features())  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
[('FIRST', <TdlDefinition object ...>),
 ('REST', None)]
>>> list(t['ATTR.FIRST'].features())  # doctest: +ELLIPSIS
[('SUB', <TdlDefinition object ...>)]
>>> t['ATTR.FIRST.SUB'].supertypes
['val']

```

Bounded list with multiple items:

```python
>>> t = parsetdl('type := super & [ ATTR < a, b > ].')
>>> sorted(t['ATTR'].features())  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
[('FIRST', <TdlDefinition object ...>),
 ('REST', <TdlDefinition object ...>)]
>>> sorted(t['ATTR.REST'].features())  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
[('FIRST', <TdlDefinition object ...>),
 ('REST', None)]

```

Simple unbounded list:

```python
>>> t = parsetdl('type := super & [ ATTR < ... > ].')
>>> sorted(t.features())  # doctest: +ELLIPSIS
[('ATTR', <TdlDefinition object ...>)]

```

Unbounded list with an initial item:

```python
>>> t = parsetdl('type := super & [ ATTR < a, ... > ].')
>>> sorted(t.features())  # doctest: +ELLIPSIS
[('ATTR.FIRST', <TdlDefinition object ...>)]

```

A dot (`.`), instead of a comma, delimiter allows access to the final
`REST` feature path (for coreferencing).

```python
>>> t = parsetdl('type := super & [ ATTR1 < a . #rest >, ATTR2 #rest ].')
>>> sorted(t.features())  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
[('ATTR1', <TdlDefinition object ...>),
 ('ATTR2', <TdlDefinition object ...>)]
>>> sorted(t['ATTR1'].features())  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
[('FIRST', <TdlDefinition object ...>),
 ('REST', <TdlDefinition object ...>)]
>>> t.coreferences
[('#rest', ['ATTR1.REST', 'ATTR2'])]

```

##### Diff Lists

Empty diff lists link the `LIST` path to the `LAST` path:

```python
>>> t = parsetdl('type := super & [ ATTR <! !> ].')
>>> sorted(t['ATTR'].features())  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
[('LAST', <TdlDefinition object ...>),
 ('LIST', <TdlDefinition object ...>)]
>>> t.coreferences
[(None, ['ATTR.LIST', 'ATTR.LAST'])]

```

Diff list with one item; `LAST` is coref'd to the position after the
item:

```python
>>> t = parsetdl('type := super & [ ATTR <! a !> ].')
>>> sorted(t['ATTR'].features())  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
[('LAST', <TdlDefinition object ...>),
 ('LIST.FIRST', <TdlDefinition object ...>)]
>>> t.coreferences
[(None, ['ATTR.LIST.REST', 'ATTR.LAST'])]

```

Multiple items on a diff list; same behavior as above:

```python
>>> t = parsetdl('type := super & [ ATTR <! a, b !> ].')
>>> sorted(t['ATTR'].features())  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
[('LAST', <TdlDefinition object ...>),
 ('LIST', <TdlDefinition object ...>)]
>>> sorted(t['ATTR.LIST'].features())  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
[('FIRST', <TdlDefinition object ...>),
 ('REST.FIRST', <TdlDefinition object ...>)]
>>> t.coreferences
[(None, ['ATTR.LIST.REST.REST', 'ATTR.LAST'])]

```
