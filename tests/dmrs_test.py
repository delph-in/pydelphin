
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


class TestNode():
    def test_init(self):
        with pytest.raises(TypeError):
            Node()
        with pytest.raises(TypeError):
            Node(1)
        Node(1, '_dog_n_1')
        Node(1, '_dog_n_1', type='x')
        Node(1, '_dog_n_1', type='x', properties={'NUM': 'sg'})
        Node(1, '_dog_n_1', type='x', properties={'NUM': 'sg'}, carg='Dog')
        Node('1', '_dog_n_1')

    def test__eq__(self):
        n = Node(1, '_dog_n_1', type='x', properties={'NUM': 'sg'})
        assert n == Node(2, '_dog_n_1', type='x', properties={'NUM': 'sg'})
        assert n != Node(1, '_dog_n_2', type='x', properties={'NUM': 'sg'})
        assert n != Node(2, '_dog_n_1', type='e', properties={'NUM': 'sg'})
        assert n != Node(2, '_dog_n_1', type='x', properties={'NUM': 'pl'})

    def test_sortinfo(self):
        n = Node(1, '_dog_n_1')
        assert n.sortinfo == {}
        n = Node(1, '_dog_n_1', type='x')
        assert n.sortinfo == {'cvarsort': 'x'}
        n = Node(1, '_dog_n_1', properties={'NUM': 'sg'})
        assert n.sortinfo == {'NUM': 'sg'}
        n = Node(1, '_dog_n_1', type='x', properties={'NUM': 'sg'})
        assert n.sortinfo == {'cvarsort': 'x', 'NUM': 'sg'}


class TestLink():
    def test_init(self):
        with pytest.raises(TypeError):
            Link()
        with pytest.raises(TypeError):
            Link(1)
        with pytest.raises(TypeError):
            Link(1, 2)
        with pytest.raises(TypeError):
            Link(1, 2, 'ARG1')
        Link(1, 2, 'ARG1', 'EQ')
        Link('1', 2, 'ARG1', 'EQ')
        Link(1, '2', 'ARG1', 'EQ')

    def test__eq__(self):
        link1 = Link(1, 2, 'ARG1', 'EQ')
        assert link1 == Link(1, 2, 'ARG1', 'EQ')
        assert link1 != Link(2, 1, 'ARG1', 'EQ')
        assert link1 != Link(1, 2, 'ARG2', 'EQ')
        assert link1 != Link(1, 2, 'ARG1', 'NEQ')


class TestDMRS():
    def test__init__(self, dogs_bark):
        d = DMRS()
        assert d.top is None
        assert d.index is None
        assert d.nodes == []
        assert d.links == []

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

    def test_arguments(self, dogs_bark):
        d = DMRS()
        assert d.arguments() == {}
        assert d.arguments('h') == {}

        d = DMRS(**dogs_bark)
        assert d.arguments() == {
            10000: [('ARG1', 10002)],
            10001: [('RSTR', 10002)],
            10002: []
        }
        assert d.arguments('h') == {
            10000: [],
            10001: [('RSTR', 10002)],
            10002: []
        }
        assert d.arguments('xei') == {
            10000: [('ARG1', 10002)],
            10001: [],
            10002: []
        }
