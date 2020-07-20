
import pytest

from delphin.lnk import Lnk
from delphin.mrs import (
    MRS,
    EP,
    HCons)
from delphin.codecs import indexedmrs
from delphin import semi


@pytest.fixture
def simple_semi():
    return semi.SemI.from_dict({
        'variables': {
            'u': {'parents': []},
            'p': {'parents': ['u']},
            'h': {'parents': ['p']},
            'i': {'parents': ['u']},
            'e': {'parents': ['i'], 'properties': [
                ['SF', 'iforce'],
                ['TENSE', 'tense'],
                ['MOOD', 'mood'],
                ['PROG', 'bool'],
                ['PERF', 'bool']]},
            'x': {'parents': ['i', 'p'], 'properties': [
                ['PERS', 'person'],
                ['NUM', 'number'],
                ['IND', 'bool']]}
        },
        'properties': {
            'tense': {'parents': []},
            'pres': {'parents': ['tense']},
            'past': {'parents': ['tense']},
            'iforce': {'parents': []},
            'prop': {'parents': ['iforce']},
            'mood': {'parents': []},
            'indicative': {'parents': ['mood']},
            'person': {'parents': []},
            '1': {'parents': ['person']},
            '2': {'parents': ['person']},
            '3': {'parents': ['person']},
            'number': {'parents': []},
            'sg': {'parents': ['number']},
            'pl': {'parents': ['number']},
            'bool': {'parents': []},
            '+': {'parents': ['bool']},
            '-': {'parents': ['bool']}
        },
        'roles': {
            'ARG0': {'value': 'i'},
            'ARG1': {'value': 'u'},
            'RSTR': {'value': 'h'},
            'BODY': {'value': 'h'},
        },
        'predicates': {
            'existential_q': {'parents': [], 'synopses': []},
            'proper_q': {
                'parents': ['existential_q'],
                'synopses': [
                    {
                        'roles': [
                            {'name': 'ARG0', 'value': 'x'},
                            {'name': 'RSTR', 'value': 'h'},
                            {'name': 'BODY', 'value': 'h'}
                        ]
                    }
                ]
            },
            'named': {
                'parents': [],
                'synopses': [
                    {
                        'roles': [
                            {'name': 'ARG0', 'value': 'x',
                             'properties': [['IND', '+']]}
                        ]
                    }
                ]
            },
            '_bark_v_1': {
                'parents': [],
                'synopses': [
                    {
                        'roles': [
                            {'name': 'ARG0', 'value': 'e'},
                            {'name': 'ARG1', 'value': 'x'},
                        ]
                    }
                ]
            },
        }
    })


def test_decode(simple_semi):
    m = indexedmrs.decode('''
      < h1, e3:PROP:PAST:INDICATIVE:-:-,
        { h4:proper_q<0:6>(x6:3:SG:+, h5, h7),
          h8:named<0:6>(x6, "Abrams"),
          h2:_bark_v_1<7:14>(e3, x6) },
        { h1 qeq h2,
          h5 qeq h8 } >''', simple_semi)
    assert m.top == 'h1'
    assert m.index == 'e3'
    assert m.rels[0].label == 'h4'
    assert m.rels[0].args['RSTR'] == 'h5'
    assert m.rels[1].carg == 'Abrams'
    assert m.rels[2].predicate == '_bark_v_1'
    assert m.rels[2].args['ARG1'] == 'x6'
    assert m.properties('e3') == {
        'SF': 'PROP',
        'TENSE': 'PAST',
        'MOOD': 'INDICATIVE',
        'PROG': '-',
        'PERF': '-'}


def test_encode(simple_semi):
    m = MRS(top='h1', index='e3',
            rels=[EP('proper_q', label='h4',
                     args={'ARG0': 'x6', 'RSTR': 'h5', 'BODY': 'h7'},
                     lnk=Lnk.charspan(0, 6)),
                  EP('named', label='h8',
                     args={'ARG0': 'x6', 'CARG': 'Abrams'},
                     lnk=Lnk.charspan(0, 6)),
                  EP('_bark_v_1', label='h2',
                     args={'ARG0': 'e3', 'ARG1': 'x6'},
                     lnk=Lnk.charspan(7, 14))],
            hcons=[HCons.qeq('h1', 'h2'), HCons.qeq('h5', 'h8')],
            variables={'e3': {'SF': 'prop', 'TENSE': 'past',
                              'MOOD': 'indicative', 'PROG': '-', 'PERF': '-'},
                       'x6': {'PERS': '3', 'NUM': 'sg', 'IND': '+'}})
    assert indexedmrs.encode(m, simple_semi) == (
        '<h1,e3:PROP:PAST:INDICATIVE:-:-,'
        '{h4:proper_q<0:6>(x6:3:SG:+,h5,h7),'
        'h8:named<0:6>(x6,"Abrams"),'
        'h2:_bark_v_1<7:14>(e3,x6)},'
        '{h1 qeq h2,h5 qeq h8}>')
    assert indexedmrs.encode(m, simple_semi, indent=True) == (
        '< h1, e3:PROP:PAST:INDICATIVE:-:-,\n'
        '  { h4:proper_q<0:6>(x6:3:SG:+, h5, h7),\n'
        '    h8:named<0:6>(x6, "Abrams"),\n'
        '    h2:_bark_v_1<7:14>(e3, x6) },\n'
        '  { h1 qeq h2,\n'
        '    h5 qeq h8 } >')
    assert indexedmrs.encode(m, simple_semi, indent=1) == (
        '< h1, e3:PROP:PAST:INDICATIVE:-:-,\n'
        ' {h4:proper_q<0:6>(x6:3:SG:+, h5, h7),\n'
        '  h8:named<0:6>(x6, "Abrams"),\n'
        '  h2:_bark_v_1<7:14>(e3, x6) },\n'
        ' {h1 qeq h2,\n'
        '  h5 qeq h8 } >')
