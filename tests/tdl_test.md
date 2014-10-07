

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
['#', 'coref']
>>> list(tdl.tokenize('#coref-tag'))
['#', 'coref-tag']

```

Inflectional Rules
------------------

```python
>>> list(tdl.tokenize('%(letter-set (!v aeiou))'))
['%', '(', 'letter-set', '(', '!', 'v', 'aeiou', ')', ')']

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
[(1, 'LETTERSET', ['%', '(', 'letter-set', '(', '!', 'v', 'aeiou', ')', ')'])]

```


Type Parsing
============

For convenience:

```python
>>> parse = lambda s: tdl.parse(StringIO(s))

```

Basic Subtyping
---------------

```python
>>> next(parse('type-name := supertype.'))
TdlType('type-name', supertypes=['supertype'])
>>> next(parse('type := super1 & super2.'))
TdlType('type', supertypes=['super1', 'super2'])

```

Basic Features
--------------

```python
>>> next(parse('type := super & [ ATTR val ].'))
TdlType('type', supertypes=['super'], features=[('ATTR', 'val')])

```