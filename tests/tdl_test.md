

```python
>>> from delphin import tdl

```

Tokenization
============

Types and Features
------------------

```python
>>> list(tdl.tokenize('*top* type-name FEATURE + -'))
['*top*', 'type-name', 'FEATURE', '+', '-']

```

Strings
-------

```python
>>> list(tdl.tokenize('"string with spaces and \\"quotes\\""'))
['"string with spaces and \\"quotes\\""']
>>> list(tdl.tokenize("'single-open-quote\\'string"))
["'single-open-quote\\'string"]

```

Lists
-----

```python
>>> list(tdl.tokenize('< list, items >'))
['<', 'list', ',', 'items', '>']
>>> list(tdl.tokenize('<! diff-list, items !>'))
['<!', 'diff-list', ',', 'items', '!>']
>>> list(tdl.tokenize('< ..., [] >'))
['<', '...', ',', '[', ']', '>']
>>> list(tdl.tokenize('< [] . #rest >'))
['<', '[', ']', '.', '#rest', '>']

```

Basic Type Definitions
----------------------

```python
>>> list(tdl.tokenize('type-name := supertype1.'))
['type-name', ':=', 'supertype1', '.']
>>> list(tdl.tokenize('type-name :+ supertype1.'))
['type-name', ':+', 'supertype1', '.']
>>> list(tdl.tokenize('type-name :< supertype1.'))
['type-name', ':<', 'supertype1', '.']

```

Features
--------

```python
>>> list(tdl.tokenize('FEATURE [ SUBFEAT val ]'))
['FEATURE', '[', 'SUBFEAT', 'val', ']']
>>> list(tdl.tokenize('FEATURE.SUBFEAT val'))
['FEATURE', '.', 'SUBFEAT', 'val']
>>> list(tdl.tokenize('[ FEATURE [ SUBFEAT1 value, SUBFEAT2 value ] ]'))
['[', 'FEATURE', '[', 'SUBFEAT1', 'value', ',', 'SUBFEAT2', 'value', ']', ']']

```

Conjunctions
------------

```python
>>> list(tdl.tokenize('supertype1 & supertype2'))
['supertype1', '&', 'supertype2']
>>> list(tdl.tokenize('supertype1 & [ ATTR val ]'))
['supertype1', '&', '[', 'ATTR', 'val', ']']
>>> list(tdl.tokenize('[ FEATURE < type & [ FEAT + ] > ]'))
['[', 'FEATURE', '<', 'type', '&', '[', 'FEAT', '+', ']', '>', ']']

```

Coreference
-----------

```python
>>> list(tdl.tokenize('#coref'))
['#coref']
>>> list(tdl.tokenize('#coref-tag'))
['#coref-tag']

```

Inflectional Rules
------------------

```python
>>> list(tdl.tokenize('%(letter-set (!v aeiou))'))
['%', '(', 'letter-set', '(', '!v', 'aeiou', ')', ')']

```


Lexing
======

For convenience:

```python
>>> from io import StringIO
>>> lex = lambda s: list(tdl.lex(StringIO(s)))

```

Type Definitions
----------------

```python
>>> lex('type-name := supertype.')
[(1, 'TYPEDEF', ['type-name', ':=', 'supertype', '.'])]
>>> lex('''t := st &
...   [ X v ].''')
[(1, 'TYPEDEF', ['t', ':=', 'st', '&', '[', 'X', 'v', ']', '.'])]
>>> lex('''t := st &
...   [ X.Y v ].''')
[(1, 'TYPEDEF', ['t', ':=', 'st', '&', '[', 'X', '.', 'Y', 'v', ']', '.'])]
>>> lex('''ir :=
...   %suffix (a b)
...   st & [ X.Y v ].''')  # doctest: +NORMALIZE_WHITESPACE
[(1, 'TYPEDEF', ['ir', ':=', '%suffix', '(', 'a', 'b', ')', 'st', '&',
 '[', 'X', '.', 'Y', 'v', ']', '.'])]

```

Comments
--------

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

Lettersets
----------

```python
>>> lex('%(letter-set (!v aeiou))')
[(1, 'LETTERSET', ['%', '(', 'letter-set', '(', '!v', 'aeiou', ')', ')'])]

```


Type Parsing
============

For convenience:

```python
>>> parsetdl = lambda s: next(tdl.parse(StringIO(s)))

```

Basic Subtyping
---------------

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

Basic Features
--------------

```python
>>> t = parsetdl('type := super & [ ATTR val ].')
>>> list(t.features())  # doctest: +ELLIPSIS
[('ATTR', <TdlDefinition object ...>)]
>>> t['ATTR'].supertypes
['val']
>>> t['attr'].supertypes
['val']

```

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

```python
>>> t = parsetdl('type := super & [ ATTR1 val1, ATTR2 val2 ].')
>>> sorted(t.features())  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
[('ATTR1', <TdlDefinition object (val1) ...>),
 ('ATTR2', <TdlDefinition object (val2) ...>)]

```

```python
>>> t = parsetdl('type := super & [ ATTR [ SUB1 val1, SUB2 val2 ] ].')
>>> sorted(t.features())  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
[('ATTR.SUB1', <TdlDefinition object (val1) ...>),
 ('ATTR.SUB2', <TdlDefinition object (val2) ...>)]

```

Features with Supertypes
------------------------

```python
>>> t = parsetdl('type := super & [ ATTR t & [ SUB val ] ].')
>>> t.supertypes
['super']
>>> t['ATTR'].supertypes
['t']
>>> t['ATTR.SUB'].supertypes
['val']
>>> list(t.features())  # doctest: +ELLIPSIS
[('ATTR', <TdlDefinition object (t) ...>)]
>>> list(t.local_constraints())  # doctest: +ELLIPSIS
[('ATTR.SUB', <TdlDefinition object (val) ...>)]

```

Normal Lists
------------

```python
>>> t = parsetdl('type := super & [ ATTR < > ].')
>>> list(t.features())
[('ATTR', None)]
>>> list(t.local_constraints())
[('ATTR', None)]
>>> t['ATTR'] is None
True

```

```python
>>> t = parsetdl('type := super & [ ATTR < a > ].')
>>> sorted(t.features())  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
[('ATTR.FIRST', <TdlDefinition object (a) ...>),
 ('ATTR.REST', None)]

```

```python
>>> t = parsetdl('type := super & [ ATTR < a & [ SUB val ] > ].')
>>> sorted(t.features())  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
[('ATTR.FIRST', <TdlDefinition object (a) ...>),
 ('ATTR.REST', None)]
>>> list(t['ATTR.FIRST'].features())  # doctest: +ELLIPSIS
[('SUB', <TdlDefinition object (val) ...>)]
>>> t['ATTR.FIRST.SUB'].supertypes
['val']

```

```python
>>> t = parsetdl('type := super & [ ATTR < a, b > ].')
>>> sorted(t.features())  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
[('ATTR.FIRST', <TdlDefinition object (a) ...>),
 ('ATTR.REST.FIRST', <TdlDefinition object (b) ...>),
 ('ATTR.REST.REST', None)]

```

```python
>>> t = parsetdl('type := super & [ ATTR < ... > ].')
>>> sorted(t.features())  # doctest: +ELLIPSIS
[('ATTR', <TdlDefinition object ...>)]

```

```python
>>> t = parsetdl('type := super & [ ATTR < a, ... > ].')
>>> sorted(t.features())  # doctest: +ELLIPSIS
[('ATTR.FIRST', <TdlDefinition object (a) ...>)]

```

```python
>>> t = parsetdl('type := super & [ ATTR < a . #rest > ].')
>>> sorted(t.features())  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
[('ATTR.FIRST', <TdlDefinition object (a) ...>),
 ('ATTR.REST', <TdlDefinition object ...>)]
>>> t.coreferences
[('#rest', 'ATTR.REST')]

```
