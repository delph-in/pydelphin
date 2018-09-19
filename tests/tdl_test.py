# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from io import StringIO

import pytest

from delphin import tdl
from delphin.tdl import (
    _Term,
    Regex,
    String,
    TypeIdentifier,
    AVM,
    ConsList,
    DiffList,
    Coreference,
    Conjunction,
    TypeDefinition,
    TypeAddendum,
    LexicalRuleDefinition
)
from delphin.exceptions import TdlError, TdlWarning


def tdlparse(s):
    return next(tdl.parse(StringIO(s)))


def test_Term():
    q = _Term(docstring='hi')
    assert q.docstring == 'hi'

    r = Regex('r*')
    s = String('s')
    t = TypeIdentifier('t')
    a = AVM()
    cl = ConsList()
    dl = DiffList()
    c = Coreference(None)
    assert isinstance(r, _Term)
    assert isinstance(s, _Term)
    assert isinstance(t, _Term)
    assert isinstance(a, _Term)
    assert isinstance(cl, _Term)
    assert isinstance(dl, _Term)
    assert isinstance(c, _Term)
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
    assert str(t) == 't2'


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
    # string formatting
    assert str(t) == '"s"'

    t = String('s2', docstring='doc')
    assert t == 's2'
    assert t == String('s2', docstring='foo')
    assert str(t) == '"s2"'


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
    # string formatting
    assert str(t) == '^r$'

    t = Regex('r2', docstring='doc')
    assert t == 'r2'
    assert t == Regex('r2', docstring='foo')
    assert str(t) == '^r2$'


def test_AVM():
    a = AVM()
    assert a.features() == []
    assert 'ATTR' not in a

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
        [AVM([('ATTR2', Conjunction([String('b')]))])]))])
    assert len(a.features()) == 1
    assert a.features()[0][0] == 'ATTR1'
    assert a.features()[0][1] == a['ATTR1']
    assert a.features()[0][1].features()[0][0] == 'ATTR2'
    assert a.features()[0][1].features()[0][1] == a['ATTR1.ATTR2']
    assert a['ATTR1.ATTR2'] == a['ATTR1']['ATTR2']
    a.normalize()
    assert a.features()[0][0] == 'ATTR1.ATTR2'

    a = AVM()
    a['ATTR1.ATTR2'] = Conjunction([TypeIdentifier('a')])
    assert len(a.features()) == 1
    assert a.features()[0][0] == 'ATTR1.ATTR2'
    b = AVM()
    b['ATTR1.ATTR2'] = TypeIdentifier('a')
    assert a == b


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
    with pytest.raises(TdlError):
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


def test_Conjunction():
    c = Conjunction()
    orig_c = c
    assert len(c.terms) == 0
    c &= TypeIdentifier('a')
    assert len(c.terms) == 1
    assert len(orig_c.terms) == 0
    with pytest.raises(TypeError):
        c &= 'b'
    with pytest.raises(TypeError):
        c.add('b')


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
    # with pytest.raises(TdlError):
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
    assert len(t.features()) == 1
    _, val = t.features()[0]
    assert isinstance(val, Conjunction)
    assert len(val.types()) == 1
    assert isinstance(val.types()[0], String)
    assert val.types()[0] == 'val'


def test_quoted_symbol():
    with pytest.warns(TdlWarning):
        t = tdlparse("a := b & [ ATTR 'val ].")
    assert len(t.features()) == 1
    _, val = t.features()[0]
    assert isinstance(val, Conjunction)
    assert len(val.types()) == 1
    assert isinstance(val.types()[0], TypeIdentifier)
    assert val.types()[0] == 'val'


def test_parse_type_features():
    t = tdlparse('a := b & [ ATTR val ].')
    assert len(t.features()) == 1
    feat, val = t.features()[0]
    assert feat == 'ATTR'
    assert isinstance(val, Conjunction)
    assert len(val.features()) == 0
    assert val.types() == ['val']

    # integers are not primitives
    t = tdlparse('a := b & [ ATTR 1 ].')
    feat, val = t.features()[0]
    assert isinstance(val, Conjunction)
    assert val.types() == ['1']
    assert isinstance(val.types()[0], TypeIdentifier)

    t = tdlparse('a := b & [ ATTR val1 & val2].')
    assert len(t.features()) == 1
    feat, val = t.features()[0]
    assert len(val.types()) == 2
    assert val.types() == ['val1', 'val2']


def test_parse_multiple_features():
    t = tdlparse('a := b & [ ATTR1 1, ATTR2 2].')
    assert len(t.features()) == 2
    feat, val = t.features()[0]
    assert feat == 'ATTR1'
    assert val.types() == ['1']
    feat, val = t.features()[1]
    assert feat == 'ATTR2'
    assert val.types() == ['2']


def test_parse_multiple_avms():
    t = tdlparse('a := b & [ ATTR1 1 ] & [ ATTR2 2].')
    assert len(t.features()) == 2
    feat, val = t.features()[0]
    assert feat == 'ATTR1'
    assert val.types() == ['1']
    feat, val = t.features()[1]
    assert feat == 'ATTR2'
    assert val.types() == ['2']


def test_parse_feature_path():
    t = tdlparse('a := b & [ ATTR1.ATTR2 2 ].')
    assert len(t.features()) == 1
    feat, val = t.features()[0]
    assert feat == 'ATTR1.ATTR2'
    assert isinstance(val, Conjunction)
    assert val.types() == ['2']

    t = tdlparse('a := b & [ ATTR1 [ ATTR2 2 ] ].')
    assert len(t.features()) == 1
    feat, val = t.features()[0]
    assert feat == 'ATTR1'
    assert isinstance(val, Conjunction)
    assert len(val.terms) == 1
    assert isinstance(val.terms[0], AVM)
    assert len(val.terms[0].features()) == 1
    feat, val = val.terms[0].features()[0]
    assert feat == 'ATTR2'
    assert val.types() == ['2']

    t = tdlparse('a := b & [ ATTR1 [ ATTR2 2, ATTR3 3 ] ].')
    assert len(t.features()) == 1
    feat, val = t.features()[0]
    assert feat == 'ATTR1'
    assert isinstance(val, Conjunction)
    assert len(val.terms) == 1
    assert isinstance(val.terms[0], AVM)
    fs = val.terms[0]
    assert len(fs.features()) == 2
    feat, val = fs.features()[0]
    assert feat == 'ATTR2'
    assert isinstance(val, Conjunction)
    assert val.types() == ['2']
    feat, val = fs.features()[1]
    assert feat == 'ATTR3'
    assert isinstance(val, Conjunction)
    assert val.types() == ['3']

    t = tdlparse('a := b & [ ATTR1.ATTR2 2, ATTR1.ATTR3 3 ].')
    assert len(t.features()) == 1
    feat, val = t.features()[0]
    assert feat == 'ATTR1'
    assert isinstance(val, AVM)
    fs = val
    assert len(fs.features()) == 2
    feat, val = fs.features()[0]
    assert feat == 'ATTR2'
    assert val.types() == ['2']
    feat, val = fs.features()[1]
    assert feat == 'ATTR3'
    assert val.types() == ['3']


def test_parse_coreferences():
    tdlparse('a := b.')

    # with pytest.raises(TdlError):
    #     tdlparse('a := b & [ ATTR1 #x & 1, ATTR2 1 ].')

    tdlparse('a := b & [ ATTR1 #x & 1, ATTR2 #x ].')
    # assert t.coreferences == [('#x', ['ATTR1', 'ATTR2'])]


def test_parse_typedef():
    # no problems
    tdlparse('a := b.')
    tdlparse('a := b & [ ].')
    tdlparse('a := b & [ ATTR val, ATTR2.ATTR3 "val" ].')
    # with warning
    with pytest.warns(TdlWarning):
        tdlparse('a :< b.')
    # problems
    with pytest.raises(TdlError):
        tdlparse('a')
    with pytest.raises(TdlError):
        tdlparse('a :=')
    with pytest.raises(TdlError):
        tdlparse('a := .')
    with pytest.raises(TdlError):
        tdlparse('a := b')
    with pytest.raises(TdlError):
        tdlparse('a := b &')
    with pytest.raises(TdlError):
        tdlparse('a := b &.')
    with pytest.raises(TdlError):
        tdlparse('a := b & [')
    with pytest.raises(TdlError):
        tdlparse('a := b & [ ]')
    with pytest.raises(TdlError):
        tdlparse('a := b & [ ] ].')
    with pytest.raises(TdlError):
        tdlparse('a := b & [ ATTR')
    with pytest.raises(TdlError):
        tdlparse('a := b & [ ATTR ].')
    with pytest.raises(TdlError):
        tdlparse('a := b & [ ATTR val')
    with pytest.raises(TdlError):
        tdlparse('a := b & [ ATTR val ]')
    with pytest.raises(TdlError):
        tdlparse('a := b & [ ATTR val,')
    with pytest.raises(TdlError):
        tdlparse('a := b & [ ATTR val.')
    with pytest.raises(TdlError):
        tdlparse('a := b & [ ATTR val, ]')
    # syntactically coherent but missing required elements
    with pytest.raises(TdlError):
        tdlparse('a := [ ].')
    with pytest.raises(TdlError):
        tdlparse('a := """doc""".')


def test_parse_typeaddendum():
    # no problems
    tdlparse('a :+ """doc""".')
    tdlparse('a :+ b.')
    tdlparse('a :+ [ ATTR val ].')
    tdlparse('a :+ b & [ ATTR val, ATTR2.ATTR3 "val" ].')
    # problems (most tests covered by type definition)
    with pytest.raises(TdlError):
        tdlparse('a :+ .')
    with pytest.raises(TdlError):
        tdlparse('a :+ b &.')


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

    with pytest.raises(TdlError):
        tdlparse('a := b & """doc""".')

    with pytest.raises(TdlError):
        tdlparse('a := b """doc""" & c.')

    # with pytest.raises(TdlError):
    #     tdlparse('a := """doc-only""".')

    # ignored
    t = tdlparse('a := b & [ ATTR """doc""" val ].')
    assert t.documentation() is None
    assert t.documentation(level='top') == []


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


def test_format_Conjunction():
    assert tdl.format(Conjunction()) == ''
    assert tdl.format(Conjunction([TypeIdentifier('a')])) == 'a'
    assert tdl.format(
        Conjunction([TypeIdentifier('a'), TypeIdentifier('b')])) == 'a & b'
