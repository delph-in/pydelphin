
import pytest

from delphin import semi


def test_properties(tmp_path):
    p = tmp_path / 'a.smi'
    p.write_text(
            'properties:\n'
            '  bool.\n'
            '  + < bool.\n'
            '  - < bool.\n')
    s = semi.load(str(p))
    assert len(s.properties) == 3
    assert all([x in s.properties for x in ('bool', '+', '-')])
    assert s.properties.subsumes('bool', '+')
    assert not s.properties.compatible('+', '-')
    # redefinition
    p.write_text(
            'properties:\n'
            '  bool.\n'
            '  bool.\n')
    with pytest.warns(semi.SemIWarning):
        semi.load(str(p))


def test_variables(tmp_path):
    p = tmp_path / 'a.smi'
    p.write_text(
            'variables:\n'
            '  u.\n'
            '  i < u.\n'
            '  e < i : PERF bool, TENSE tense.\n'
            '  p < u.\n'
            '  x < i & p.\n'
            'properties:\n'
            '  bool.\n'
            '  tense.\n')
    s = semi.load(str(p))
    assert len(s.variables) == 5
    assert all([v in s.variables for v in 'uiepx'])
    assert s.variables['u'] == []
    assert s.variables['i'] == []
    assert s.variables['e'] == [('PERF', 'bool'), ('TENSE', 'tense')]
    assert s.variables['p'] == []
    assert s.variables['x'] == []
    assert all(s.variables.subsumes('u', v) for v in 'iepx')
    assert not s.variables.compatible('e', 'x')
    # redefinition
    p.write_text(
            'variables:\n'
            '  u.\n'
            '  u.\n')
    with pytest.warns(semi.SemIWarning):
        semi.load(str(p))


def test_roles(tmp_path):
    p = tmp_path / 'a.smi'
    p.write_text(
            'variables:\n'
            '  i.\n'
            'roles:\n'
            '  ARG0 : i.\n'
            '  CARG : string.')
    s = semi.load(str(p))
    assert len(s.roles) == 2
    assert all([r in s.roles for r in ('ARG0', 'CARG')])
    assert s.roles['ARG0'] == 'i'
    assert s.roles['CARG'] == 'string'
    # redefinition
    p.write_text(
            'variables:\n'
            '  i.\n'
            'roles:\n'
            '  ARG0 : i.\n'
            '  ARG0 : i.\n')
    with pytest.warns(semi.SemIWarning):
        semi.load(str(p))


def test_predicates(tmp_path):
    p = tmp_path / 'a.smi'
    p.write_text(
            'variables:\n'
            '  u.\n'
            '  i < u.\n'
            '  p < u.\n'
            '  e < i.\n'
            '  x < i : IND bool.\n'
            'properties:\n'
            '  bool.\n'
            '  + < bool.\n'
            'roles:\n'
            '  ARG0 : i.\n'
            '  ARG1 : u.\n'
            '  ARG2 : u.\n'
            '  ARG3 : u.\n'
            'predicates:\n'
            '  existential_q.\n'
            '  _the_q < existential_q.\n'
            '  _predicate_n_1 : ARG0 x { IND + }.\n'
            '  _predicate_v_of : ARG0 e, ARG1 i, ARG2 p, [ ARG3 i ].\n'
            '  _predominant_a_1 : ARG0 e, ARG1 e.\n'
            '  _predominant_a_1 : ARG0 e, ARG1 p.')
    s = semi.load(str(p))
    assert set(s.predicates) == {'existential_q', '_the_q', '_predicate_n_1',
                                 '_predicate_v_of', '_predominant_a_1'}
    assert s.predicates.parents('_the_q') == ('existential_q',)
    assert s.predicates.parents('_predicate_n_1') == ('*top*',)
    assert s.predicates.parents('_predicate_v_of') == ('*top*',)
    assert s.predicates.parents('_predominant_a_1') == ('*top*',)
    assert len(s.predicates['_the_q']) == 0
    assert len(s.predicates['_predicate_n_1']) == 1
    assert len(s.predicates['_predicate_v_of']) == 1
    assert len(s.predicates['_predominant_a_1']) == 2


def test_include(tmp_path):
    a = tmp_path / 'a.smi'
    b = tmp_path / 'b.smi'
    sub = tmp_path / 'sub'
    sub.mkdir()
    c = sub / 'c.smi'
    d = sub / 'd.smi'
    a.write_text(
            'predicates:\n'
            '  abstract_q : ARG0 x, RSTR h, BODY h.\n'
            '  can_able.\n'
            '  _able_a_1 < can_able.\n'
            'include: b.smi\n'
            'include: sub/c.smi')
    b.write_text(
            'predicates:\n'
            '  existential_q < abstract_q.\n'
            '  _able_a_1 : ARG0 e, ARG1 p.')
    c.write_text(
            'predicates:\n'
            '  universal_q < abstract_q\n'
            '  _able_a_1 : ARG0 e, ARG1 i, ARG2 h.\n'
            'include: d.smi')
    d.write_text(
            'variables:\n'
            '  u.\n'
            '  i < u.\n'
            '  p < u.\n'
            '  h < p.\n'
            '  e < i.\n'
            '  x < i.\n'
            'properties:\n'
            '  tense.\n'
            '  pres < tense.\n'
            'roles:\n'
            '  ARG0 : i.\n'
            '  ARG1 : u.\n'
            '  ARG2 : u.\n'
            '  RSTR : h.\n'
            '  BODY : h.')
    s = semi.load(str(a))
    assert len(s.variables) == 6
    assert len(s.properties) == 2
    assert len(s.roles) == 5
    assert 'abstract_q' in s.predicates
    assert 'existential_q' in s.predicates
    assert 'can_able' in s.predicates
    assert '_able_a_1' in s.predicates
    assert 'can_able' in s.predicates.parents('_able_a_1')
    assert len(s.predicates['_able_a_1']) == 2
    # redefinition
    a.write_text(
            'variables:\n'
            '  i.\n'
            'include: b.smi\n')
    b.write_text(
            'variables:\n'
            '  i.\n')
    with pytest.warns(semi.SemIWarning):
        semi.load(str(a))


def test_comments(tmp_path):
    p = tmp_path / 'a.smi'
    p.write_text(
            '; comment\n'
            'variables:\n'
            '  ; comment\n'
            '  u.\n'
            '  ; x < u.\n'
            '  i < u.\n'
            '  e < i.\n')
    s = semi.load(str(p))
    assert len(s.variables) == 3
    assert 'x' not in s.variables


def test_consistency():
    from delphin import hierarchy
    # invalid hierarchy
    with pytest.raises(hierarchy.HierarchyError):
        semi.SemI(variables={'u': {'parents': []},
                             'i': {'parents': ['u', 'i']}})
    # undeclared variable
    with pytest.raises(semi.SemIError):
        semi.SemI(roles={'ARG0': {'value': 'i'}})
    # undeclared role
    with pytest.raises(semi.SemIError):
        semi.SemI(
            variables={'u': {'parents': []},
                       'i': {'parents': ['u']}},
            predicates={
                '_predicate_n_1': {
                    'parents': [],
                    'synopses': [
                        {'roles': [{'name': 'ARG0', 'value': 'i'}]}]}})
    # undeclared properties
    with pytest.raises(semi.SemIError):
        semi.SemI(
            variables={'u': {'parents': []},
                       'i': {'parents': ['u']}},
            roles={'ARG0': {'value': 'i'}},
            predicates={
                '_predicate_n_1': {
                    'parents': [],
                    'synopses': [
                        {'roles': [{'name': 'ARG0',
                                    'value': 'i',
                                    'properties': {'IND': '+'}}]}]}})
    # undeclared property value
    with pytest.raises(semi.SemIError):
        semi.SemI(
            variables={'u': {'parents': []},
                       'i': {'parents': ['u'],
                             'properties': [['IND', 'bool']]}},
            roles={'ARG0': {'value': 'i'}},
            properties={'bool': {'parents': []}},
            predicates={
                '_predicate_n_1': {
                    'parents': [],
                    'synopses': [
                        {'roles': [{'name': 'ARG0',
                                    'value': 'i',
                                    'properties': {'IND': '+'}}]}]}})


def test_to_dict(tmp_path):
    p = tmp_path / 'a.smi'
    p.write_text(
            'variables:\n'
            '  u.\n'
            '  i < u.\n'
            '  p < u.\n'
            '  e < i : TENSE tense.\n'
            '  x < i & p : IND bool.\n'
            'properties:\n'
            '  tense.\n'
            '  pres < tense.\n'
            '  bool.\n'
            '  + < bool.\n'
            'roles:\n'
            '  ARG0 : i.\n'
            '  ARG1 : u.\n'
            '  ARG2 : u.\n'
            '  ARG3 : u.\n'
            'predicates:\n'
            '  existential_q.\n'
            '  _the_q < existential_q.\n'
            '  _predicate_n_1 : ARG0 x { IND + }.\n'
            '  _predicate_v_of : ARG0 e, ARG1 i, ARG2 p, [ ARG3 i ].\n'
            '  _predominant_a_1 : ARG0 e, ARG1 e.\n'
            '  _predominant_a_1 : ARG0 e, ARG1 p.')
    s = semi.load(str(p))
    d = s.to_dict()
    assert set(d) == {'variables', 'roles', 'properties', 'predicates'}
    assert d['variables'] == {
        'u': {},
        'i': {'parents': ['u']},
        'p': {'parents': ['u']},
        'e': {'parents': ['i'], 'properties': [['TENSE', 'tense']]},
        'x': {'parents': ['i', 'p'], 'properties': [['IND', 'bool']]}
    }
    assert d['properties'] == {
        'tense': {},
        'pres': {'parents': ['tense']},
        'bool': {},
        '+': {'parents': ['bool']}
    }
    assert d['roles'] == {
        'ARG0': {'value': 'i'},
        'ARG1': {'value': 'u'},
        'ARG2': {'value': 'u'},
        'ARG3': {'value': 'u'}
    }
    assert set(d['predicates']) == {
        'existential_q', '_the_q', '_predicate_n_1', '_predicate_v_of',
        '_predominant_a_1'
    }
    assert d['predicates']['existential_q'] == {}
    assert d['predicates']['_the_q'] == {
        'parents': ['existential_q'],
    }
    assert d['predicates']['_predicate_n_1'] == {
        'synopses': [
            {
                'roles': [
                    {'name': 'ARG0', 'value': 'x',
                     'properties': {'IND': '+'}}
                ]
            }
        ]
    }
    assert d['predicates']['_predicate_v_of'] == {
        'synopses': [
            {
                'roles': [
                    {'name': 'ARG0', 'value': 'e'},
                    {'name': 'ARG1', 'value': 'i'},
                    {'name': 'ARG2', 'value': 'p'},
                    {'name': 'ARG3', 'value': 'i', 'optional': True}
                ]
            }
        ]
    }
    assert d['predicates']['_predominant_a_1'] == {
        'synopses': [
            {
                'roles': [
                    {'name': 'ARG0', 'value': 'e'},
                    {'name': 'ARG1', 'value': 'e'}
                ]
            },
            {
                'roles': [
                    {'name': 'ARG0', 'value': 'e'},
                    {'name': 'ARG1', 'value': 'p'}
                ]
            }
        ]
    }


def test_from_dict(tmp_path):
    p = tmp_path / 'a.smi'
    p.write_text(
            'variables:\n'
            '  u.\n'
            '  i < u.\n'
            '  p < u.\n'
            '  e < i : TENSE tense.\n'
            '  x < i & p : IND bool.\n'
            'properties:\n'
            '  tense.\n'
            '  pres < tense.\n'
            '  bool.\n'
            '  + < bool.\n'
            'roles:\n'
            '  ARG0 : i.\n'
            '  ARG1 : u.\n'
            '  ARG2 : u.\n'
            '  ARG3 : u.\n'
            'predicates:\n'
            '  existential_q.\n'
            '  _the_q < existential_q.\n'
            '  _predicate_n_1 : ARG0 x { IND + }.\n'
            '  _predicate_v_of : ARG0 e, ARG1 i, ARG2 p, [ ARG3 i ].\n'
            '  _predominant_a_1 : ARG0 e, ARG1 e.\n'
            '  _predominant_a_1 : ARG0 e, ARG1 p.')
    s1 = semi.load(str(p))
    s2 = semi.SemI.from_dict({
        'variables': {
            'u': {},
            'i': {'parents': ['u']},
            'p': {'parents': ['u']},
            'e': {'parents': ['i'], 'properties': [('TENSE', 'tense')]},
            'x': {'parents': ['i', 'p'], 'properties': [['IND', 'bool']]}
        },
        'properties': {
            'tense': {},
            'pres': {'parents': ['tense']},
            'bool': {},
            '+': {'parents': ['bool']}
        },
        'roles': {
            'ARG0': {'value': 'i'},
            'ARG1': {'value': 'u'},
            'ARG2': {'value': 'u'},
            'ARG3': {'value': 'u'}
        },
        'predicates': {
            'existential_q': {},
            '_the_q': {
                'parents': ['existential_q']
            },
            '_predicate_n_1': {
                'synopses': [
                    {'roles': [{'name': 'ARG0', 'value': 'x', 'properties': {'IND': '+'}}]}
                ]
            },
            '_predicate_v_of': {
                'synopses': [
                    {
                        'roles': [
                            {'name': 'ARG0', 'value': 'e'},
                            {'name': 'ARG1', 'value': 'i'},
                            {'name': 'ARG2', 'value': 'p'},
                            {'name': 'ARG3', 'value': 'i', 'optional': True}
                        ]
                    }
                ]
            },
            '_predominant_a_1': {
                'parents': [],
                'synopses': [
                    {
                        'roles': [
                            {'name': 'ARG0', 'value': 'e'},
                            {'name': 'ARG1', 'value': 'e'}
                        ]
                    },
                    {
                        'roles': [
                            {'name': 'ARG0', 'value': 'e'},
                            {'name': 'ARG1', 'value': 'p'}
                        ]
                    }
                ]
            }
        }
    })
    assert s1.variables == s2.variables
    assert s1.properties == s2.properties
    assert s1.roles == s2.roles
    assert s1.predicates == s2.predicates
