
from delphin.mrs.xmrs import Xmrs
from delphin.mrs.components import ElementaryPredication as EP, Pred
from delphin.mrs import query

sp = Pred.surface
qeq = lambda hi, lo: (hi, 'qeq', lo)

# "Cats are chased by big dogs." (reordered, but equivalent)
m = Xmrs(
    top='h0',
    eps=[
        EP(10000, sp('udef_q_rel'), 'h4', {'ARG0': 'x3', 'RSTR': 'h5'}),
        EP(10001, sp('"_big_a_1_rel"'), 'h7', {'ARG0': 'e8', 'ARG1': 'x3'}),
        EP(10002, sp('"_dog_n_1_rel"'), 'h7', {'ARG0': 'x3'}),
        EP(10003, sp('"_chase_v_1_rel"'), 'h1', {'ARG0': 'e2', 'ARG1': 'x3', 'ARG2': 'x9'}),
        EP(10004, sp('udef_q_rel'), 'h10', {'ARG0': 'x9', 'RSTR': 'h11'}),
        EP(10005, sp('"_cat_n_1_rel"'), 'h13', {'ARG0': 'x9'})
    ],
    hcons=[qeq('h0', 'h1'), qeq('h5', 'h7'), qeq('h11', 'h13')],
    icons=[('e2', 'topic', 'x9')]
)

def select_nodeids(xmrs, iv=None, label=None, pred=None):
    pass

def test_select_nodeids():
    assert query.select_nodeids(Xmrs()) == []

    assert query.select_nodeids(m) == [10000, 10001, 10002, 10003, 10004, 10005]
    assert query.select_nodeids(m, iv='e2') == [10003]
    assert query.select_nodeids(m, iv='e4') == []
    assert query.select_nodeids(m, pred='"_chase_v_1_rel"') == [10003]
    assert query.select_nodeids(m, pred='udef_q_rel') == [10000, 10004]
    assert query.select_nodeids(m, label='h7') == [10001, 10002]
    assert query.select_nodeids(m, label='h0') == []
    assert query.select_nodeids(m, pred='udef_q_rel', label='h4') == [10000]
    assert query.select_nodeids(m, iv='x3', pred='"_cat_n_1_rel"') == []

def test_select_nodes():
    def nids(nodes):
        return [n.nodeid for n in nodes]

    assert nids(query.select_nodes(Xmrs())) == []
    assert nids(query.select_nodes(Xmrs(), nodeid=10000)) == []

    assert nids(query.select_nodes(m)) == [10000, 10001, 10002, 10003, 10004, 10005]
    assert nids(query.select_nodes(m, nodeid=10000)) == [10000]
    assert nids(query.select_nodes(m, pred='"_chase_v_1_rel"')) == [10003]
    assert nids(query.select_nodes(m, nodeid=10003, pred='"_chase_v_1_rel"')) == [10003]
    assert nids(query.select_nodes(m, nodeid=10003, pred='"_dog_n_1_rel"')) == []

def test_select_eps():
    def nids(eps):
        return [ep.nodeid for ep in eps]

    assert nids(query.select_eps(Xmrs())) == []
    assert nids(query.select_eps(Xmrs(), nodeid=10000)) == []

    assert nids(query.select_eps(m)) == [10000, 10001, 10002, 10003, 10004, 10005]
    assert nids(query.select_eps(m, nodeid=10005)) == [10005]
    assert nids(query.select_eps(m, iv='x3')) == [10000, 10002]
    assert nids(query.select_eps(m, label='h7')) == [10001, 10002]
    assert nids(query.select_eps(m, pred='udef_q_rel')) == [10000, 10004]
    assert nids(query.select_eps(m, iv='x3', pred='udef_q_rel')) == [10000]
    assert nids(query.select_eps(m, iv='x3', label='h7')) == [10002]
    assert nids(query.select_eps(m, iv='x3', label='h7', pred='udef_q_rel')) == []

def test_select_args():
    assert query.select_args(Xmrs()) == []

    assert query.select_args(m) == [
        (10000, 'ARG0', 'x3'), (10000, 'RSTR', 'h5'),
        (10001, 'ARG0', 'e8'), (10001, 'ARG1', 'x3'),
        (10002, 'ARG0', 'x3'),
        (10003, 'ARG0', 'e2'), (10003, 'ARG1', 'x3'), (10003, 'ARG2', 'x9'),
        (10004, 'ARG0', 'x9'), (10004, 'RSTR', 'h11'),
        (10005, 'ARG0', 'x9')
    ]
    assert query.select_args(m, nodeid=10000) == [(10000, 'ARG0', 'x3'), (10000, 'RSTR', 'h5')]
    assert query.select_args(m, rargname='ARG1') == [(10001, 'ARG1', 'x3'), (10003, 'ARG1', 'x3')]
    assert query.select_args(m, value='x9') == [(10003, 'ARG2', 'x9'), (10004, 'ARG0', 'x9'), (10005, 'ARG0', 'x9')]
    assert query.select_args(m, nodeid=10000, rargname='RSTR') == [(10000, 'RSTR', 'h5')]
    assert query.select_args(m, nodeid=10000, value='h5') == [(10000, 'RSTR', 'h5')]
    assert query.select_args(m, nodeid=10000, rargname='ARG2') == []

def test_select_links():
    def ends(ls):
        return [(l.start, l.end) for l in ls]

    assert ends(query.select_links(Xmrs())) == []

    assert ends(query.select_links(m)) == [(0, 10003), (10000, 10002), (10001, 10002), (10003, 10002), (10003, 10005), (10004, 10005)]
    assert ends(query.select_links(m, start=0)) == [(0, 10003)]
    assert ends(query.select_links(m, start=10003)) == [(10003, 10002), (10003, 10005)]
    assert ends(query.select_links(m, end=10002)) == [(10000, 10002), (10001, 10002), (10003, 10002)]
    assert ends(query.select_links(m, rargname='ARG1')) == [(10001, 10002), (10003, 10002)]
    assert ends(query.select_links(m, post='H')) == [(0, 10003), (10000, 10002), (10004, 10005)]
    assert ends(query.select_links(m, start=10003, rargname='ARG1')) == [(10003, 10002)]
    assert ends(query.select_links(m, end=10002, post='H')) == [(10000, 10002)]

def test_select_hcons():
    def hi_los(hcs):
        return sorted(((hc[0], hc[2]) for hc in hcs), key=lambda hc: int(hc[0][1:]))

    assert hi_los(query.select_hcons(Xmrs())) == []

    assert hi_los(query.select_hcons(m)) == [('h0', 'h1'), ('h5', 'h7'), ('h11', 'h13')]
    assert hi_los(query.select_hcons(m, hi='h0')) == [('h0', 'h1')]
    assert hi_los(query.select_hcons(m, lo='h0')) == []
    assert hi_los(query.select_hcons(m, lo='h1')) == [('h0', 'h1')]
    assert hi_los(query.select_hcons(m, relation='qeq')) == [('h0', 'h1'), ('h5', 'h7'), ('h11', 'h13')]
    assert hi_los(query.select_hcons(m, hi='h0', lo='h1')) == [('h0', 'h1')]
    assert hi_los(query.select_hcons(m, hi='h0', lo='h7')) == []

def test_select_icons():
    def l_rs(ics):
        return sorted(ics, key=lambda ic: int(ic[0][1:]))

    assert l_rs(query.select_icons(Xmrs())) == []

    assert l_rs(query.select_icons(m)) == [('e2', 'topic', 'x9')]
    assert l_rs(query.select_icons(m, left='e2')) == [('e2', 'topic', 'x9')]
    assert l_rs(query.select_icons(m, right='x9')) == [('e2', 'topic', 'x9')]
    assert l_rs(query.select_icons(m, relation='topic')) == [('e2', 'topic', 'x9')]
    assert l_rs(query.select_icons(m, relation='focus')) == []
    assert l_rs(query.select_icons(m, left='e2', right='x9')) == [('e2', 'topic', 'x9')]

def test_find_argument_target():
    assert query.find_argument_target(m, 10000, 'RSTR') == 10002
    assert query.find_argument_target(m, 10001, 'ARG1') == 10002
    assert query.find_argument_target(m, 10003, 'ARG2') == 10005

    # test CARGs and unbound vars: "Abrams tried."
    m2 = Xmrs(
        top='h0',
        eps=[
            EP(10000, sp('proper_q_rel'), 'h4', {'ARG0': 'x3', 'RSTR': 'h5'}),
            EP(10001, sp('named_rel'), 'h7', {'ARG0': 'x3', 'CARG': 'Abrams'}),
            EP(10002, sp('"_try_v_1_rel"'), 'h1', {'ARG0': 'e2', 'ARG1': 'x3', 'ARG2': 'i9'}),
        ],
        hcons=[qeq('h0', 'h1'), qeq('h5', 'h7')],
    )
    assert query.find_argument_target(m2, 10001, 'CARG') == 'Abrams'
    assert query.find_argument_target(m2, 10002, 'ARG2') == 'i9'

def test_find_subgraphs_by_pred():
    def f(x, ps, c=None):
        return sorted(
            sorted(r.nodeids())
            for r in query.find_subgraphs_by_preds(x, ps, connected=c)
        )
    assert f(m, ['udef_q_rel', '"_dog_n_1_rel"']) == [[10000, 10002], [10002, 10004]]
    assert f(m, ['udef_q_rel', '"_dog_n_1_rel"'], c=True) == [[10000, 10002]]
    assert f(m, ['udef_q_rel', '"_dog_n_1_rel"', '"_cat_n_1_rel"'], c=True) == []
    assert f(m, ['udef_q_rel', '"_dog_n_1_rel"', 'udef_q_rel', '"_cat_n_1_rel"'], c=True) == []
    assert f(m, ['udef_q_rel', '"_dog_n_1_rel"', '"_chase_v_1_rel"', 'udef_q_rel', '"_cat_n_1_rel"'], c=True) == [[10000, 10002, 10003, 10004, 10005]]

def test_intrinsic_variable():
    # works for quantifiers, too
    assert query.intrinsic_variable(m, 10000) == 'x3'
    assert query.intrinsic_variable(m, 10001) == 'e8'
    assert query.intrinsic_variable(m, 10002) == 'x3'
    assert query.intrinsic_variable(m, 10003) == 'e2'

def test_intrinsic_variables():
    assert query.intrinsic_variables(Xmrs()) == []
    assert query.intrinsic_variables(m) == ['e2', 'x3', 'e8', 'x9']

def test_bound_variables():
    assert query.bound_variables(Xmrs()) == []
    assert query.bound_variables(m) == ['x3', 'x9']

def test_in_labelset():
    assert query.in_labelset(m, [10000]) == True
    assert query.in_labelset(m, [10000, 10002]) == False
    assert query.in_labelset(m, [10001, 10002]) == True
    assert query.in_labelset(m, [10001], 'h7') == True
    assert query.in_labelset(m, [10000], 'h7') == False
    assert query.in_labelset(m, [10001, 10002, 10003]) == False

# deprecated

def test_find_quantifier():
    assert query.find_quantifier(m, 10002) == 10000
    assert query.find_quantifier(m, 10000) == None
    assert query.find_quantifier(m, 10003) == None

def test_get_outbound_args():
    assert query.get_outbound_args(m, 10000) == [(10000, 'RSTR', 'h5')]
    assert query.get_outbound_args(m, 10003) == [(10003, 'ARG1', 'x3'), (10003, 'ARG2', 'x9')]
    assert query.get_outbound_args(m, 10002) == []

def test_nodeid():
    assert query.nodeid(m, 'x3') == 10002
    assert query.nodeid(m, 'x3', quantifier=True) == 10000
    assert query.nodeid(m, 'e2') == 10003
