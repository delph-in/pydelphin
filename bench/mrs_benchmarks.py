
from __future__ import print_function
import timeit

from delphin.mrs import simplemrs, dmrx, compare

# load "Does he have anything to do with the campaign?"
print('simplemrs.loads_one'.ljust(50), end='')
print(timeit.timeit(
    'simplemrs.loads_one(\'[ LTOP: h0 INDEX: e2 [ e SF: ques TENSE: pres MOOD: indicative PROG: - PERF: - ] RELS: < [ pron_rel<5:7> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: sg GEND: m PRONTYPE: std_pron ] ]  [ pronoun_q_rel<5:7> LBL: h5 ARG0: x3 RSTR: h6 BODY: h7 ]  [ "_have_v_1_rel"<8:12> LBL: h1 ARG0: e2 ARG1: x3 ARG2: x8 [ x PERS: 3 NUM: sg ] ]  [ thing_rel<13:21> LBL: h9 ARG0: x8 ]  [ _any_q_rel<13:21> LBL: h10 ARG0: x8 RSTR: h11 BODY: h12 ]  [ "_do_v_1_rel"<25:27> LBL: h9 ARG0: e13 [ e SF: prop TENSE: untensed MOOD: indicative PROG: - PERF: - ] ARG1: i14 ARG2: x8 ARG3: h15 ]  [ _with_p_rel<28:32> LBL: h16 ARG0: e17 [ e SF: prop TENSE: untensed MOOD: indicative PROG: - PERF: - ] ARG1: x8 ARG2: x18 [ x PERS: 3 NUM: sg IND: + ] ]  [ _the_q_rel<33:36> LBL: h19 ARG0: x18 RSTR: h20 BODY: h21 ]  [ "_campaign_n_1_rel"<37:46> LBL: h22 ARG0: x18 ] > HCONS: < h0 qeq h1 h6 qeq h4 h11 qeq h9 h15 qeq h16 h20 qeq h22 > ]\')',
    setup='from __main__ import simplemrs',
    number=1000
))
# convert same sentence to DMRS
print('dmrx.dumps_one'.ljust(50), end='')
print(timeit.timeit(
    'dmrx.dumps_one(m)',
    setup='from __main__ import simplemrs, dmrx; m=simplemrs.loads_one(\'[ LTOP: h0 INDEX: e2 [ e SF: ques TENSE: pres MOOD: indicative PROG: - PERF: - ] RELS: < [ pron_rel<5:7> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: sg GEND: m PRONTYPE: std_pron ] ]  [ pronoun_q_rel<5:7> LBL: h5 ARG0: x3 RSTR: h6 BODY: h7 ]  [ "_have_v_1_rel"<8:12> LBL: h1 ARG0: e2 ARG1: x3 ARG2: x8 [ x PERS: 3 NUM: sg ] ]  [ thing_rel<13:21> LBL: h9 ARG0: x8 ]  [ _any_q_rel<13:21> LBL: h10 ARG0: x8 RSTR: h11 BODY: h12 ]  [ "_do_v_1_rel"<25:27> LBL: h9 ARG0: e13 [ e SF: prop TENSE: untensed MOOD: indicative PROG: - PERF: - ] ARG1: i14 ARG2: x8 ARG3: h15 ]  [ _with_p_rel<28:32> LBL: h16 ARG0: e17 [ e SF: prop TENSE: untensed MOOD: indicative PROG: - PERF: - ] ARG1: x8 ARG2: x18 [ x PERS: 3 NUM: sg IND: + ] ]  [ _the_q_rel<33:36> LBL: h19 ARG0: x18 RSTR: h20 BODY: h21 ]  [ "_campaign_n_1_rel"<37:46> LBL: h22 ARG0: x18 ] > HCONS: < h0 qeq h1 h6 qeq h4 h11 qeq h9 h15 qeq h16 h20 qeq h22 > ]\')',
    number=1000
))

print('mrs.compare.isomorphic'.ljust(50), end='')
print(timeit.timeit(
    'compare.isomorphic(m1, m2)',
    setup='from __main__ import simplemrs, compare; m1=simplemrs.loads_one(\'[ LTOP: h0 INDEX: e2 [ e SF: ques TENSE: pres MOOD: indicative PROG: - PERF: - ] RELS: < [ pron_rel<5:7> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: sg GEND: m PRONTYPE: std_pron ] ]  [ pronoun_q_rel<5:7> LBL: h5 ARG0: x3 RSTR: h6 BODY: h7 ]  [ "_have_v_1_rel"<8:12> LBL: h1 ARG0: e2 ARG1: x3 ARG2: x8 [ x PERS: 3 NUM: sg ] ]  [ thing_rel<13:21> LBL: h9 ARG0: x8 ]  [ _any_q_rel<13:21> LBL: h10 ARG0: x8 RSTR: h11 BODY: h12 ]  [ "_do_v_1_rel"<25:27> LBL: h9 ARG0: e13 [ e SF: prop TENSE: untensed MOOD: indicative PROG: - PERF: - ] ARG1: i14 ARG2: x8 ARG3: h15 ]  [ _with_p_rel<28:32> LBL: h16 ARG0: e17 [ e SF: prop TENSE: untensed MOOD: indicative PROG: - PERF: - ] ARG1: x8 ARG2: x18 [ x PERS: 3 NUM: sg IND: + ] ]  [ _the_q_rel<33:36> LBL: h19 ARG0: x18 RSTR: h20 BODY: h21 ]  [ "_campaign_n_1_rel"<37:46> LBL: h22 ARG0: x18 ] > HCONS: < h0 qeq h1 h6 qeq h4 h11 qeq h9 h15 qeq h16 h20 qeq h22 > ]\'); m2=simplemrs.loads_one(\'[ LTOP: h0 INDEX: e2 [ e SF: ques TENSE: pres MOOD: indicative PROG: - PERF: - ] RELS: < [ pron_rel<5:7> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: sg GEND: m PRONTYPE: std_pron ] ]  [ pronoun_q_rel<5:7> LBL: h5 ARG0: x3 RSTR: h6 BODY: h7 ]  [ "_have_v_1_rel"<8:12> LBL: h1 ARG0: e2 ARG1: x3 ARG2: x8 [ x PERS: 3 NUM: sg ] ]  [ thing_rel<13:21> LBL: h9 ARG0: x8 ]  [ _any_q_rel<13:21> LBL: h10 ARG0: x8 RSTR: h11 BODY: h12 ]  [ "_do_v_1_rel"<25:27> LBL: h9 ARG0: e13 [ e SF: prop TENSE: untensed MOOD: indicative PROG: - PERF: - ] ARG1: i14 ARG2: x8 ARG3: h15 ]  [ _with_p_rel<28:32> LBL: h16 ARG0: e17 [ e SF: prop TENSE: untensed MOOD: indicative PROG: - PERF: - ] ARG1: x8 ARG2: x18 [ x PERS: 3 NUM: sg IND: + ] ]  [ _the_q_rel<33:36> LBL: h19 ARG0: x18 RSTR: h20 BODY: h21 ]  [ "_campaign_n_1_rel"<37:46> LBL: h22 ARG0: x18 ] > HCONS: < h0 qeq h1 h6 qeq h4 h11 qeq h9 h15 qeq h16 h20 qeq h22 > ]\')',
    number=100
))
