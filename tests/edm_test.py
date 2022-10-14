
from typing import Tuple

from delphin.codecs import eds
from delphin.edm import compute

golds = eds.loads('''
  {e2:
   _1:proper_q<0:3>[BV x3]
   x3:named<0:3>("Kim"){x PERS 3, NUM sg, IND +}[]
   e10:_study_v_1<4:11>{e SF prop, TENSE past, MOOD indicative, PROG -, PERF -}[ARG1 x3]
   e12:_for_p<12:15>{e SF prop, TENSE untensed, MOOD indicative, PROG -, PERF -}[ARG1 e10, ARG2 x13]
   e2:_and_c<16:19>{e SF prop, TENSE past, MOOD indicative, PROG -, PERF -}[L-HNDL e10, L-INDEX e10, R-HNDL e14, R-INDEX e14]
   e14:_pass_v_1<20:26>{e SF prop, TENSE past, MOOD indicative, PROG -, PERF -}[ARG1 x3, ARG2 x13]
   _2:def_explicit_q<27:30>[BV x13]
   e20:poss<27:30>{e SF prop, TENSE untensed, MOOD indicative, PROG -, PERF -}[ARG1 x13, ARG2 x21]
   _3:pronoun_q<27:30>[BV x21]
   x21:pron<27:30>{x PERS 3, NUM sg, GEND f, PT std}[]
   x13:_test_n_of<31:36>{x PERS 3, NUM sg, IND +}[]}
''')

tests = eds.loads('''
  {e9:
   _1:proper_q<0:3>[BV x3]
   x3:named<0:3>("Kim"){x PERS 3, NUM sg, IND +}[]
   e9:_study_v_1<4:11>{e SF prop, TENSE past, MOOD indicative, PROG -, PERF -}[ARG1 x3]
   e11:_for_p<12:15>{e SF prop, TENSE untensed, MOOD indicative, PROG -, PERF -}[ARG1 e9, ARG2 x12]
   e2:_and_c<16:19>{e SF prop, TENSE past, MOOD indicative, PROG -, PERF -}[ARG1 e9, ARG2 e13]
   e13:_pass_v_1<20:26>{e SF prop, TENSE past, MOOD indicative, PROG -, PERF -}[ARG1 x3, ARG2 x12]
   _2:def_explicit_q<27:30>[BV x12]
   e18:poss<27:30>{e SF prop, TENSE untensed, MOOD indicative, PROG -, PERF -}[ARG1 x12, ARG2 x19]
   _3:pronoun_q<27:30>[BV x19]
   x19:pron<27:30>{x PERS 3, NUM sg, GEND f, IND +, PT std}[]
   x12:_test_n_of<31:36>{x PERS 3, NUM sg, IND +}[]}
''')


def edm_sig3(*args, **kwargs) -> Tuple[float, float, float]:
    p, r, f = compute(*args, **kwargs)
    return round(p, 3), round(r, 3), round(f, 3)


def test_edm_from_eds():
    assert edm_sig3(golds, tests) == (0.934, 0.919, 0.927)
    assert edm_sig3(golds, tests, name_weight=0) == (0.920, 0.902, 0.911)
    assert edm_sig3(golds, tests, argument_weight=0) == (0.959, 0.979, 0.969)
    assert edm_sig3(golds, tests, constant_weight=0) == (0.933, 0.918, 0.926)
    assert edm_sig3(golds, tests, top_weight=0) == (0.950, 0.934, 0.942)
