
import pytest

from delphin import dmrs


@pytest.fixture
def dogs_bark():
    return {
        'top': 10000,
        'index': 10000,
        'nodes': [dmrs.Node(10000, '_bark_v_1_rel', type='e'),
                  dmrs.Node(10001, 'udef_q_rel'),
                  dmrs.Node(10002, '_dog_n_1_rel', type='x')],
        'links': [dmrs.Link(10000, 10002, 'ARG1', 'NEQ'),
                  dmrs.Link(10001, 10002, 'RSTR', 'H')]}


class TestNode():
    def test_init(self):
        with pytest.raises(TypeError):
            dmrs.Node()
        with pytest.raises(TypeError):
            dmrs.Node(1)
        dmrs.Node(1, '_dog_n_1')
        dmrs.Node(1, '_dog_n_1', type='x')
        dmrs.Node(1, '_dog_n_1', type='x', properties={'NUM': 'sg'})
        dmrs.Node(1, '_dog_n_1', type='x', properties={'NUM': 'sg'}, carg='Dog')
        dmrs.Node('1', '_dog_n_1')

    def test__eq__(self):
        n = dmrs.Node(1, '_dog_n_1', type='x', properties={'NUM': 'sg'})
        assert n == dmrs.Node(2, '_dog_n_1', type='x', properties={'NUM': 'sg'})
        assert n != dmrs.Node(1, '_dog_n_2', type='x', properties={'NUM': 'sg'})
        assert n != dmrs.Node(2, '_dog_n_1', type='e', properties={'NUM': 'sg'})
        assert n != dmrs.Node(2, '_dog_n_1', type='x', properties={'NUM': 'pl'})

    def test_sortinfo(self):
        n = dmrs.Node(1, '_dog_n_1')
        assert n.sortinfo == {}
        n = dmrs.Node(1, '_dog_n_1', type='x')
        assert n.sortinfo == {'cvarsort': 'x'}
        n = dmrs.Node(1, '_dog_n_1', properties={'NUM': 'sg'})
        assert n.sortinfo == {'NUM': 'sg'}
        n = dmrs.Node(1, '_dog_n_1', type='x', properties={'NUM': 'sg'})
        assert n.sortinfo == {'cvarsort': 'x', 'NUM': 'sg'}


class TestLink():
    def test_init(self):
        with pytest.raises(TypeError):
            dmrs.Link()
        with pytest.raises(TypeError):
            dmrs.Link(1)
        with pytest.raises(TypeError):
            dmrs.Link(1, 2)
        with pytest.raises(TypeError):
            dmrs.Link(1, 2, 'ARG1')
        dmrs.Link(1, 2, 'ARG1', 'EQ')
        dmrs.Link('1', 2, 'ARG1', 'EQ')
        dmrs.Link(1, '2', 'ARG1', 'EQ')

    def test__eq__(self):
        link1 = dmrs.Link(1, 2, 'ARG1', 'EQ')
        assert link1 == dmrs.Link(1, 2, 'ARG1', 'EQ')
        assert link1 != dmrs.Link(2, 1, 'ARG1', 'EQ')
        assert link1 != dmrs.Link(1, 2, 'ARG2', 'EQ')
        assert link1 != dmrs.Link(1, 2, 'ARG1', 'NEQ')


class TestDMRS():
    def test__init__(self, dogs_bark):
        d = dmrs.DMRS()
        assert d.top is None
        assert d.index is None
        assert d.nodes == []
        assert d.links == []

        d = dmrs.DMRS(**dogs_bark)
        assert d.top == 10000
        assert d.index == 10000
        assert len(d.nodes) == 3
        assert d.nodes[0].predicate == '_bark_v_1_rel'
        assert d.nodes[1].predicate == 'udef_q_rel'
        assert d.nodes[2].predicate == '_dog_n_1_rel'
        assert len(d.links) == 2
        assert d.links[0].role == 'ARG1'
        assert d.links[1].role == 'RSTR'

        # make sure the old way of marking top still works
        dogs_bark2 = dict(dogs_bark)
        dogs_bark2['links'].append(dmrs.Link(0, dogs_bark['top'], None, 'H'))
        del dogs_bark2['top']
        d2 = dmrs.DMRS(**dogs_bark2)
        assert d.top == d2.top

    def test_arguments(self, dogs_bark):
        d = dmrs.DMRS()
        assert d.arguments() == {}
        assert d.arguments('h') == {}

        d = dmrs.DMRS(**dogs_bark)
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

    def test_scopal_arguments(self, dogs_bark):
        d = dmrs.DMRS()
        assert d.scopal_arguments() == {}

        d = dmrs.DMRS(**dogs_bark)
        assert d.scopal_arguments() == {
            10000: [],
            10001: [('RSTR', 'qeq', 10002)],
            10002: []
        }

        _, scopes = d.scopes()
        scopemap = {}
        for lbl, nodes in scopes.items():
            for node in nodes:
                scopemap[node.id] = lbl
        assert d.scopal_arguments(scopes=scopes) == {
            10000: [],
            10001: [('RSTR', 'qeq', scopemap[10002])],
            10002: []
        }
