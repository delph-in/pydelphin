# -*- coding: utf-8 -*-

import sys
import os
import tempfile

import pytest

from delphin.tfs import TFSError
from delphin import tdl
from delphin.tdl import (
    Term,
    Regex,
    String,
    TypeIdentifier,
    AVM,
    ConsList,
    DiffList,
    Coreference,
    Conjunction,
    LetterSet,
    WildCard,
    TypeDefinition,
    TypeAddendum,
    LexicalRuleDefinition,
    TypeEnvironment,
    InstanceEnvironment,
    FileInclude,
    TDLError,
    TDLSyntaxError,
    TDLWarning)


def _iterparse(s):
    with tempfile.TemporaryDirectory() as dir:
        path = os.path.join(dir, 'tmp.tdl')
        with open(path, 'w') as fh:
            print(s, file=fh)
        yield from tdl.iterparse(path)


def tdlparse(s):
    _, obj, _ = next(_iterparse(s))
    return obj


def test_Term():
    q = Term(docstring='hi')
    assert q.docstring == 'hi'

    r = Regex('r*')
    s = String('s')
    t = TypeIdentifier('t')
    a = AVM()
    cl = ConsList()
    dl = DiffList()
    c = Coreference(None)
    assert isinstance(r, Term)
    assert isinstance(s, Term)
    assert isinstance(t, Term)
    assert isinstance(a, Term)
    assert isinstance(cl, Term)
    assert isinstance(dl, Term)
    assert isinstance(c, Term)
    assert isinstance(r & s, Conjunction)
    assert (r & s).terms == [r, s]
    assert isinstance(s & t, Conjunction)
    assert isinstance(t & a, Conjunction)
    assert isinstance(a & cl, Conjunction)
    assert isinstance(cl & dl, Conjunction)
    assert isinstance(dl & c, Conjunction)
    assert isinstance(c & r, Conjunction)
    assert isinstance((r & s) & t, Conjunction)
    assert ((r & s) & t).terms == [r, s, t]
    assert isinstance(r & (s & t), Conjunction)
    assert (r & (s & t)).terms == [r, s, t]


def test_TypeIdentifier():
    with pytest.raises(TypeError):
        t = TypeIdentifier()
    t = TypeIdentifier('t')
    # case-insensitive comparision
    assert t == TypeIdentifier('t')
    assert t == TypeIdentifier('T')
    assert t != String('t')
    assert t != Regex('t')
    assert t == 't'
    assert t == 'T'

    t = TypeIdentifier('t2', docstring='doc')
    assert t == 't2'
    assert t == TypeIdentifier('t2', docstring='foo')


def test_String():
    with pytest.raises(TypeError):
        t = String()

    t = String('s')
    # case-sensitive comparison
    assert t == String('s')
    assert t != String('S')
    assert t != TypeIdentifier('s')
    assert t != Regex('s')
    assert t == 's'
    assert t != 'S'

    t = String('s2', docstring='doc')
    assert t == 's2'
    assert t == String('s2', docstring='foo')


def test_Regex():
    with pytest.raises(TypeError):
        t = Regex()

    t = Regex('r')
    # case-sensitive comparison
    assert t == Regex('r')
    assert t != Regex('R')
    assert t != TypeIdentifier('r')
    assert t != String('r')
    assert t == 'r'
    assert t != 'R'

    t = Regex('r2', docstring='doc')
    assert t == 'r2'
    assert t == Regex('r2', docstring='foo')


def test_AVM():
    a = AVM()
    assert a.features() == []
    assert 'ATTR' not in a

    with pytest.raises(TypeError):
        AVM({'ATTR': 'val'})

    a = AVM([('ATTR', Conjunction([TypeIdentifier('a')]))])
    assert len(a.features()) == 1
    assert 'ATTR' in a
    assert a.features()[0][0] == 'ATTR'
    assert a.features()[0][1].types() == ['a']
    assert a.features()[0][1] == a['ATTR']

    a = AVM([('ATTR1.ATTR2', Conjunction([String('b')]))])
    assert len(a.features()) == 1
    assert a.features()[0][0] == 'ATTR1.ATTR2'
    assert a.features()[0][1] == a['ATTR1.ATTR2']

    a = AVM([('ATTR1', Conjunction(
        [AVM([('ATTR2.ATTR3', Conjunction([String('b')]))])]))])
    assert len(a.features()) == 1
    assert a.features()[0][0] == 'ATTR1'
    assert a.features()[0][1] == a['ATTR1']
    assert a['ATTR1'].features()[0][0] == 'ATTR2.ATTR3'
    assert a['ATTR1'].features()[0][1] == a['ATTR1.ATTR2.ATTR3']
    assert a['ATTR1.ATTR2.ATTR3'] == a['ATTR1']['ATTR2']['ATTR3']
    assert a.features(expand=True)[0][0] == 'ATTR1.ATTR2.ATTR3'
    a.normalize()
    assert a.features()[0][0] == 'ATTR1.ATTR2.ATTR3'
    assert a.features(expand=True)[0][0] == 'ATTR1.ATTR2.ATTR3'

    a = AVM()
    a['ATTR1.ATTR2'] = Conjunction([TypeIdentifier('a')])
    assert len(a.features()) == 1
    assert a.features()[0][0] == 'ATTR1.ATTR2'
    b = AVM()
    b['ATTR1.ATTR2'] = TypeIdentifier('a')
    assert a == b

    a = AVM([('ATTR1', Conjunction(
        [TypeIdentifier('b'),
         AVM([('ATTR2', TypeIdentifier('c'))])]))])
    assert a.features(expand=True) == [
        ('ATTR1', TypeIdentifier('b')),
        ('ATTR1.ATTR2', TypeIdentifier('c'))]


def test_ConsList():
    c = ConsList()
    assert len(c) == 0
    assert c.terminated is False
    assert c.features() == []
    c.terminate(tdl.EMPTY_LIST_TYPE)
    assert c.terminated is True
    assert c.features() == []

    c = ConsList([TypeIdentifier('a')])
    assert len(c) == 1
    assert c['FIRST'] is not None
    assert c['REST'] == AVM()
    c.append(TypeIdentifier('b'))
    assert len(c) == 2
    assert c['REST.FIRST'] is not None
    assert c['REST.REST'] == AVM()
    c.terminate(tdl.EMPTY_LIST_TYPE)
    with pytest.raises(TDLError):
        c.append(TypeIdentifier('c'))

    c = ConsList([TypeIdentifier('a')], end=Coreference('x'))
    assert len(c) == 2
    assert c.terminated is True


def test_DiffList():
    d = DiffList()
    assert len(d) == 0
    assert d.last == 'LIST'
    assert d['LAST'] == d[d.last]

    d = DiffList([TypeIdentifier('a')])
    assert len(d) == 1
    assert d.last == 'LIST.REST'
    assert d['LAST'] == d[d.last]
    d = DiffList([TypeIdentifier('a'), String('b')])
    assert len(d) == 2
    assert d.last == 'LIST.REST.REST'
    assert d['LAST'] == d[d.last]

    # append() is not defined for DiffList
    with pytest.raises(AttributeError):
        d.append(TypeIdentifier('d'))


def test_Coreference():
    Coreference(None)
    Coreference('x')
    with pytest.raises(TypeError):
        Coreference()


class TestConjunction:
    def test_init(self):
        c = Conjunction()
        assert c.terms == []
        c = Conjunction([TypeIdentifier('a')])
        assert len(c.terms) == 1
        with pytest.raises(TypeError):
            Conjunction('a')
        with pytest.raises(TypeError):
            Conjunction(['a'])
        with pytest.raises(TypeError):
            Conjunction(TypeIdentifier('a'))

    def test_and(self):
        c = Conjunction()
        assert len(c.terms) == 0
        c &= TypeIdentifier('a')
        assert len(c.terms) == 1
        c &= TypeIdentifier('b')
        assert len(c.terms) == 2
        with pytest.raises(TypeError):
            c &= 'b'

    def test_eq(self):
        a = Conjunction([TypeIdentifier('a')])
        b = Conjunction([String('a')])
        assert a == a
        assert a != b
        assert a == TypeIdentifier('a')
        assert a != String('a')

    def test__contains__(self):
        a = Conjunction()
        assert 'ATTR' not in a
        a.add(AVM({'ATTR': TypeIdentifier('val')}))
        assert 'ATTR' in a
        a.add(AVM({'ATTR': TypeIdentifier('val2')}))  # two AVMs
        assert 'ATTR' in a

    def test__getitem__(self):
        a = Conjunction()
        with pytest.raises(KeyError):
            a['ATTR']
        a.add(AVM({'ATTR': TypeIdentifier('val')}))
        assert a['ATTR'] == TypeIdentifier('val')
        a.add(AVM({'ATTR': TypeIdentifier('val2')}))  # two AVMs
        assert a['ATTR'] == Conjunction([TypeIdentifier('val'),
                                         TypeIdentifier('val2')])

    def test__setitem__(self):
        a = Conjunction()
        with pytest.raises(TDLError):
            a['ATTR'] = TypeIdentifier('val')
        a.add(AVM())
        a['ATTR'] = TypeIdentifier('val')
        assert a['ATTR'] == TypeIdentifier('val')
        # reassignment overwrites
        a['ATTR'] = TypeIdentifier('val2')
        assert a['ATTR'] == TypeIdentifier('val2')
        a['ATTR'] &= TypeIdentifier('val3')
        assert a['ATTR'] == Conjunction([TypeIdentifier('val2'),
                                         TypeIdentifier('val3')])
        # setitem adds to the last AVM
        a.add(AVM())
        a['ATTR'] = TypeIdentifier('val4')
        assert a.terms[1]['ATTR'] == TypeIdentifier('val4')

    def test__setitem__issue293(self):
        a = AVM({'A': Conjunction([AVM()])})
        a['A.B'] = String('c')
        with pytest.raises(TFSError):
            a['A.B.C'] = String('d')

    def test__delitem__(self):
        a = Conjunction([AVM({'A.B': String('x')}),
                         AVM({'A.D': String('y')})])
        del a['A.B']
        assert 'A.B' not in a
        assert 'A.D' in a
        del a['A']
        assert 'A' not in a

    def test_get(self):
        pass

    def test_normalize(self):
        pass

    def test_terms(self):
        pass

    def test_add(self):
        c = Conjunction()
        with pytest.raises(TypeError):
            c.add('b')
        c.add(TypeIdentifier('a'))
        assert c.terms == [TypeIdentifier('a')]

    def test_types(self):
        pass

    def test_features(self):
        pass

    def test_string(self):
        pass


def test_TypeDefinition():
    with pytest.raises(TypeError):
        TypeDefinition()
    with pytest.raises(TypeError):
        TypeDefinition('typename')

    t = TypeDefinition('typename', Conjunction([TypeIdentifier('a')]))
    assert t.identifier == 'typename'
    assert t.supertypes == t.conjunction.types() == [TypeIdentifier('a')]
    assert t.features() == []
    assert t.documentation() is None
    assert t.documentation(level='top') == []

    # promote simple definition to Conjunction
    t = TypeDefinition('typename', TypeIdentifier('a'))
    assert t.identifier == 'typename'
    assert t.supertypes == t.conjunction.types() == [TypeIdentifier('a')]
    assert t.features() == []
    assert t.documentation() is None
    assert t.documentation(level='top') == []

    # must have a supertype  (test currently only at parse-time)
    # with pytest.raises(TDLError):
    #     TypeDefinition('t', Conjunction([AVM([('ATTR', String('s'))])]))

    t = TypeDefinition('t', Conjunction([AVM([('ATTR', String('s'))]),
                                         TypeIdentifier('a')]))
    assert t.supertypes == [TypeIdentifier('a')]
    assert t.features() == [('ATTR', Conjunction([String('s')]))]

    t = TypeDefinition('t', TypeIdentifier('a'), docstring='doc')
    assert t.docstring == 'doc'
    assert t.documentation() == 'doc'
    assert t.documentation(level='top') == ['doc']

    t = TypeDefinition(
        't', TypeIdentifier('a', docstring='a doc'), docstring='doc')
    assert t.docstring == 'doc'
    assert t.documentation() == 'a doc'
    assert t.documentation(level='top') == ['a doc', 'doc']


def test_TypeAddendum():
    with pytest.raises(TypeError):
        TypeAddendum()
    TypeAddendum('typename')
    # remaining tests assumed to be the same as TypeDefinition


def test_LexicalRuleDefinition():
    pass


def test_parse_identifiers():
    assert tdlparse('a := b.').identifier == 'a'
    assert tdlparse('*a* := b.').identifier == '*a*'
    assert tdlparse(u'Ⅲ := b.').identifier == u'Ⅲ'
    assert tdlparse(u'＊-marker := b.').identifier == u'＊-marker'
    assert tdlparse(u'，_c_1 := b.').identifier == u'，_c_1'
    assert tdlparse(u'_n_1 := b.').identifier == u'_n_1'
    assert tdlparse(u'和_c_⚠ := b.').identifier == u'和_c_⚠'
    assert tdlparse(u'格里姆斯比•罗伊洛特_n_1 := b.').identifier == (
        u'格里姆斯比•罗伊洛特_n_1')
    with pytest.raises(TDLSyntaxError):
        tdlparse('a:b := b.')
    with pytest.raises(TDLSyntaxError):
        tdlparse('a[b := b.')
    with pytest.raises(TDLSyntaxError):
        tdlparse('a!b := b.')
    with pytest.raises(TDLSyntaxError):
        tdlparse('a|b := b.')
    with pytest.raises(TDLSyntaxError):
        tdlparse('a.b := b.')
    with pytest.raises(TDLSyntaxError):
        tdlparse('#a := b.')
    with pytest.raises(TDLSyntaxError):
        tdlparse('a&b := b.')
    with pytest.raises(TDLSyntaxError):
        tdlparse('a,b := b.')


def test_parse_supertypes():
    t = tdlparse('a := b.')
    assert t.supertypes == ['b']

    t = tdlparse('a := b & c.')
    assert t.supertypes == ['b', 'c']

    t = tdlparse('a := b & [ ] & d.')
    assert t.supertypes == ['b', 'd']

    t = tdlparse('a := "string".')
    assert t.supertypes == ['string']


def test_parse_no_features():
    t = tdlparse('a := b.')
    assert t.features() == []

    t = tdlparse('a := b & [ ].')
    assert t.features() == []


def test_parse_string_features():
    t = tdlparse('a := b & [ ATTR "val" ].')
    assert isinstance(t['ATTR'], String)
    assert t['ATTR'] == 'val'


def test_quoted_symbol():
    with pytest.warns(TDLWarning):
        t = tdlparse("a := b & [ ATTR 'val ].")
    assert isinstance(t['ATTR'], TypeIdentifier)
    assert t['ATTR'] == 'val'


def test_parse_type_features():
    t = tdlparse('a := b & [ ATTR val ].')
    assert isinstance(t['ATTR'], TypeIdentifier)
    assert t['ATTR'] == 'val'

    # integers are not primitives
    t = tdlparse('a := b & [ ATTR 1 ].')
    assert isinstance(t['ATTR'], TypeIdentifier)
    assert t['ATTR'] == '1'

    t = tdlparse('a := b & [ ATTR val1 & val2].')
    assert isinstance(t['ATTR'], Conjunction)
    assert t['ATTR'].terms == ['val1', 'val2']


def test_parse_cons_list():
    t = tdlparse('a := b & [ ATTR < > ].')
    assert isinstance(t['ATTR'], ConsList)
    assert t['ATTR'].terminated

    t = tdlparse('a := b & [ ATTR < ... > ].')
    assert isinstance(t['ATTR'], ConsList)
    assert not t['ATTR'].terminated

    t = tdlparse('a := b & [ ATTR < [] . #x > ].')
    assert isinstance(t['ATTR'], ConsList)
    assert t['ATTR'].terminated

    t = tdlparse('a := b & [ ATTR < [] , ... > ].')
    assert isinstance(t['ATTR'], ConsList)
    assert not t['ATTR'].terminated

    with pytest.raises(TDLSyntaxError):
        tdlparse('a := b & [ ATTR < [] , > ].')
    with pytest.raises(TDLSyntaxError):
        tdlparse('a := b & [ ATTR < , [] > ].')
    with pytest.raises(TDLSyntaxError):
        tdlparse('a := b & [ ATTR < [] [] > ].')


@pytest.mark.skipif(sys.version_info < (3, 7),
                    reason='recursion test is flaky on Python 3.6')
@pytest.mark.slow
def test_issue_294():
    # check for recursion error
    with pytest.raises(TDLError):
        tdlparse('a := b & [ ATTR < [] ' + ', []' * 500 + ' > ].')
    # make sure it's avoidable
    oldlimit = sys.getrecursionlimit()
    try:
        sys.setrecursionlimit(2500)
        tdlparse('a := b & [ ATTR < [] ' + ', []' * 500 + ' > ].')
    finally:
        sys.setrecursionlimit(oldlimit)


def test_parse_diff_list():
    t = tdlparse('a := b & [ ATTR <! !> ].')
    assert isinstance(t['ATTR'], DiffList)

    t = tdlparse('a := b & [ ATTR <! [] !> ].')
    assert isinstance(t['ATTR'], DiffList)

    t = tdlparse('a := b & [ ATTR <! [], [] !> ].')
    assert isinstance(t['ATTR'], DiffList)


def test_parse_multiple_features():
    t = tdlparse('a := b & [ ATTR1 1, ATTR2 2].')
    assert len(t.features()) == 2
    assert t['ATTR1'] == '1'
    assert t['ATTR2'] == '2'


def test_parse_multiple_avms():
    t = tdlparse('a := b & [ ATTR1 1 ] & [ ATTR2 2].')
    assert len(t.conjunction.terms) == 3
    assert len(t.features()) == 2
    assert t['ATTR1'] == '1'
    assert t['ATTR2'] == '2'


def test_parse_feature_path():
    t = tdlparse('a := b & [ ATTR1.ATTR2 2 ].')
    assert isinstance(t['ATTR1'], AVM)
    assert isinstance(t['ATTR1.ATTR2'], TypeIdentifier)
    assert t['ATTR1.ATTR2'] == t['ATTR1']['ATTR2'] == '2'

    t = tdlparse('a := b & [ ATTR1 [ ATTR2 2 ] ].')
    assert isinstance(t['ATTR1'], AVM)
    assert isinstance(t['ATTR1.ATTR2'], TypeIdentifier)
    assert t['ATTR1.ATTR2'] == t['ATTR1']['ATTR2'] == '2'

    t = tdlparse('a := b & [ ATTR1 [ ATTR2 2, ATTR3 3 ] ].')
    assert isinstance(t['ATTR1'], AVM)
    assert t['ATTR1.ATTR2'] == '2'
    assert t['ATTR1.ATTR3'] == '3'

    t = tdlparse('a := b & [ ATTR1.ATTR2 2, ATTR1.ATTR3 3 ].')
    assert isinstance(t['ATTR1'], AVM)
    assert t['ATTR1.ATTR2'] == '2'
    assert t['ATTR1.ATTR3'] == '3'


def test_parse_coreferences():
    tdlparse('a := b.')

    # with pytest.raises(TDLError):
    #     tdlparse('a := b & [ ATTR1 #x & 1, ATTR2 1 ].')

    tdlparse('a := b & [ ATTR1 #x & 1, ATTR2 #x ].')
    # assert t.coreferences == [('#x', ['ATTR1', 'ATTR2'])]


def test_parse_typedef():
    # no problems
    tdlparse('a := b.')
    tdlparse('a := b & [ ].')
    tdlparse('a := b & [ ATTR val, ATTR2.ATTR3 "val" ].')
    # with warning
    with pytest.warns(TDLWarning):
        tdlparse('a :< b.')
    # problems
    with pytest.raises(TDLSyntaxError):
        tdlparse('a')
    with pytest.raises(TDLSyntaxError):
        tdlparse('a :=')
    with pytest.raises(TDLSyntaxError):
        tdlparse('a := .')
    with pytest.raises(TDLSyntaxError):
        tdlparse('a := b')
    with pytest.raises(TDLSyntaxError):
        tdlparse('a := b &')
    with pytest.raises(TDLSyntaxError):
        tdlparse('a := b &.')
    with pytest.raises(TDLSyntaxError):
        tdlparse('a := b & [')
    with pytest.raises(TDLSyntaxError):
        tdlparse('a := b & [ ]')
    with pytest.raises(TDLSyntaxError):
        tdlparse('a := b & [ ] ].')
    with pytest.raises(TDLSyntaxError):
        tdlparse('a := b & [ ATTR')
    with pytest.raises(TDLSyntaxError):
        tdlparse('a := b & [ ATTR ].')
    with pytest.raises(TDLSyntaxError):
        tdlparse('a := b & [ ATTR val')
    with pytest.raises(TDLSyntaxError):
        tdlparse('a := b & [ ATTR val ]')
    with pytest.raises(TDLSyntaxError):
        tdlparse('a := b & [ ATTR val,')
    with pytest.raises(TDLSyntaxError):
        tdlparse('a := b & [ ATTR val.')
    with pytest.raises(TDLSyntaxError):
        tdlparse('a := b & [ ATTR val, ]')
    # syntactically coherent but missing required elements
    with pytest.raises(TDLSyntaxError):
        tdlparse('a := [ ].')
    with pytest.raises(TDLSyntaxError):
        tdlparse('a := """doc""".')


def test_parse_typeaddendum():
    # no problems
    tdlparse('a :+ """doc""".')
    tdlparse('a :+ b.')
    tdlparse('a :+ [ ATTR val ].')
    tdlparse('a :+ b & [ ATTR val, ATTR2.ATTR3 "val" ].')
    # problems (most tests covered by type definition)
    with pytest.raises(TDLSyntaxError):
        tdlparse('a :+ .')
    with pytest.raises(TDLSyntaxError):
        tdlparse('a :+ b &.')


def test_parse_lexicalruledefinition():
    # no problems
    lr = tdlparse('a := %prefix no-pattern-rule.')
    assert lr.affix_type == 'prefix'
    assert lr.patterns == []
    lr = tdlparse('a := %suffix (y ies) y-plural-rule.')
    assert lr.affix_type == 'suffix'
    assert lr.patterns == [('y', 'ies')]
    lr = tdlparse('a := %suffix (y ies) (!c !cs) (?i us) silly-plural-rule.')
    assert lr.affix_type == 'suffix'
    assert lr.patterns == [('y', 'ies'), ('!c', '!cs'), ('?i', 'us')]
    # problems (most tests covered by type definition)
    with pytest.raises(TDLSyntaxError):
        tdlparse('a := %infix (i a) infix-rule.')
    with pytest.raises(TDLSyntaxError):
        tdlparse('a := %prefix (a) bad-rule.')
    with pytest.raises(TDLSyntaxError):
        tdlparse('a := %prefix (a b c) bad-rule.')


def test_parse_docstrings():
    t = tdlparse('a := b.')
    assert t.documentation() is None
    assert t.documentation(level='top') == []

    t = tdlparse('a := """doc""" b.')
    assert t.documentation() == 'doc'
    assert t.documentation(level='top') == ['doc']

    t = tdlparse('''a := """
        doc""" b.''')
    assert t.documentation() == '\n        doc'

    t = tdlparse('a := """doc1""" b & """doc2""" c.')
    assert t.documentation() == 'doc1'
    assert t.documentation(level='top') == ['doc1', 'doc2']

    t = tdlparse('a :+ """doc-only""".')
    assert t.documentation() == 'doc-only'

    t = tdlparse('a := b & """doc""" [ ].')
    assert t.documentation() == 'doc'

    t = tdlparse('a := b """doc""".')
    assert t.documentation() == 'doc'

    t = tdlparse('a := b & [ ] & """doc""" c.')
    assert t.documentation() == 'doc'

    # parsing errors

    with pytest.raises(TDLSyntaxError):
        tdlparse('a := b & """doc""".')

    with pytest.raises(TDLSyntaxError):
        tdlparse('a := b """doc""" & c.')

    # with pytest.raises(TDLError):
    #     tdlparse('a := """doc-only""".')

    # ignored
    t = tdlparse('a := b & [ ATTR """doc""" val ].')
    assert t.documentation() is None
    assert t.documentation(level='top') == []


def test_parse_letterset():
    ls = tdlparse(r'%(letter-set (!a ab\)c))')
    assert isinstance(ls, LetterSet)
    assert ls.var == '!a'
    assert ls.characters == 'ab)c'
    with pytest.raises(TDLSyntaxError):
        tdlparse('%letter-set (!a abc)')
    with pytest.raises(TDLSyntaxError):
        tdlparse('%(letter-set (?a abc))')
    with pytest.raises(TDLSyntaxError):
        tdlparse('%(letter-set (!a ab c))')


def test_parse_wildcard():
    wc = tdlparse(r'%(wild-card (?a ab\)c))')
    assert isinstance(wc, WildCard)
    assert wc.var == '?a'
    assert wc.characters == 'ab)c'
    with pytest.raises(TDLSyntaxError):
        tdlparse('%wild-card (?a abc)')
    with pytest.raises(TDLSyntaxError):
        tdlparse('%(wild-card (!a abc))')
    with pytest.raises(TDLSyntaxError):
        tdlparse('%(wild-card (?a ab c))')


def test_parse_linecomment():
    lc = tdlparse('; this is a comment\n')
    assert lc == ' this is a comment'


def test_parse_blockcomment():
    bc = tdlparse('#| this is a comment\n   on multiple lines|#')
    assert bc == ' this is a comment\n   on multiple lines'


def test_parse_environments():
    g = _iterparse(':begin :type.\n'
                   ':end :type.')
    event, e, _ = next(g)
    assert event == 'BeginEnvironment'
    assert isinstance(e, TypeEnvironment)
    assert e.entries == []
    event, e, _ = next(g)
    assert event == 'EndEnvironment'
    assert isinstance(e, TypeEnvironment)
    assert e.entries == []

    g = _iterparse(':begin :instance.\n'
                   ':end :instance.')
    event, e, _ = next(g)
    assert event == 'BeginEnvironment'
    assert isinstance(e, InstanceEnvironment)
    assert e.entries == []
    assert e.status == 'instance'
    event, e, _ = next(g)
    assert event == 'EndEnvironment'
    assert isinstance(e, InstanceEnvironment)
    assert e.entries == []

    g = _iterparse(':begin :type.\n'
                   'a := b & [ ATTR val ].\n'
                   ':end :type.')
    event, e, _ = next(g)
    assert event == 'BeginEnvironment'
    assert len(e.entries) == 0
    event, t, _ = next(g)
    assert event == 'TypeDefinition'
    event, e, _ = next(g)
    assert event == 'EndEnvironment'
    assert e.entries == [t]

    g = _iterparse(':begin :type.\n'
                 ':include "file1.tdl".\n'
                 ':include "subdir/file2.tdl".\n'
                 ':end :type.')
    event, e, _ = next(g)
    assert len(e.entries) == 0
    assert next(g)[0] == 'FileInclude'
    assert next(g)[0] == 'FileInclude'
    assert next(g)[0] == 'EndEnvironment'
    assert len(e.entries) == 2
    assert isinstance(e.entries[0], FileInclude)
    assert e.entries[0].value == 'file1.tdl'
    assert e.entries[0].path.name == 'file1.tdl'
    assert e.entries[1].value == 'subdir/file2.tdl'
    assert e.entries[1].path.name == 'file2.tdl'
    assert e.entries[1].path.parent.name == 'subdir'

    g = _iterparse(':begin :type.\n'
                   '  :include "file1.tdl".\n'
                   '  :begin :instance :status lex-rule.\n'
                   '    :include "lrules.tdl".\n'
                   '  :end :instance.\n'
                   ':end :type.')
    event, e, _ = next(g)
    assert next(g)[0] == 'FileInclude'
    event, e2, _ = next(g)
    assert event == 'BeginEnvironment'
    assert next(g)[0] == 'FileInclude'
    assert next(g)[0] == 'EndEnvironment'
    assert next(g)[0] == 'EndEnvironment'
    assert len(e.entries) == 2
    assert isinstance(e, TypeEnvironment)
    assert isinstance(e.entries[0], FileInclude)
    assert isinstance(e.entries[1], InstanceEnvironment)
    assert e2.status == 'lex-rule'
    assert len(e2.entries) == 1
    assert isinstance(e2.entries[0], FileInclude)


def test_format_TypeTerms():
    assert tdl.format(TypeIdentifier('a-type')) == 'a-type'
    assert tdl.format(String('a string')) == '"a string"'
    assert tdl.format(Regex('a*re[g]ex')) == '^a*re[g]ex$'
    assert tdl.format(Coreference('coref')) == '#coref'


def test_format_AVM():
    assert tdl.format(AVM()) == '[ ]'
    assert tdl.format(
        AVM([('ATTR', Conjunction([TypeIdentifier('a')]))])) == '[ ATTR a ]'
    assert tdl.format(
        AVM([('ATTR1', Conjunction([TypeIdentifier('a')])),
             ('ATTR2', Conjunction([TypeIdentifier('b')]))])
    ) == ('[ ATTR1 a,\n'
          '  ATTR2 b ]')
    assert tdl.format(
        AVM([('ATTR1', AVM([('ATTR2', Conjunction([TypeIdentifier('a')]))]))])
    ) == ('[ ATTR1.ATTR2 a ]')
    assert tdl.format(
        AVM([('ATTR1',
              Conjunction([AVM(
                  [('ATTR2', Conjunction([TypeIdentifier('a')]))])]))])
    ) == ('[ ATTR1 [ ATTR2 a ] ]')


def test_format_lists():
    assert tdl.format(ConsList()) == '< ... >'
    assert tdl.format(ConsList(end=tdl.EMPTY_LIST_TYPE)) == '< >'
    assert tdl.format(ConsList([String('a')])) == '< "a", ... >'
    assert tdl.format(
        ConsList([String('a')], end=Coreference('b'))) == '< "a" . #b >'

    assert tdl.format(DiffList()) == '<! !>'
    assert tdl.format(DiffList([String('a')])) == '<! "a" !>'
    assert tdl.format(DiffList([String('a'), String('b')])) == '<! "a", "b" !>'


def test_format_docstring_terms():
    assert tdl.format(
        TypeIdentifier('a', docstring='doc')) == '"""\ndoc\n"""\na'
    assert tdl.format(
        String('a', docstring='doc')) == '"""\ndoc\n"""\n"a"'
    assert tdl.format(
        Regex('a', docstring='doc')) == '"""\ndoc\n"""\n^a$'
    assert tdl.format(
        Coreference('a', docstring='doc')) == '"""\ndoc\n"""\n#a'
    assert tdl.format(
        AVM(docstring='doc')) == '"""\ndoc\n"""\n[ ]'
    assert tdl.format(
        ConsList(docstring='doc')) == '"""\ndoc\n"""\n< ... >'
    assert tdl.format(
        DiffList(docstring='doc')) == '"""\ndoc\n"""\n<! !>'
    # escape docstrings if necessary
    assert tdl.format(
        TypeIdentifier('a', docstring='"one" ""two"" """three""" """"""""')
    ) == '"""\n"one" ""two"" ""\\"three""\\" ""\\"""\\"""\n"""\na'


def test_format_Conjunction():
    assert tdl.format(Conjunction()) == ''
    assert tdl.format(Conjunction([TypeIdentifier('a')])) == 'a'
    assert tdl.format(
        Conjunction([TypeIdentifier('a'), TypeIdentifier('b')])) == 'a & b'


def test_format_typedefs():
    t = TypeDefinition(
        'id',
        Conjunction([TypeIdentifier('a', docstring='a doc'),
                     AVM([('ATTR', TypeIdentifier('b'))])]),
        docstring='t doc')
    t2 = TypeDefinition(
        'id',
        Conjunction([TypeIdentifier('a'),
                     AVM([('ATTR', TypeIdentifier('b'))],
                         docstring='a doc')]),
        docstring='t doc')
    a = TypeAddendum(
        'id',
        Conjunction([AVM([('ATTR', TypeIdentifier('b', docstring='b doc'))])]),
        docstring='t doc')
    lr = LexicalRuleDefinition(
        'id', affix_type='suffix', patterns=[('a', 'b'), ('c', 'd')],
        conjunction=Conjunction([TypeIdentifier('a', docstring='a doc')]),
        docstring='lr doc')

    assert tdl.format(t) == (
        'id := """\n'
        '      a doc\n'
        '      """\n'
        '      a &\n'
        '  [ ATTR b ]\n'
        '  """\n'
        '  t doc\n'
        '  """.')
    assert tdl.format(t2) == (
        'id := a &\n'
        '  """\n'
        '  a doc\n'
        '  """\n'
        '  [ ATTR b ]\n'
        '  """\n'
        '  t doc\n'
        '  """.')
    assert tdl.format(a) == (
        'id :+ [ ATTR """\n'
        '             b doc\n'
        '             """\n'
        '             b ]\n'
        '  """\n'
        '  t doc\n'
        '  """.')
    assert tdl.format(lr) == (
        'id :=\n'
        '%suffix (a b) (c d)\n'
        '  """\n'
        '  a doc\n'
        '  """\n'
        '  a\n'
        '  """\n'
        '  lr doc\n'
        '  """.')


def test_format_morphsets():
    assert tdl.format(LetterSet('!b', 'abc')) == '%(letter-set (!b abc))'
    assert tdl.format(WildCard('?b', 'abc')) == '%(wild-card (?b abc))'


def test_format_environments():
    assert tdl.format(TypeEnvironment()) == (
        ':begin :type.\n'
        ':end :type.')
    e = TypeEnvironment(entries=[
        TypeDefinition(
            'id',
            Conjunction([TypeIdentifier('a'),
                         AVM([('ATTR', TypeIdentifier('b'))])]))])
    assert tdl.format(e) == (
        ':begin :type.\n'
        '  id := a &\n'
        '    [ ATTR b ].\n'
        ':end :type.')
    e = TypeEnvironment(entries=[
        FileInclude('other.tdl'),
        InstanceEnvironment(status='lex-rule', entries=[
            FileInclude('lrules.tdl')]),
        FileInclude('another.tdl')])
    assert tdl.format(e) == (
        ':begin :type.\n'
        '  :include "other.tdl".\n'
        '  :begin :instance :status lex-rule.\n'
        '    :include "lrules.tdl".\n'
        '  :end :instance.\n'
        '  :include "another.tdl".\n'
        ':end :type.')
