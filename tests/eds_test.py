
import pytest

from delphin.eds import EDS, Node


@pytest.fixture
def dogs_bark():
    return {
        'top': '_1',
        'nodes': [Node('_1', '_bark_v_1', type='e', edges={'ARG1': '_3'}),
                  Node('_2', 'udef_q', edges={'BV': '_3'}),
                  Node('_3', '_dog_n_1', type='x')]
    }


def test_empty_EDS():
    d = EDS()
    assert d.top is None
    assert d.nodes == []


def test_basic_EDS(dogs_bark):
    d = EDS(**dogs_bark)
    assert d.top == '_1'
    assert len(d.nodes) == 3

    assert d.nodes[0].predicate == '_bark_v_1'
    assert d.nodes[1].predicate == 'udef_q'
    assert d.nodes[2].predicate == '_dog_n_1'

    assert d.nodes[0].edges == {'ARG1': '_3'}
    assert d.nodes[1].edges == {'BV': '_3'}
    assert d.nodes[2].edges == {}

    assert len(d.edges) == 2
    assert d.edges[0] == ('_1', 'ARG1', '_3')
    assert d.edges[1] == ('_2', 'BV', '_3')
