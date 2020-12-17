
import pytest

from delphin.eds import EDS, Node, from_mrs, EDSWarning
from delphin.mrs import MRS, EP, HCons


@pytest.fixture
def dogs_bark():
    return {
        'top': 'e2',
        'nodes': [Node('e2', '_bark_v_1', type='e', edges={'ARG1': 'x4'}),
                  Node('_1', 'udef_q', edges={'BV': 'x4'}),
                  Node('x4', '_dog_n_1', type='x')]
    }


@pytest.fixture
def dogs_bark_mrs():
    return MRS(
        top='h0',
        index='e2',
        rels=[EP('_bark_v_1', label='h1', args={'ARG0': 'e2', 'ARG1': 'x4'}),
              EP('udef_q', label='h3',
                 args={'ARG0': 'x4', 'RSTR': 'h5', 'BODY': 'h6'}),
              EP('_dog_n_1', label='h7', args={'ARG0': 'x4'})],
        hcons=[HCons.qeq('h0', 'h1'), HCons.qeq('h5', 'h7')]
    )


def test_empty_EDS():
    d = EDS()
    assert d.top is None
    assert d.nodes == []


def test_basic_EDS(dogs_bark):
    d = EDS(**dogs_bark)
    assert d.top == 'e2'
    assert len(d.nodes) == 3

    assert d.nodes[0].predicate == '_bark_v_1'
    assert d.nodes[1].predicate == 'udef_q'
    assert d.nodes[2].predicate == '_dog_n_1'

    assert d.nodes[0].edges == {'ARG1': 'x4'}
    assert d.nodes[1].edges == {'BV': 'x4'}
    assert d.nodes[2].edges == {}

    assert len(d.edges) == 2
    assert d.edges[0] == ('e2', 'ARG1', 'x4')
    assert d.edges[1] == ('_1', 'BV', 'x4')


def test_from_mrs(dogs_bark, dogs_bark_mrs):
    d = from_mrs(dogs_bark_mrs)
    e = EDS(**dogs_bark)
    assert d[d.top] == e[e.top] and d.nodes == e.nodes
    assert d == e

    # recover TOP from INDEX
    dogs_bark_mrs.top = None
    d = from_mrs(dogs_bark_mrs)
    e = EDS(**dogs_bark)
    assert d == e

    # no TOP or INDEX
    dogs_bark_mrs.index = None
    with pytest.warns(EDSWarning):
        d = from_mrs(dogs_bark_mrs)
    e = EDS(**{'top': None, 'nodes': dogs_bark['nodes']})
    assert d == e

def test_from_mrs_broken_hcons_issue_319(dogs_bark_mrs):
    # broken top
    dogs_bark_mrs.rels[0].label = 'h99'
    with pytest.warns(EDSWarning):
        d = from_mrs(dogs_bark_mrs)
    assert d.top == 'e2'

    # it probably rained
    m = MRS(
        top='h0',
        index='e2',
        rels=[EP('_probable_a_1', label='h1', args={'ARG0': 'i4', 'ARG1': 'h5'}),
              EP('_rain_v_1', label='h6', args={'ARG0': 'e2'})],
        hcons=[HCons.qeq('h0', 'h1'), HCons.qeq('h5', 'h6')]
    )
    # no warning normally
    e = from_mrs(m)
    # broken hcons
    m.rels[1].label = 'h99'
    with pytest.warns(EDSWarning):
        d = from_mrs(m)
    assert len(d.nodes) == 2
    assert len(d.arguments()['i4']) == 0
