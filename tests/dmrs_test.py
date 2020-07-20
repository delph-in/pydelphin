
import pytest

from delphin.codecs import simplemrs
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


def test_from_mrs_it_rains():
    m = simplemrs.decode('''
        [ TOP: h0 INDEX: e2 [e TENSE: pres]
          RELS: < [ _rain_v_1<3:8> LBL: h1 ARG0: e2 ] >
          HCONS: < h0 qeq h1 > ]''')
    d = dmrs.from_mrs(m)
    assert len(d.nodes) == 1
    assert d.nodes[0].predicate == '_rain_v_1'
    assert d.nodes[0].type == 'e'
    assert d.nodes[0].properties == {'TENSE': 'pres'}


def test_from_mrs_nearly_all_cats_were_chased_by_dogs():
    m = simplemrs.decode('''
        [ LTOP: h0
          INDEX: e2 [ e SF: prop TENSE: past MOOD: indicative PROG: - PERF: - ]
          RELS: < [ _nearly_x_deg<0:6> LBL: h4 ARG0: e5 [ e SF: prop TENSE: untensed MOOD: indicative PROG: - PERF: - ] ARG1: u6 ]
                  [ _all_q<7:10> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: pl IND: + ] RSTR: h7 BODY: h8 ]
                  [ _cat_n_1<11:15> LBL: h9 ARG0: x3 ]
                  [ _chase_v_1<21:27> LBL: h1 ARG0: e2 ARG1: x10 [ x PERS: 3 NUM: pl IND: + ] ARG2: x3 ]
                  [ udef_q<31:36> LBL: h11 ARG0: x10 RSTR: h12 BODY: h13 ]
                  [ _dog_n_1<31:36> LBL: h14 ARG0: x10 ] >
          HCONS: < h0 qeq h1 h7 qeq h9 h12 qeq h14 >
          ICONS: < e2 topic x3 > ]''')
    d = dmrs.from_mrs(m)
    assert len(d.nodes) == 6
    n1 = d.nodes[0]
    n2 = d.nodes[1]
    assert n1.predicate == '_nearly_x_deg'
    assert n2.predicate == '_all_q'
    assert any((l.start, l.end, l.role, l.post) == (n1.id, n2.id, 'MOD', 'EQ')
               for l in d.links)


def test_from_mrs_issue_303():
    # https://github.com/delph-in/pydelphin/issues/303
    m = simplemrs.decode('''
        [ TOP: h0 INDEX: e2 [e TENSE: pres]
          RELS: < [ _rain_v_1<3:8> LBL: h1 ARG0: e2 ] >
          HCONS: < > ]''')
    with pytest.warns(dmrs.DMRSWarning):
        d = dmrs.from_mrs(m)
        assert d.top is None

    m = simplemrs.decode('''
        [ TOP: h0 INDEX: e2 [e TENSE: pres]
          RELS: < [ _rain_v_1<3:8> LBL: h1 ARG0: e2 ] >
          HCONS: < h0 qeq h3 > ]''')
    with pytest.warns(dmrs.DMRSWarning):
        d = dmrs.from_mrs(m)
        assert d.top is None

    m = simplemrs.decode('''
        [ LTOP: h0
          INDEX: e2 [ e SF: prop TENSE: past MOOD: indicative PROG: - PERF: - ]
          RELS: < [ neg<7:10> LBL: h1 ARG0: e4 [ e SF: prop TENSE: untensed MOOD: indicative PROG: - PERF: - ] ARG1: h5 ]
                  [ _rain_v_1<11:16> LBL: h6 ARG0: e2 ] >
          HCONS: < h0 qeq h1 h5 qeq h7 >
          ICONS: < > ]''')
    with pytest.warns(dmrs.DMRSWarning):
        d = dmrs.from_mrs(m)
        n = d.nodes[0]
        assert n.predicate == 'neg'
        assert 'ARG1' not in d.scopal_arguments()[n.id]
