
from delphin.codecs import simplemrs


def test_decode_nearly(nearly_all_dogs_bark_mrs):
    m = simplemrs.decode(
        '[ <0:21> "Nearly all dogs bark."'
        ' TOP: h0'
        ' INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]'
        ' RELS: <'
        ' [ _nearly_x_deg<0:6> LBL: h4 ARG0: e5 [ e SF: prop TENSE: untensed MOOD: indicative PROG: - PERF: - ] ARG1: u6 ]'
        ' [ _all_q<7:10> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: pl IND: + PT: pt ] RSTR: h7 BODY: h8 ]'
        ' [ _dog_n_1<11:15> LBL: h9 ARG0: x3 ]'
        ' [ _bark_v_1<16:20> LBL: h1 ARG0: e2 ARG1: x3 ] >'
        ' HCONS: < h0 qeq h1 h7 qeq h9 > ]'
    )
    assert m == nearly_all_dogs_bark_mrs


def test_encode_nearly(nearly_all_dogs_bark_mrs):
    assert simplemrs.encode(nearly_all_dogs_bark_mrs) == (
        '[ <0:21> "Nearly all dogs bark."'
        ' TOP: h0'
        ' INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]'
        ' RELS: <'
        ' [ _nearly_x_deg<0:6> LBL: h4 ARG0: e5 [ e SF: prop TENSE: untensed MOOD: indicative PROG: - PERF: - ] ARG1: u6 ]'
        ' [ _all_q<7:10> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: pl IND: + PT: pt ] RSTR: h7 BODY: h8 ]'
        ' [ _dog_n_1<11:15> LBL: h9 ARG0: x3 ]'
        ' [ _bark_v_1<16:20> LBL: h1 ARG0: e2 ARG1: x3 ] >'
        ' HCONS: < h0 qeq h1 h7 qeq h9 > ]'
    )

    assert simplemrs.encode(nearly_all_dogs_bark_mrs, indent=True) == (
        '[ <0:21> "Nearly all dogs bark."\n'
        '  TOP: h0\n'
        '  INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]\n'
        '  RELS: < [ _nearly_x_deg<0:6> LBL: h4 ARG0: e5 [ e SF: prop TENSE: untensed MOOD: indicative PROG: - PERF: - ] ARG1: u6 ]\n'
        '          [ _all_q<7:10> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: pl IND: + PT: pt ] RSTR: h7 BODY: h8 ]\n'
        '          [ _dog_n_1<11:15> LBL: h9 ARG0: x3 ]\n'
        '          [ _bark_v_1<16:20> LBL: h1 ARG0: e2 ARG1: x3 ] >\n'
        '  HCONS: < h0 qeq h1 h7 qeq h9 > ]'
    )


def test_decode_issue_302():
    # https://github.com/delph-in/pydelphin/issues/302

    def assert_predicate(p):
        m = simplemrs.decode(
            '[ TOP: h0 RELS: < [ {}<1:2> LBL: h1 ] > HCONS: < h0 qeq h1 > ]'
            .format(p)
        )
        assert m.rels[0].predicate == p

    assert_predicate(r'_foo:bar_n_1')
    assert_predicate(r'_foo:bar_n')
    # assert_predicate(r'_+-]\?[/NN_u_unknown_rel"')
    # the following originally had NN but preds are case insensitive
    assert_predicate(r'_xml:tm/nn_u_unknown')
    assert_predicate(r'_24/7_n_1')
    assert_predicate(r'_foo<bar_n_1')
    assert_predicate(r'_foo_n_<1:3')
