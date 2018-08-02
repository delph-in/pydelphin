# -*- coding: utf-8 -*-
"""
Created on Thu Jul 26 17:33:39 2018

@author: aymm
"""

from delphin.mrs import simplemrs, compare

# s1 and s2 differ only by the presence of '_rel' at the end of the predicates
 
s1 = '[ LTOP: h0 INDEX: e2 [ e SF: prop TENSE: past MOOD: indicative PROG: - PERF: - ] RELS: < [ proper_q<0:6> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: sg IND: + ] RSTR: h5 BODY: h6 ]  [ named<0:6> LBL: h7 CARG: "Abrams" ARG0: x3 ]  [ _sleep_v_1<7:13> LBL: h1 ARG0: e2 ARG1: x3 ] > HCONS: < h0 qeq h1 h5 qeq h7 > ]'

s2 = '[ LTOP: h0 INDEX: e2 [ e SF: prop TENSE: past MOOD: indicative PROG: - PERF: - ] RELS: < [ proper_q_rel<0:6> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: sg IND: + ] RSTR: h5 BODY: h6 ]  [ named_rel<0:6> LBL: h7 CARG: "Abrams" ARG0: x3 ]  [ _sleep_v_1_rel<7:13> LBL: h1 ARG0: e2 ARG1: x3 ] > HCONS: < h0 qeq h1 h5 qeq h7 > ]'

x1 = simplemrs.loads_one(s1)
x2 = simplemrs.loads_one(s2)

def test_isomorphic():
    assert x1 == x2 # generally a stricter test than isomorphism
    assert compare.isomorphic(x1, x2) 
    assert compare.isomorphic(x1, x1) 
    assert compare.isomorphic(x2, x2) 
