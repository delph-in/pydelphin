
import pytest

from delphin.dmrs import DMRS, Node, Link


@pytest.fixture
def dogs_bark():
    return {
        'top': 10000,
        'index': 10000,
        'nodes': [Node(10000, '_bark_v_1_rel', type='e'),
                  Node(10001, 'udef_q_rel'),
                  Node(10002, '_dog_n_1_rel', type='x')],
        'links': [Link(10000, 10002, 'ARG1', 'NEQ'),
                  Link(10001, 10002, 'RSTR', 'H')]}


def test_empty_DMRS():
    d = DMRS()
    assert d.top is None
    assert d.index is None
    assert d.nodes == []
    assert d.links == []


def test_basic_DMRS(dogs_bark):
    d = DMRS(**dogs_bark)
    assert d.top == 10000
    assert d.index == 10000
    assert len(d.nodes) == 3
    assert d.nodes[0].predicate == '_bark_v_1_rel'
    assert d.nodes[1].predicate == 'udef_q_rel'
    assert d.nodes[2].predicate == '_dog_n_1_rel'
    assert len(d.links) == 2
    assert d.links[0].role == 'ARG1'
    assert d.links[1].role == 'RSTR'
