
import pytest

from delphin.derivation import (
    from_string,
    from_dict,
    DerivationSyntaxError,
    Derivation as D,
    UDFNode as N,
    UDFTerminal as T,
    UDFToken as Tk
)


class TestUDFNode():
    def test_init(self):
        n = N(1, 'entity')
        assert n.id == 1
        assert n.entity == 'entity'
        assert n.score == -1.0
        assert n.start == -1
        assert n.end == -1
        assert n.daughters == []
        assert n.is_head()  # it has no siblings
        assert n.type is None
        n = N(1, 'entity', 0.5, 1, 2, [], head=True, type='type')
        assert n.id == 1
        assert n.entity == 'entity'
        assert n.score == 0.5
        assert n.start == 1
        assert n.end == 2
        assert n.daughters == []
        assert n.is_head()
        assert n.type == 'type'

    def test_parent(self):
        n1 = N(None, 'entity')
        assert n1.parent is None
        n2 = N(1, 'entity', 0.5, 1, 2, [], head=True, type='type', parent=n1)
        assert n2.parent is n1


class TestDerivation():
    def test_init(self):
        with pytest.raises(TypeError):
            D()
        with pytest.raises(TypeError):
            D(1)
        D(1, 'some-thing')
        D(1, 'some-thing', 0.5, 0, 3, [T('some-token')])
        # roots are special: id is None, entity is root, daughters must
        # exactly 1 node; rest are None
        with pytest.raises(TypeError):
            D(None)
        with pytest.raises(TypeError):
            D(None, 'some-root', 0.5)
        with pytest.raises(TypeError):
            D(None, 'some-root', start=1)
        with pytest.raises(TypeError):
            D(None, 'some-root', end=1)
        with pytest.raises(ValueError):
            D(None, 'some-root',
              daughters=[N(1, 'some-thing'), N(2, 'some-thing')])
        with pytest.raises(ValueError):
            D(None, 'some-root', daughters=[T('some-token')])
        D(None, 'some-root', daughters=[N(1, 'some-thing')])
        D(None, 'some-root', None, None, None, daughters=[N(1, 'some-thing')])
        # root not as top
        with pytest.raises(ValueError):
            D(1, 'some-thing', daughters=[
                N(None, 'some-root', daughters=[
                    N(2, 'a-lex', daughters=[T('some-token')])
                ])
            ])

    def test_attributes(self):
        t = D(1, 'some-thing')
        assert t.id == 1
        assert t.entity == 'some-thing'
        assert t.score == -1
        assert t.start == -1
        assert t.end == -1
        assert t.daughters == []
        t = D(1, 'some-thing', 0.5, 1, 6, [T('some token')])
        assert t.id == 1
        assert t.entity == 'some-thing'
        assert t.score == 0.5
        assert t.start == 1
        assert t.end == 6
        assert t.daughters == [T('some token')]
        t = D(None, 'some-root', daughters=[D(1, 'some-thing')])
        assert t.id is None
        assert t.entity == 'some-root'
        assert t.score is None
        assert t.start is None
        assert t.end is None
        assert len(t.daughters) == 1

    def test_fromstring(self):
        with pytest.raises(DerivationSyntaxError):
            from_string('')
        # root with no children
        # TODO: this should be a DerivationSyntaxError but the current
        # UDF parser doesn't make that straightforward. Revist this
        # when/if the UDF parsing changes
        with pytest.raises(ValueError):
            from_string('(some-root)')
        # does not start with `(` or end with `)`
        with pytest.raises(DerivationSyntaxError):
            from_string(' (1 some-thing -1 -1 -1 ("token"))')
        with pytest.raises(DerivationSyntaxError):
            from_string(' (1 some-thing -1 -1 -1 ("token")) ')
        # uneven parens
        with pytest.raises(DerivationSyntaxError):
            from_string('(1 some-thing -1 -1 -1 ("token")')
        # ok
        t = from_string('(1 some-thing -1 -1 -1 ("token"))')
        assert t.id == 1
        assert t.entity == 'some-thing'
        assert t.score == -1.0
        assert t.start == -1
        assert t.end == -1
        assert t.daughters == [T('token')]
        # newlines in tree
        t = from_string('''(1 some-thing -1 -1 -1
                              ("token"))''')
        assert t.id == 1
        assert t.entity == 'some-thing'
        assert t.score == -1.0
        assert t.start == -1
        assert t.end == -1
        assert t.daughters == [T('token')]
        # LKB-style terminals
        t = from_string('''(1 some-thing -1 -1 -1
                              ("to ken" 1 2))''')
        assert t.id == 1
        assert t.entity == 'some-thing'
        assert t.score == -1.0
        assert t.start == -1
        assert t.end == -1
        assert t.daughters == [T('to ken')]  # start/end ignored
        # TFS-style terminals
        t = from_string(r'''(1 some-thing -1 -1 -1
                              ("to ken" 2 "token [ +FORM \"to\" ]"
                                        3 "token [ +FORM \"ken\" ]"))''')
        assert t.id == 1
        assert t.entity == 'some-thing'
        assert t.score == -1.0
        assert t.start == -1
        assert t.end == -1
        assert t.daughters == [
            T('to ken', [Tk(2, r'token [ +FORM \"to\" ]'),
                         Tk(3, r'token [ +FORM \"ken\" ]')])
        ]
        # longer example
        t = from_string(r'''(root
            (1 some-thing 0.4 0 5
                (2 a-lex 0.8 0 1
                    ("a" 1 "token [ +FORM \"a\" ]"))
                (3 bcd-lex 0.5 2 5
                    ("bcd" 2 "token [ +FORM \"bcd\" ]")))
        )''')
        assert t.entity == 'root'
        assert len(t.daughters) == 1
        top = t.daughters[0]
        assert top.id == 1
        assert top.entity == 'some-thing'
        assert top.score == 0.4
        assert top.start == 0
        assert top.end == 5
        assert len(top.daughters) == 2
        lex = top.daughters[0]
        assert lex.id == 2
        assert lex.entity == 'a-lex'
        assert lex.score == 0.8
        assert lex.start == 0
        assert lex.end == 1
        assert lex.daughters == [T('a', [Tk(1, r'token [ +FORM \"a\" ]')])]
        lex = top.daughters[1]
        assert lex.id == 3
        assert lex.entity == 'bcd-lex'
        assert lex.score == 0.5
        assert lex.start == 2
        assert lex.end == 5
        assert lex.daughters == [T('bcd',
                                   [Tk(2, r'token [ +FORM \"bcd\" ]')])]

    def test_str(self):
        s = '(1 some-thing -1 -1 -1 ("token"))'
        assert str(from_string(s)) == s
        s = (r'(root (1 some-thing 0.4 0 5 (2 a-lex 0.8 0 1 '
             r'("a" 1 "token [ +FORM \"a\" ]")) '
             r'(3 bcd-lex 0.5 2 5 ("bcd" 2 "token [ +FORM \"bcd\" ]"))))')
        assert str(from_string(s)) == s

    def test_eq(self):
        a = from_string('(1 some-thing -1 -1 -1 ("token"))')
        # identity
        b = from_string('(1 some-thing -1 -1 -1 ("token"))')
        assert a == b
        # ids and scores don't matter
        b = from_string('(100 some-thing 0.114 -1 -1 ("token"))')
        assert a == b
        # tokens matter
        b = from_string('(1 some-thing -1 -1 -1 ("nekot"))')
        assert a != b
        # and type of rhs
        assert a != '(1 some-thing -1 -1 -1 ("token"))'
        # and tokenization
        b = from_string('(1 some-thing -1 2 7 ("token"))')
        assert a != b
        # and of course entities
        b = from_string('(1 epyt-emos -1 -1 -1 ("token"))')
        assert a != b
        # and number of children
        a = from_string('(1 x -1 -1 -1 (2 y -1 -1 -1 ("y")))')
        b = from_string('(1 x -1 -1 -1 (2 y -1 -1 -1 ("y")) (3 z -1 -1 -1 ("z")))')
        assert a != b
        # and order of children
        a = from_string('(1 x -1 -1 -1 (2 y -1 -1 -1 ("y")) (3 z -1 -1 -1 ("z")))')
        b = from_string('(1 x -1 -1 -1 (3 z -1 -1 -1 ("z")) (2 y -1 -1 -1 ("y")))')
        assert a != b
        # and UDX properties when specified
        a = from_string('(1 x -1 -1 -1 (2 ^y -1 -1 -1 ("y")) (3 z -1 -1 -1 ("z")))')
        b = from_string('(1 x -1 -1 -1 (2 ^y -1 -1 -1 ("y")) (3 z -1 -1 -1 ("z")))')
        assert a == b
        b = from_string('(1 x -1 -1 -1 (2 y -1 -1 -1 ("y")) (3 ^z -1 -1 -1 ("z")))')
        assert a != b
        b = from_string('(1 x -1 -1 -1 (2 y -1 -1 -1 ("y")) (3 z -1 -1 -1 ("z")))')
        assert a != b
        a = from_string('(1 some-thing@some-type -1 -1 -1 ("token"))')
        b = from_string('(1 some-thing@some-type -1 -1 -1 ("token"))')
        assert a == b
        b = from_string('(1 some-thing@another-type -1 -1 -1 ("token"))')
        assert a != b
        b = from_string('(1 some-thing -1 -1 -1 ("token"))')
        assert a != b

    def test_is_root(self):
        a = from_string('(1 some-thing -1 -1 -1 ("token"))')
        assert not a.is_root()
        a = from_string('(root (1 some-thing -1 -1 -1 ("token")))')
        assert a.is_root()
        assert not a.daughters[0].is_root()

    def test_is_head(self):
        # NOTE: is_head() is undefined for nodes with multiple
        # siblings, none of which are marked head (e.g. in plain UDF)
        a = from_string('(root (1 some-thing -1 -1 -1'
                        '  (2 some-thing -1 -1 -1 ("a"))'
                        '  (3 some-thing -1 -1 -1 ("b"))))')
        assert a.is_head()
        node = a.daughters[0]
        assert node.is_head()
        assert node.daughters[0].is_head() is None
        assert node.daughters[1].is_head() is None
        # if one sibling is marked, all become decidable
        a = from_string('(root (1 some-thing -1 -1 -1'
                        '  (2 some-thing -1 -1 -1 ("a"))'
                        '  (3 ^some-thing -1 -1 -1 ("b"))))')
        assert a.is_head()
        node = a.daughters[0]
        assert node.is_head()
        assert not node.daughters[0].is_head()
        assert node.daughters[1].is_head()

    def test_entity(self):
        a = from_string('(root (1 some-thing -1 -1 -1'
                        '  (2 a-thing -1 -1 -1 ("a"))'
                        '  (3 b-thing -1 -1 -1 ("b"))))')
        assert a.entity == 'root'
        node = a.daughters[0]
        assert node.entity == 'some-thing'
        assert node.daughters[0].entity == 'a-thing'
        assert node.daughters[1].entity == 'b-thing'
        a = from_string('(root (1 some-thing@some-type -1 -1 -1'
                        '  (2 a-thing@a-type -1 -1 -1 ("a"))'
                        '  (3 b-thing@b-type -1 -1 -1 ("b"))))')
        assert a.entity == 'root'
        node = a.daughters[0]
        assert node.entity == 'some-thing'
        assert node.daughters[0].entity == 'a-thing'
        assert node.daughters[1].entity == 'b-thing'

    def test_type(self):
        a = from_string('(root (1 some-thing -1 -1 -1'
                        '  (2 a-thing -1 -1 -1 ("a"))'
                        '  (3 b-thing -1 -1 -1 ("b"))))')
        assert a.type is None
        node = a.daughters[0]
        assert node.type is None
        assert node.daughters[0].type is None
        assert node.daughters[1].type is None
        a = from_string('(root (1 some-thing@some-type -1 -1 -1'
                        '  (2 a-thing@a-type -1 -1 -1 ("a"))'
                        '  (3 b-thing@b-type -1 -1 -1 ("b"))))')
        assert a.type is None
        node = a.daughters[0]
        assert node.type == 'some-type'
        assert node.daughters[0].type == 'a-type'
        assert node.daughters[1].type == 'b-type'

    def test_preterminals(self):
        a = from_string('(root (1 some-thing -1 -1 -1'
                        '  (2 a-thing -1 -1 -1 ("a"))'
                        '  (3 b-thing -1 -1 -1 ("b"))))')
        assert [t.id for t in a.preterminals()] == [2, 3]
        a = from_string(
            '(root'
            ' (1 some-thing@some-type 0.4 0 5'
            '  (2 a-lex@a-type 0.8 0 1'
            '   ("a b"'
            '    3 "token [ +FORM \\"a\\" ]"'
            '    4 "token [ +FORM \\"b\\" ]"))'
            '  (5 b-lex@b-type 0.9 1 2'
            '   ("b"'
            '    6 "token [ +FORM \\"b\\" ]"))))')
        assert [t.id for t in a.preterminals()] == [2, 5]

    def test_terminals(self):
        a = from_string('(root (1 some-thing -1 -1 -1'
                        '  (2 a-thing -1 -1 -1 ("a"))'
                        '  (3 b-thing -1 -1 -1 ("b"))))')
        assert [t.form for t in a.terminals()] == ['a', 'b']
        a = from_string(
            '(root'
            ' (1 some-thing@some-type 0.4 0 5'
            '  (2 a-lex@a-type 0.8 0 1'
            '   ("a b"'
            '    3 "token [ +FORM \\"a\\" ]"'
            '    4 "token [ +FORM \\"b\\" ]"))'
            '  (5 b-lex@b-type 0.9 1 2'
            '   ("b"'
            '    6 "token [ +FORM \\"b\\" ]"))))')
        assert [t.form for t in a.terminals()] == ['a b', 'b']

    def test_internals(self):
        a = from_string('(root (1 some-thing -1 -1 -1'
                        '  (2 a-thing -1 -1 -1 ("a"))'
                        '  (3 b-thing -1 -1 -1 ("b"))))')
        assert [t.id for t in a.internals()] == [None, 1]
        a = from_string(
            '(root'
            ' (1 some-thing@some-type 0.4 0 5'
            '  (2 a-lex@a-type 0.8 0 1'
            '   ("a b"'
            '    3 "token [ +FORM \\"a\\" ]"'
            '    4 "token [ +FORM \\"b\\" ]"))'
            '  (5 b-lex@b-type 0.9 1 2'
            '   ("b"'
            '    6 "token [ +FORM \\"b\\" ]"))))')
        assert [t.id for t in a.internals()] == [None, 1]

    def test_to_udf(self):
        s = '(1 some-thing -1 -1 -1 ("token"))'
        assert from_string(s).to_udf(indent=None) == s
        assert from_string(s).to_udf(indent=1) == (
            '(1 some-thing -1 -1 -1\n'
            ' ("token"))'
        )
        s = (r'(root (1 some-thing 0.4 0 5 (2 a-lex 0.8 0 1 '
             r'("a" 3 "token [ +FORM \"a\" ]")) '
             r'(4 bcd-lex 0.5 2 5 ("bcd" 5 "token [ +FORM \"bcd\" ]"))))')
        assert from_string(s).to_udf(indent=1) == (
            '(root\n'
            ' (1 some-thing 0.4 0 5\n'
            '  (2 a-lex 0.8 0 1\n'
            '   ("a"\n'
            '    3 "token [ +FORM \\"a\\" ]"))\n'
            '  (4 bcd-lex 0.5 2 5\n'
            '   ("bcd"\n'
            '    5 "token [ +FORM \\"bcd\\" ]"))))'
        )
        s = (r'(root (1 some-thing 0.4 0 5 (2 a-lex 0.8 0 1 '
             r'("a b" 3 "token [ +FORM \"a\" ]" 4 "token [ +FORM \"b\" ]"))))')
        assert from_string(s).to_udf(indent=1) == (
            '(root\n'
            ' (1 some-thing 0.4 0 5\n'
            '  (2 a-lex 0.8 0 1\n'
            '   ("a b"\n'
            '    3 "token [ +FORM \\"a\\" ]"\n'
            '    4 "token [ +FORM \\"b\\" ]"))))'
        )
        s = (r'(root (1 some-thing@some-type 0.4 0 5 (2 a-lex@a-type 0.8 0 1 '
             r'("a b" 3 "token [ +FORM \"a\" ]" 4 "token [ +FORM \"b\" ]"))))')
        assert from_string(s).to_udf(indent=1) == (
            '(root\n'
            ' (1 some-thing 0.4 0 5\n'
            '  (2 a-lex 0.8 0 1\n'
            '   ("a b"\n'
            '    3 "token [ +FORM \\"a\\" ]"\n'
            '    4 "token [ +FORM \\"b\\" ]"))))'
        )

    def test_to_udx(self):
        s = '(1 some-thing -1 -1 -1 ("token"))'
        assert from_string(s).to_udx(indent=None) == s
        s = (r'(root (1 some-thing@some-type 0.4 0 5 '
             r'(2 a-lex@a-type 0.8 0 1 '
             r'("a b" 3 "token [ +FORM \"a\" ]" 4 "token [ +FORM \"b\" ]")) '
             r'(5 b-lex@b-type 0.9 1 2 '
             r'("b" 6 "token [ +FORM \"b\" ]"))))')
        assert from_string(s).to_udx(indent=1) == (
            '(root\n'
            ' (1 some-thing@some-type 0.4 0 5\n'
            '  (2 a-lex@a-type 0.8 0 1\n'
            '   ("a b"\n'
            '    3 "token [ +FORM \\"a\\" ]"\n'
            '    4 "token [ +FORM \\"b\\" ]"))\n'
            '  (5 b-lex@b-type 0.9 1 2\n'
            '   ("b"\n'
            '    6 "token [ +FORM \\"b\\" ]"))))'
        )

    def test_to_dict(self):
        s = '(1 some-thing -1 -1 -1 ("token"))'
        assert from_string(s).to_dict() == {
            'id': 1,
            'entity': 'some-thing',
            'score': -1.0,
            'start': -1,
            'end': -1,
            'form': 'token'
        }
        fields = ('id', 'entity', 'score')
        # daughters and form are always shown
        assert from_string(s).to_dict(fields=fields) == {
            'id': 1,
            'entity': 'some-thing',
            'score': -1.0,
            'form': 'token'
        }
        s = (r'(root (0 top@top-rule -1 -1 -1'
             r' (1 a-lex@a-type -1 -1 -1 ("a b" 2 "token [ +FORM \"a\" ]"'
             r'  3 "token [ +FORM \"b\" ]"))'
             r' (4 ^c-lex@c-type -1 -1 -1 ("c" 5 "token [ +FORM \"c\" ]"))))')
        assert from_string(s).to_dict() == {
            'entity': 'root',
            'daughters': [
                {
                    'id': 0,
                    'entity': 'top',
                    'type': 'top-rule',
                    'score': -1.0,
                    'start': -1,
                    'end': -1,
                    'daughters': [
                        {
                            'id': 1,
                            'entity': 'a-lex',
                            'type': 'a-type',
                            'score': -1.0,
                            'start': -1,
                            'end': -1,
                            'form': 'a b',
                            'tokens': [
                                {'id': 2, 'tfs': r'token [ +FORM \"a\" ]'},
                                {'id': 3, 'tfs': r'token [ +FORM \"b\" ]'}
                            ]
                        },
                        {
                            'id': 4,
                            'entity': 'c-lex',
                            'type': 'c-type',
                            'head': True,
                            'score': -1.0,
                            'start': -1,
                            'end': -1,
                            'form': 'c',
                            'tokens': [
                                {'id': 5, 'tfs': r'token [ +FORM \"c\" ]'}
                            ]
                        }
                    ]
                }
            ]
        }
        assert from_string(s).to_dict(fields=fields) == {
            'entity': 'root',
            'daughters': [
                {
                    'id': 0,
                    'entity': 'top',
                    'score': -1.0,
                    'daughters': [
                        {
                            'id': 1,
                            'entity': 'a-lex',
                            'score': -1.0,
                            'form': 'a b'
                        },
                        {
                            'id': 4,
                            'entity': 'c-lex',
                            'score': -1.0,
                            'form': 'c'
                        }

                    ]
                }
            ]
        }

    def test_from_dict(self):
        s = '(root (1 some-thing -1 -1 -1 ("a")))'
        d = {
            'entity': 'root',
            'daughters': [
                {
                    'id': 1,
                    'entity': 'some-thing',
                    'form': 'a'
                }
            ]
        }
        assert from_dict(d) == from_string(s)
        s = (r'(root (1 ^some-thing@some-type -1 -1 -1 ("a b"'
             r' 2 "token [ +FORM \"a\" ]"'
             r' 3 "token [ +FORM \"b\" ]")))')
        d = {
            'entity': 'root',
            'daughters': [
                {
                    'id': 1,
                    'entity': 'some-thing',
                    'type': 'some-type',
                    'head': True,
                    'form': 'a b',
                    'tokens': [
                        {'id': 2, 'tfs': r'token [ +FORM \"a\" ]'},
                        {'id': 3, 'tfs': r'token [ +FORM \"b\" ]'}
                    ]
                }
            ]
        }
        assert from_dict(d) == from_string(s)
