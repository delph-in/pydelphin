
from delphin.mrs import xmrs, path as mp
from delphin.mrs.components import Pred, ElementaryPredication as EP

sp = Pred.stringpred

def qeq(hi, lo): return (hi, 'qeq', lo)

m0 = xmrs.Xmrs()

# "It rains."
m1 = xmrs.Xmrs(
    top='h0',
    eps=[EP(10000, sp('"_rain_v_1_rel"'), 'h1', {'ARG0': 'e2'})],
    hcons=[qeq('h0', 'h1')]
)

# "Big dogs bark."
m2 = xmrs.Xmrs(
    top='h0',
    eps=[
        EP(10000, sp('udef_q_rel'), 'h4', {'ARG0': 'x3', 'RSTR': 'h5'}),
        EP(10001, sp('"_big_a_1_rel"'), 'h7', {'ARG0': 'e8', 'ARG1': 'x3'}),
        EP(10002, sp('"_dog_n_1_rel"'), 'h7', {'ARG0': 'x3'}),
        EP(10003, sp('"_bark_v_1_rel"'), 'h1', {'ARG0': 'e2', 'ARG1': 'x3'})
    ],
    hcons=[qeq('h0', 'h1'), qeq('h5', 'h7')]
)

# "Big scary dogs bark."
m3 = xmrs.Xmrs(
    top='h0',
    eps=[
        EP(10000, sp('udef_q_rel'), 'h4', {'ARG0': 'x3', 'RSTR': 'h5'}),
        EP(10001, sp('"_big_a_1_rel"'), 'h7', {'ARG0': 'e8', 'ARG1': 'x3'}),
        EP(10002, sp('"_scary_a_1_rel"'), 'h7', {'ARG0': 'e9', 'ARG1': 'x3'}),
        EP(10003, sp('"_dog_n_1_rel"'), 'h7', {'ARG0': 'x3'}),
        EP(10004, sp('"_bark_v_1_rel"'), 'h1', {'ARG0': 'e2', 'ARG1': 'x3'})
    ],
    hcons=[qeq('h0', 'h1'), qeq('h5', 'h7')]
)

def test_headed_walk():
    assert list(mp.walk(m0)) == []
    assert list(mp.walk(m1)) == [(0, 10000, ':/H>')]
    assert list(mp.walk(m2)) == [(0, 10003, ':/H>'), (10003, 10002, ':ARG1/NEQ>'), (10002, 10001, '<ARG1/EQ:'), (10002, 10000, '<RSTR/H:')]
    assert list(mp.walk(m2, start=10002)) == [(10002, 10001, '<ARG1/EQ:'), (10002, 10000, '<RSTR/H:')]
    assert list(mp.walk(m3)) == [(0, 10004, ':/H>'), (10004, 10003, ':ARG1/NEQ>'), (10003, 10001, '<ARG1/EQ:'), (10003, 10002, '<ARG1/EQ:'), (10003, 10000, '<RSTR/H:')]

def test_topdown_walk():
    assert list(mp.walk(m0, method='top-down')) == []
    assert list(mp.walk(m1, method='top-down')) == [(0, 10000, ':/H>')]
    assert list(mp.walk(m2, method='top-down')) == [(0, 10003, ':/H>'), (10003, 10002, ':ARG1/NEQ>')]
    assert list(mp.walk(m2, start=10001, method='top-down')) == [(10001, 10002, ':ARG1/EQ>')]
    assert list(mp.walk(m3, method='top-down')) == [(0, 10004, ':/H>'), (10004, 10003, ':ARG1/NEQ>')]

def test_bottomup_walk():
    assert list(mp.walk(m0, method='bottom-up')) == []
    assert list(mp.walk(m1, method='bottom-up')) == []
    assert list(mp.walk(m1, start=10000, method='bottom-up')) == [(10000, 0, '</H:')]
    assert list(mp.walk(m2, start=10002, method='bottom-up')) == [(10002, 10001, '<ARG1/EQ:'), (10002, 10003, '<ARG1/NEQ:'), (10003, 0, '</H:'), (10002, 10000, '<RSTR/H:')]
    assert list(mp.walk(m3, start=10003, method='bottom-up')) == [(10003, 10001, '<ARG1/EQ:'), (10003, 10002, '<ARG1/EQ:'), (10003, 10004, '<ARG1/NEQ:'), (10004, 0, '</H:'), (10003, 10000, '<RSTR/H:')]
