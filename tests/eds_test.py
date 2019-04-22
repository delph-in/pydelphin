
import pytest

from delphin.eds import EDS, Node, Edge


@pytest.fixture
def dogs_bark():
    return {
        'top': '_1',
        'nodes': [Node('_1', '_bark_v_1', type='e'),
                  Node('_2', 'udef_q'),
                  Node('_3', '_dog_n_1', type='x')],
        'edges': [Edge('_1', '_3', 'ARG1'),
                  Edge('_2', '_3', 'BV')]}


def test_empty_EDS():
    d = EDS()
    assert d.top is None
    assert d.nodes == []
    assert d.edges == []


def test_basic_EDS(dogs_bark):
    d = EDS(**dogs_bark)
    assert d.top == '_1'
    assert len(d.nodes) == 3
    assert d.nodes[0].predicate == '_bark_v_1'
    assert d.nodes[1].predicate == 'udef_q'
    assert d.nodes[2].predicate == '_dog_n_1'
    assert len(d.edges) == 2
    assert d.edges[0].role == 'ARG1'
    assert d.edges[1].role == 'BV'
