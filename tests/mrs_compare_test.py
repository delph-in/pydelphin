
import pytest

from delphin.mrs import compare, simplemrs

# empty
m0 = simplemrs.decode('''[ ]''')

# "It rains."
m1 = simplemrs.decode('''
[ LTOP: h0
  INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
  RELS: < [ "_rain_v_1_rel"<3:9> LBL: h1 ARG0: e2 ] >
  HCONS: < h0 qeq h1 > ]
''')

# m1 but with different Lnk values
m1b = simplemrs.decode('''
[ LTOP: h0
  INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
  RELS: < [ "_rain_v_1_rel"<0:6> LBL: h1 ARG0: e2 ] >
  HCONS: < h0 qeq h1 > ]
''')

# m1 but with different properties (TENSE)
m1c = simplemrs.decode('''
[ LTOP: h0
  INDEX: e2 [ e SF: prop TENSE: past MOOD: indicative PROG: - PERF: - ]
  RELS: < [ "_rain_v_1_rel"<3:9> LBL: h1 ARG0: e2 ] >
  HCONS: < h0 qeq h1 > ]
''')

# m1 but with unlinked LTOP
m1d = simplemrs.decode('''
[ LTOP: h0
  INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
  RELS: < [ "_rain_v_1_rel"<3:9> LBL: h1 ARG0: e2 ] >
  HCONS: < > ]
''')

# m1 but with equated LTOP
m1e = simplemrs.decode('''
[ LTOP: h1
  INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
  RELS: < [ "_rain_v_1_rel"<3:9> LBL: h1 ARG0: e2 ] >
  HCONS: < > ]
''')

# "It snows." like m1, but with a different pred
m1f = simplemrs.decode('''
[ LTOP: h0
  INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
  RELS: < [ "_snow_v_1_rel"<3:9> LBL: h1 ARG0: e2 ] >
  HCONS: < h0 qeq h1 > ]
''')

# "It rains (something)" like m1, but with a different arity (in the
# ERG this might be a different _rain_ pred)
m1g = simplemrs.decode('''
[ LTOP: h0
  INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
  RELS: < [ "_rain_v_1_rel"<3:9> LBL: h1 ARG0: e2 ARG1: i6] >
  HCONS: < h0 qeq h1 > ]
''')

# "Dogs and dogs chase dogs and dogs and chase dogs and dog"
# the original sentence had all "dogs", but I changed the final one
# to singular (even if it isn't plausible for the ERG with the rest
# of the configuration) so I can test that local properties don't
# get ignored when comparing overall structure
pathological1 = simplemrs.decode('''
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
''')

# changed "dogs" to "dog" in a similar local position but different in the
# overall graph:
# "Dogs and dogs chase dogs and dog and chase dogs and dogs"
pathological2 = simplemrs.decode('''
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
''')

# x1 and x2 differ only by the presence of '_rel' at the end of the predicates

x1 = simplemrs.decode('''
[ LTOP: h0 INDEX: e2 [ e SF: prop TENSE: past MOOD: indicative PROG: - PERF: - ]
  RELS: < [ proper_q<0:6> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: sg IND: + ] RSTR: h5 BODY: h6 ]
          [ named<0:6> LBL: h7 CARG: "Abrams" ARG0: x3 ]
          [ _sleep_v_1<7:13> LBL: h1 ARG0: e2 ARG1: x3 ] >
  HCONS: < h0 qeq h1 h5 qeq h7 > ]
''')

x2 = simplemrs.decode('''
[ LTOP: h0 INDEX: e2 [ e SF: prop TENSE: past MOOD: indicative PROG: - PERF: - ]
  RELS: < [ proper_q_rel<0:6> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: sg IND: + ] RSTR: h5 BODY: h6 ]
          [ named_rel<0:6> LBL: h7 CARG: "Abrams" ARG0: x3 ]
          [ _sleep_v_1_rel<7:13> LBL: h1 ARG0: e2 ARG1: x3 ] >
  HCONS: < h0 qeq h1 h5 qeq h7 > ]
''')

def test_isomorphic():
    assert compare.isomorphic(m1, m1) == True  # identity
    assert compare.isomorphic(m1, m1b) == True  # diff Lnk only
    assert compare.isomorphic(m1, m1c) == False  # diff TENSE value
    assert compare.isomorphic(m1, m1c, check_varprops=False) == True
    assert compare.isomorphic(m1, m1d) == False  # unlinked LTOP
    assert compare.isomorphic(m1, m1e) == False  # equated LTOP
    assert compare.isomorphic(m1, m1f) == False  # same structure, diff pred
    assert compare.isomorphic(m1, m1g) == False  # diff arity
    # be aware if the next ones take a long time to resolve
    assert compare.isomorphic(pathological1, pathological1) == True
    assert compare.isomorphic(pathological1, pathological2) == False
    # test for normalized forms being treated as equivalent by compare.isomorphic
    assert x1 == x2 # generally a stricter test than isomorphism
    assert compare.isomorphic(x1, x2) == True # if normalized
    assert compare.isomorphic(x1, x1) == True # identity
    assert compare.isomorphic(x2, x2) == True # identity
