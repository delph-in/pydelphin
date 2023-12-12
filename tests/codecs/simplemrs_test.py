
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


def test_escapes_issue_367():
    # https://github.com/delph-in/pydelphin/issues/367
    m = simplemrs.decode(
        '[ TOP: h0'
        ' INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]'
        ' RELS: < [ udef_q<0:6> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: sg ] RSTR: h5 BODY: h6 ]'
        '         [ _blue_a_1<0:6> LBL: h7 ARG0: x3 ARG1: i8 ]'
        '         [ _in_p_loc<10:12> LBL: h1 ARG0: e2 ARG1: x3 ARG2: x9 [ x PERS: 3 NUM: sg IND: + ] ]'
        '         [ _this_q_dem<13:17> LBL: h10 ARG0: x9 RSTR: h11 BODY: h12 ]'
        '         [ _folder_n_of<18:25> LBL: h13 ARG0: x9 ARG1: i14 ] >'
        ' HCONS: < h0 qeq h1 h5 qeq h7 h11 qeq h13 > ]'
    )
    m.surface = '"Blue" is in this folder.'
    s = simplemrs.encode(m)
    assert '\\"Blue\\" is in this folder.' in s
    m2 = simplemrs.decode(s)
    assert m == m2
    assert m.surface == m2.surface


def test_legacy_single_quote_predicates_issue_373():
    # https://github.com/delph-in/pydelphin/issues/373
    m = simplemrs.decode("[ RELS: < [ 'single+quoted LBL: h0 ] > ]")
    assert m.rels[0].predicate == "single+quoted"


def test_quote_reserved_characters_issue_372():
    # https://github.com/delph-in/pydelphin/issues/372

    def assert_quoted(p: str, escape: bool = False):
        m = simplemrs.decode(f'[ RELS: < [ "{p}"<1:2> LBL: h0 ] > ]')
        _p = m.rels[0].predicate
        assert (_p.replace('"', r'\"') if escape else _p) == p
        s = simplemrs.encode(m)
        assert f'"{p}"' in s
        simplemrs.decode(s)  # confirm it roundtrips without error

    assert_quoted("a space")
    assert_quoted("a:colon")
    assert_quoted(r'double\"quotes', escape=True)
    assert_quoted("single'quotes")
    assert_quoted("left<angle")
    assert_quoted("right>angle")
    assert_quoted("left[bracket")
    assert_quoted("right]bracket")
