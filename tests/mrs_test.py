
import pytest

from delphin import mrs
from delphin.codecs import simplemrs


@pytest.fixture
def dogs_bark():
    return {
        'top': 'h0',
        'index': 'e2',
        'rels': [mrs.EP('_bark_v_1', 'h1',
                    args={'ARG0': 'e2', 'ARG1': 'x4'}),
                 mrs.EP('udef_q', 'h3',
                    args={'ARG0': 'x4', 'RSTR': 'h5', 'BODY': 'h7'}),
                 mrs.EP('_dog_n_1', 'h6', args={'ARG0': 'x4'})],
        'hcons': [mrs.HCons.qeq('h0', 'h1'),
                  mrs.HCons.qeq('h5', 'h6')],
        'variables': {
            'e2': {'TENSE': 'pres'},
            'x4': {'NUM': 'pl'}}}


# def test_empty_MRS():
#     m = MRS()
#     assert m.top is None
#     assert m.index is None
#     assert len(m.rels) == 0
#     assert len(m.hcons) == 0
#     assert len(m.icons) == 0
#     assert m.variables == {}


class TestEP():
    def test__init__(self):
        with pytest.raises(TypeError):
            mrs.EP()
        with pytest.raises(TypeError):
            mrs.EP('_dog_n_1')
        mrs.EP('_dog_n_1', 'h3')

    def test__eq__(self):
        ep = mrs.EP('_dog_n_1', 'h3')
        assert ep == mrs.EP('_dog_n_1', 'h3')
        assert ep != mrs.EP('_dog_n_2', 'h3')
        assert ep != mrs.EP('_dog_n_1', 'h4')
        ep = mrs.EP('_chase_v_1', 'h1', {'ARG0': 'e2', 'ARG1': 'x4', 'ARG2': 'x6'})
        assert ep == mrs.EP('_chase_v_1', 'h1',
                        {'ARG0': 'e2', 'ARG1': 'x4', 'ARG2': 'x6'})
        assert ep != mrs.EP('_chase_v_2', 'h1',
                        {'ARG0': 'e2', 'ARG1': 'x4', 'ARG2': 'x6'})
        assert ep != mrs.EP('_chase_v_1', 'h2',
                        {'ARG0': 'e2', 'ARG1': 'x4', 'ARG2': 'x6'})
        assert ep != mrs.EP('_chase_v_1', 'h2',
                        {'ARG0': 'e2', 'ARG1': 'x6', 'ARG2': 'x4'})
        assert ep != mrs.EP('_chase_v_1', 'h2')


class TestMRS():
    def test__init__(self, dogs_bark):
        m = mrs.MRS()
        assert m.top is None
        assert m.index is None
        assert len(m.rels) == 0
        assert len(m.hcons) == 0
        assert len(m.icons) == 0
        assert m.variables == {}

        m = mrs.MRS(**dogs_bark)
        assert m.top == 'h0'
        assert m.index == 'e2'
        assert len(m.rels) == 3
        assert len(m.hcons) == 2
        assert len(m.icons) == 0
        assert m.variables == {
            'h0': {},
            'h1': {},
            'e2': {'TENSE': 'pres'},
            'h3': {},
            'x4': {'NUM': 'pl'},
            'h5': {},
            'h6': {},
            'h7': {}}


@pytest.fixture
def m1():
    # "It rains."
    return simplemrs.decode('''
    [ LTOP: h0
      INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
      RELS: < [ "_rain_v_1_rel"<3:9> LBL: h1 ARG0: e2 ] >
      HCONS: < h0 qeq h1 > ]
    ''')


# m1 but with different Lnk values
@pytest.fixture
def m1b():
    return simplemrs.decode('''
    [ LTOP: h0
      INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
      RELS: < [ "_rain_v_1_rel"<0:6> LBL: h1 ARG0: e2 ] >
      HCONS: < h0 qeq h1 > ]
    ''')


# m1 but with different properties (TENSE)
@pytest.fixture
def m1c():
    return simplemrs.decode('''
    [ LTOP: h0
      INDEX: e2 [ e SF: prop TENSE: past MOOD: indicative PROG: - PERF: - ]
      RELS: < [ "_rain_v_1_rel"<3:9> LBL: h1 ARG0: e2 ] >
      HCONS: < h0 qeq h1 > ]
    ''')


# m1 but with unlinked LTOP
@pytest.fixture
def m1d():
    return simplemrs.decode('''
    [ LTOP: h0
      INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
      RELS: < [ "_rain_v_1_rel"<3:9> LBL: h1 ARG0: e2 ] >
      HCONS: < > ]
    ''')


# m1 but with equated LTOP
@pytest.fixture
def m1e():
    return simplemrs.decode('''
    [ LTOP: h1
      INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
      RELS: < [ "_rain_v_1_rel"<3:9> LBL: h1 ARG0: e2 ] >
      HCONS: < > ]
    ''')


# "It snows." like m1, but with a different pred
@pytest.fixture
def m1f():
    return simplemrs.decode('''
    [ LTOP: h0
      INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
      RELS: < [ "_snow_v_1_rel"<3:9> LBL: h1 ARG0: e2 ] >
      HCONS: < h0 qeq h1 > ]
    ''')


# "It rains (something)" like m1, but with a different arity (in the
# ERG this might be a different _rain_ pred)
@pytest.fixture
def m1g():
    return simplemrs.decode('''
    [ LTOP: h0
      INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
      RELS: < [ "_rain_v_1_rel"<3:9> LBL: h1 ARG0: e2 ARG1: i6] >
      HCONS: < h0 qeq h1 > ]
    ''')


# "The dogs chased the dog."
@pytest.fixture
def m2():
    return simplemrs.decode('''
    [ "The dogs chased the dog."
      TOP: h0
      INDEX: e2 [ e SF: prop TENSE: past MOOD: indicative PROG: - PERF: - ]
      RELS: < [ _the_q<0:3> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: pl IND: + ] RSTR: h5 BODY: h6 ]
              [ _dog_n_1<4:7> LBL: h7 ARG0: x3 ]
              [ _chase_v_1<8:14> LBL: h1 ARG0: e2 ARG1: x3 ARG2: x8 [ x PERS: 3 NUM: sg IND: + ] ]
              [ _the_q<15:18> LBL: h9 ARG0: x8 RSTR: h10 BODY: h11 ]
              [ _dog_n_1<19:23> LBL: h12 ARG0: x8 ] >
      HCONS: < h0 qeq h1 h5 qeq h7 h10 qeq h12 > ]
    ''')  # noqa: E501


# "The dog chased the dogs."
@pytest.fixture
def m2b():
    return simplemrs.decode('''
    [ "The dog chased the dogs."
      TOP: h0
      INDEX: e2 [ e SF: prop TENSE: past MOOD: indicative PROG: - PERF: - ]
      RELS: < [ _the_q<0:3> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: sg IND: + ] RSTR: h5 BODY: h6 ]
              [ _dog_n_1<4:7> LBL: h7 ARG0: x3 ]
              [ _chase_v_1<8:14> LBL: h1 ARG0: e2 ARG1: x3 ARG2: x8 [ x PERS: 3 NUM: pl IND: + ] ]
              [ _the_q<15:18> LBL: h9 ARG0: x8 RSTR: h10 BODY: h11 ]
              [ _dog_n_1<19:23> LBL: h12 ARG0: x8 ] >
      HCONS: < h0 qeq h1 h5 qeq h7 h10 qeq h12 > ]
    ''')  # noqa: E501


# "Dogs and dogs chase dogs and dogs and chase dogs and dog"
# the original sentence had all "dogs", but I changed the final one
# to singular (even if it isn't plausible for the ERG with the rest
# of the configuration) so I can test that local properties don't
# get ignored when comparing overall structure
@pytest.fixture
def pathological1():
    return simplemrs.decode('''
    [ LTOP: h0 INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
      RELS: < [ udef_q_rel<0:13> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: pl ] RSTR: h5 BODY: h6 ]
              [ udef_q_rel<0:4> LBL: h7 ARG0: x8 [ x PERS: 3 NUM: pl IND: + ] RSTR: h9 BODY: h10 ]
              [ "_dog_n_1_rel"<0:4> LBL: h11 ARG0: x8 ]
              [ _and_c_rel<5:8> LBL: h12 ARG0: x3 L-INDEX: x8 R-INDEX: x13 [ x PERS: 3 NUM: pl IND: + ] ]
              [ udef_q_rel<9:13> LBL: h14 ARG0: x13 RSTR: h15 BODY: h16 ]
              [ "_dog_n_1_rel"<9:13> LBL: h17 ARG0: x13 ]
              [ "_chase_v_1_rel"<14:19> LBL: h18 ARG0: e19 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ] ARG1: x3 ARG2: x20 [ x PERS: 3 NUM: pl ] ]
              [ udef_q_rel<20:33> LBL: h21 ARG0: x20 RSTR: h22 BODY: h23 ]
              [ udef_q_rel<20:24> LBL: h24 ARG0: x25 [ x PERS: 3 NUM: pl IND: + ] RSTR: h26 BODY: h27 ]
              [ "_dog_n_1_rel"<20:24> LBL: h28 ARG0: x25 ]
              [ _and_c_rel<25:28> LBL: h29 ARG0: x20 L-INDEX: x25 R-INDEX: x30 [ x PERS: 3 NUM: pl IND: + ] ]
              [ udef_q_rel<29:33> LBL: h31 ARG0: x30 RSTR: h32 BODY: h33 ]
              [ "_dog_n_1_rel"<29:33> LBL: h34 ARG0: x30 ]
              [ _and_c_rel<34:37> LBL: h1 ARG0: e2 L-INDEX: e19 R-INDEX: e35 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ] L-HNDL: h18 R-HNDL: h36 ]
              [ "_chase_v_1_rel"<38:43> LBL: h36 ARG0: e35 ARG1: x3 ARG2: x37 [ x PERS: 3 NUM: pl ] ]
              [ udef_q_rel<44:58> LBL: h38 ARG0: x37 RSTR: h39 BODY: h40 ]
              [ udef_q_rel<44:48> LBL: h41 ARG0: x42 [ x PERS: 3 NUM: pl IND: + ] RSTR: h43 BODY: h44 ]
              [ "_dog_n_1_rel"<44:48> LBL: h45 ARG0: x42 ]
              [ _and_c_rel<49:52> LBL: h46 ARG0: x37 L-INDEX: x42 R-INDEX: x47 [ x PERS: 3 NUM: sg IND: + ] ]
              [ udef_q_rel<53:58> LBL: h48 ARG0: x47 RSTR: h49 BODY: h50 ]
              [ "_dog_n_1_rel"<53:58> LBL: h51 ARG0: x47 ] >
      HCONS: < h0 qeq h1 h5 qeq h12 h9 qeq h11 h15 qeq h17 h22 qeq h29 h26 qeq h28 h32 qeq h34 h39 qeq h46 h43 qeq h45 h49 qeq h51 > ]
    ''')  # noqa: E501


# changed "dogs" to "dog" in a similar local position but different in the
# overall graph:
# "Dogs and dogs chase dogs and dog and chase dogs and dogs"
@pytest.fixture
def pathological2():
    return simplemrs.decode('''
    [ LTOP: h0 INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
      RELS: < [ udef_q_rel<0:13> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: pl ] RSTR: h5 BODY: h6 ]
              [ udef_q_rel<0:4> LBL: h7 ARG0: x8 [ x PERS: 3 NUM: pl IND: + ] RSTR: h9 BODY: h10 ]
              [ "_dog_n_1_rel"<0:4> LBL: h11 ARG0: x8 ]
              [ _and_c_rel<5:8> LBL: h12 ARG0: x3 L-INDEX: x8 R-INDEX: x13 [ x PERS: 3 NUM: pl IND: + ] ]
              [ udef_q_rel<9:13> LBL: h14 ARG0: x13 RSTR: h15 BODY: h16 ]
              [ "_dog_n_1_rel"<9:13> LBL: h17 ARG0: x13 ]
              [ "_chase_v_1_rel"<14:19> LBL: h18 ARG0: e19 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ] ARG1: x3 ARG2: x20 [ x PERS: 3 NUM: pl ] ]
              [ udef_q_rel<20:33> LBL: h21 ARG0: x20 RSTR: h22 BODY: h23 ]
              [ udef_q_rel<20:24> LBL: h24 ARG0: x25 [ x PERS: 3 NUM: pl IND: + ] RSTR: h26 BODY: h27 ]
              [ "_dog_n_1_rel"<20:24> LBL: h28 ARG0: x25 ]
              [ _and_c_rel<25:28> LBL: h29 ARG0: x20 L-INDEX: x25 R-INDEX: x30 [ x PERS: 3 NUM: sg IND: + ] ]
              [ udef_q_rel<29:33> LBL: h31 ARG0: x30 RSTR: h32 BODY: h33 ]
              [ "_dog_n_1_rel"<29:33> LBL: h34 ARG0: x30 ]
              [ _and_c_rel<34:37> LBL: h1 ARG0: e2 L-INDEX: e19 R-INDEX: e35 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ] L-HNDL: h18 R-HNDL: h36 ]
              [ "_chase_v_1_rel"<38:43> LBL: h36 ARG0: e35 ARG1: x3 ARG2: x37 [ x PERS: 3 NUM: pl ] ]
              [ udef_q_rel<44:58> LBL: h38 ARG0: x37 RSTR: h39 BODY: h40 ]
              [ udef_q_rel<44:48> LBL: h41 ARG0: x42 [ x PERS: 3 NUM: pl IND: + ] RSTR: h43 BODY: h44 ]
              [ "_dog_n_1_rel"<44:48> LBL: h45 ARG0: x42 ]
              [ _and_c_rel<49:52> LBL: h46 ARG0: x37 L-INDEX: x42 R-INDEX: x47 [ x PERS: 3 NUM: pl IND: + ] ]
              [ udef_q_rel<53:58> LBL: h48 ARG0: x47 RSTR: h49 BODY: h50 ]
              [ "_dog_n_1_rel"<53:58> LBL: h51 ARG0: x47 ] >
      HCONS: < h0 qeq h1 h5 qeq h12 h9 qeq h11 h15 qeq h17 h22 qeq h29 h26 qeq h28 h32 qeq h34 h39 qeq h46 h43 qeq h45 h49 qeq h51 > ]
    ''')  # noqa: E501


def test_is_isomorphic_identity(m1, m1b, m1c, m1d, m1e, m1f, m1g, m2, m2b):
    assert mrs.is_isomorphic(m1, m1)
    assert mrs.is_isomorphic(m1b, m1b)
    assert mrs.is_isomorphic(m1c, m1c)
    assert mrs.is_isomorphic(m1d, m1d)
    assert mrs.is_isomorphic(m1e, m1e)
    assert mrs.is_isomorphic(m1f, m1f)
    assert mrs.is_isomorphic(m1g, m1g)
    assert mrs.is_isomorphic(m2, m2)
    assert mrs.is_isomorphic(m2b, m2b)


def test_is_isomorphic_lnk(m1, m1b):
    assert mrs.is_isomorphic(m1, m1b)  # diff Lnk only


def test_is_isomorphic_properties(m1, m1c):
    assert not mrs.is_isomorphic(m1, m1c)  # diff TENSE value
    assert mrs.is_isomorphic(m1, m1c, properties=False)


def test_is_isomorphic_top(m1, m1d, m1e):
    assert not mrs.is_isomorphic(m1, m1d)  # unlinked LTOP
    assert not mrs.is_isomorphic(m1, m1e)  # equated LTOP


def test_is_isomorphic_pred(m1, m1f):
    assert not mrs.is_isomorphic(m1, m1f)  # same structure, diff pred


def test_is_isomorphic_arity(m1, m1g):
    assert not mrs.is_isomorphic(m1, m1g)  # diff arity


def test_is_isomorphic_multi_pred(m2):
    assert mrs.is_isomorphic(m2, m2)


def test_is_isomorphic_multi_pred2(m2, m2b):
    assert not mrs.is_isomorphic(m2, m2b)


def test_is_isomorphic_pathological1(pathological1):
    # be aware if the next ones take a long time to resolve
    assert mrs.is_isomorphic(pathological1, pathological1)


def test_is_isomorphic_pathological2(pathological1, pathological2):
    # be aware if the next ones take a long time to resolve
    assert not mrs.is_isomorphic(pathological1, pathological2)


def test_is_isomorphic_recursive():
    m = simplemrs.decode('''
    [ "Kim did not not not not not leave."
      TOP: h0
      INDEX: e2 [ e SF: prop TENSE: past MOOD: indicative PROG: - PERF: - ]
      RELS: < [ proper_q<0:3> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: sg IND: + ] RSTR: h5 BODY: h6 ]
              [ named<0:3> LBL: h7 ARG0: x3 CARG: "Kim" ]
              [ neg<8:11> LBL: h1 ARG0: e9 [ e SF: prop TENSE: untensed MOOD: indicative PROG: - PERF: - ] ARG1: h10 ]
              [ neg<12:15> LBL: h11 ARG0: e12 [ e SF: prop TENSE: untensed MOOD: indicative PROG: - PERF: - ] ARG1: h13 ]
              [ neg<16:19> LBL: h14 ARG0: e15 [ e SF: prop TENSE: untensed MOOD: indicative PROG: - PERF: - ] ARG1: h16 ]
              [ neg<20:23> LBL: h17 ARG0: e18 [ e SF: prop TENSE: untensed MOOD: indicative PROG: - PERF: - ] ARG1: h19 ]
              [ neg<24:27> LBL: h20 ARG0: e21 [ e SF: prop TENSE: untensed MOOD: indicative PROG: - PERF: - ] ARG1: h22 ]
              [ _leave_v_1<28:34> LBL: h23 ARG0: e2 ARG1: x3 ARG2: i24 ] >
      HCONS: < h0 qeq h1 h5 qeq h7 h10 qeq h11 h13 qeq h14 h16 qeq h17 h19 qeq h20 h22 qeq h23 > ]
    ''')  # noqa: E501
    assert mrs.is_isomorphic(m, m)


def test_from_dmrs(dogs_bark):
    from delphin import dmrs
    m = mrs.MRS(**dogs_bark)
    d = dmrs.DMRS(
        top=10002,
        index=10002,
        nodes=[
            dmrs.Node(10000, 'udef_q'),
            dmrs.Node(10001, '_dog_n_1', type='x',
                      properties={'NUM': 'pl'}),
            dmrs.Node(10002, '_bark_v_1', type='e',
                      properties={'TENSE': 'pres'})],
        links=[
            dmrs.Link(10000, 10001, 'RSTR', 'H'),
            dmrs.Link(10002, 10001, 'ARG1', 'NEQ')])
    _m = mrs.from_dmrs(d)

    # Issue #248
    labels = set(ep.label for ep in _m.rels)
    hcons = {hc.hi: hc.lo for hc in _m.hcons}
    assert _m.top not in labels
    assert _m.top in hcons
    assert hcons[_m.top] in labels
    # ensure equivalency
    assert mrs.is_isomorphic(m, _m)

    # try with no hook
    d.top = None
    d.index = None
    # it won't be isomorphic, just check for errors
    _m = mrs.from_dmrs(d)
    assert _m.top is None
    assert _m.index is None
    assert len(_m.rels) == 3
    assert len(_m.hcons) == 1
