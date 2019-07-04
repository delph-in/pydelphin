
from __future__ import unicode_literals

import io
from pathlib import Path

import pytest

from delphin.commands import (
    convert,
    mkprof,
    process,
    select,
    compare,
    repp,
    CommandError
)


@pytest.fixture
def dir_with_mrs(tmp_path):
    d = tmp_path.joinpath('mrs-dir')
    d.mkdir()
    f = d.joinpath('ex.mrs')
    f.write_text('[ TOP: h0 INDEX: e2 [ e TENSE: past ]'
                 '  RELS: < [ _rain_v_1<3:9> LBL: h1 ARG0: e2 ] >'
                 '  HCONS: < h0 qeq h1 > ]')
    return d


@pytest.fixture
def ace_output():
    return r'''SENT: It rained.
[ LTOP: h0 INDEX: e2 [ e SF: prop TENSE: past MOOD: indicative PROG: - PERF: - ] RELS: < [ _rain_v_1<3:10> LBL: h1 ARG0: e2 ] > HCONS: < h0 qeq h1 > ICONS: < > ] ;  (545 sb-hd_mc_c 1.206314 0 2 (71 it 0.947944 0 1 ("it" 46 "token [ +FORM \"it\" +FROM \"0\" +TO \"2\" +ID *diff-list* [ LIST *list* LAST *list* ] +TNT null_tnt [ +TAGS *null* +PRBS *null* +MAIN tnt_main [ +TAG \"PRP\" +PRB \"1.0\" ] ] +CLASS alphabetic [ +CASE capitalized+lower +INITIAL + ] +TRAIT token_trait [ +UW - +IT italics +LB bracket_null [ LIST *list* LAST *list* ] +RB bracket_null [ LIST *list* LAST *list* ] +LD bracket_null [ LIST *list* LAST *list* ] +RD bracket_null [ LIST *list* LAST *list* ] +HD token_head [ +TI \"<0:2>\" +LL ctype [ -CTYPE- string ] +TG string ] ] +PRED predsort +CARG \"It\" +TICK + +ONSET c-or-v-onset ]")) (544 w_period_plr 0.291582 1 2 (543 v_pst_olr 0.000000 1 2 (57 rain_v1 0.000000 1 2 ("rained." 44 "token [ +FORM \"rained.\" +FROM \"3\" +TO \"10\" +ID *diff-list* [ LIST *list* LAST *list* ] +TNT null_tnt [ +TAGS *null* +PRBS *null* +MAIN tnt_main [ +TAG \"VBD\" +PRB \"1.0\" ] ] +CLASS alphabetic [ +CASE non_capitalized+lower +INITIAL - ] +TRAIT token_trait [ +UW - +IT italics +LB bracket_null [ LIST *list* LAST *list* ] +RB bracket_null [ LIST *list* LAST *list* ] +LD bracket_null [ LIST *list* LAST *list* ] +RD bracket_null [ LIST *list* LAST *list* ] +HD token_head [ +TI \"<3:10>\" +LL ctype [ -CTYPE- string ] +TG string ] ] +PRED predsort +CARG \"rained\" +TICK + +ONSET c-or-v-onset ]")))))
NOTE: 1 readings, added 351 / 20 edges to chart (16 fully instantiated, 10 actives used, 7 passives used)	RAM: 1118k


NOTE: parsed 1 / 1 sentences, avg 1118k, time 0.01857s
'''


@pytest.fixture
def ace_tsdb_stdout():
    return r''' NOTE: tsdb run: (:application . "answer") (:platform . "gcc 4.2") (:grammar . "ERG (2018)") (:avms . 10495) (:lexicon . 40234) (:lrules . 112) (:rules . 250)
(:ninputs . 3) (:p-input . "(1, 0, 1, <0:2>, 1, \"It\", 0, \"null\", \"PRP\" 1.0) (2, 1, 2, <3:9>, 1, \"rained\", 0, \"null\", \"VBD\" 1.0) (3, 2, 3, <9:10>, 1, \".\", 0, \"null\", \".\" 1.0)") (:copies . 144) (:unifications . 40362) (:ntokens . 5) (:p-tokens . "(42, 1, 2, <3:10>, 1, \"rained.\", 0, \"null\") (44, 1, 2, <3:10>, 1, \"rained.\", 0, \"null\") (45, 1, 2, <3:10>, 1, \"rained.\", 0, \"null\") (46, 0, 1, <0:2>, 1, \"it\", 0, \"null\") (47, 0, 1, <0:2>, 1, \"it\", 0, \"null\")") (:results . (((:result-id . 0) (:derivation ." (545 sb-hd_mc_c 1.206314 0 2 (71 it 0.947944 0 1 (\"it\" 46 \"token [ +FORM \\\"it\\\" +FROM \\\"0\\\" +TO \\\"2\\\" +ID *diff-list* [ LIST *list* LAST *list* ] +TNT null_tnt [ +TAGS *null* +PRBS *null* +MAIN tnt_main [ +TAG \\\"PRP\\\" +PRB \\\"1.0\\\" ] ] +CLASS alphabetic [ +CASE capitalized+lower +INITIAL + ] +TRAIT token_trait [ +UW - +IT italics +LB bracket_null [ LIST *list* LAST *list* ] +RB bracket_null [ LIST *list* LAST *list* ] +LD bracket_null [ LIST *list* LAST *list* ] +RD bracket_null [ LIST *list* LAST *list* ] +HD token_head [ +TI \\\"<0:2>\\\" +LL ctype [ -CTYPE- string ] +TG string ] ] +PRED predsort +CARG \\\"It\\\" +TICK + +ONSET c-or-v-onset ]\")) (544 w_period_plr 0.291582 1 2 (543 v_pst_olr 0.000000 1 2 (57 rain_v1 0.000000 1 2 (\"rained.\" 44 \"token [ +FORM \\\"rained.\\\" +FROM \\\"3\\\" +TO \\\"10\\\" +ID *diff-list* [ LIST *list* LAST *list* ] +TNT null_tnt [ +TAGS *null* +PRBS *null* +MAIN tnt_main [ +TAG \\\"VBD\\\" +PRB \\\"1.0\\\" ] ] +CLASS alphabetic [ +CASE non_capitalized+lower +INITIAL - ] +TRAIT token_trait [ +UW - +IT italics +LB bracket_null [ LIST *list* LAST *list* ] +RB bracket_null [ LIST *list* LAST *list* ] +LD bracket_null [ LIST *list* LAST *list* ] +RD bracket_null [ LIST *list* LAST *list* ] +HD token_head [ +TI \\\"<3:10>\\\" +LL ctype [ -CTYPE- string ] +TG string ] ] +PRED predsort +CARG \\\"rained\\\" +TICK + +ONSET c-or-v-onset ]\")))))") (:mrs ."[ LTOP: h0 INDEX: e2 [ e SF: prop TENSE: past MOOD: indicative PROG: - PERF: - ] RELS: < [ _rain_v_1<3:10> LBL: h1 ARG0: e2 ] > HCONS: < h0 qeq h1 > ICONS: < > ]") (:flags ((:ascore . 1.206314) (:probability . 1.000000)))))) (:readings . 1) (:pedges . 16) (:aedges . 4)   (:total . 6) (:treal . 6) (:tcpu . 6) (:others . 1146412)


NOTE: parsed 1 / 1 sentences, avg 1119k, time 0.00654s
'''


@pytest.fixture
def sentence_file(tmp_path):
    f = tmp_path.joinpath('sents.txt')
    f.write_text('A dog barked.\n*Dog barked.')
    return f


def test_convert(dir_with_mrs, mini_testsuite, ace_output, ace_tsdb_stdout,
                 monkeypatch):
    ex = str(dir_with_mrs.joinpath('ex.mrs'))
    with pytest.raises(TypeError):
        convert(ex)
    with pytest.raises(TypeError):
        convert(ex, 'simplemrs')
    with pytest.raises(CommandError):
        convert(ex, 'eds', 'simplemrs')
    with pytest.raises(CommandError):
        convert(ex, 'invalid', 'simplemrs')
    with pytest.raises(CommandError):
        convert(ex, 'simplemrs', 'invalid')
    with pytest.raises(CommandError):
        convert(mini_testsuite, 'simplemrs', 'simplemrs',
                select='result.result-id result.mrs')
    convert(ex, 'simplemrs', 'simplemrs')
    _bidi_convert(dir_with_mrs, 'simplemrs', 'mrx')
    _bidi_convert(dir_with_mrs, 'simplemrs', 'mrs-json')
    convert(ex, 'simplemrs', 'mrs-prolog')
    _bidi_convert(dir_with_mrs, 'simplemrs', 'dmrx')
    convert(ex, 'simplemrs', 'simpledmrs')
    _bidi_convert(dir_with_mrs, 'simplemrs', 'dmrs-json')
    _bidi_convert(dir_with_mrs, 'simplemrs', 'dmrs-penman')
    _bidi_convert(dir_with_mrs, 'simplemrs', 'eds')
    _bidi_convert(dir_with_mrs, 'simplemrs', 'eds-json')
    _bidi_convert(dir_with_mrs, 'simplemrs', 'eds-penman')
    with open(ex) as fh:
        convert(fh, 'simplemrs', 'simplemrs')
    with monkeypatch.context() as m:
        m.setattr('sys.stdin', io.StringIO(ace_output))
        convert(None, 'ace', 'simplemrs')
    with monkeypatch.context() as m:
        m.setattr('sys.stdin', io.StringIO(ace_tsdb_stdout))
        convert(None, 'ace', 'simplemrs')
    convert(ex, 'simplemrs', 'simplemrs', properties=False)
    convert(ex, 'simplemrs', 'simplemrs', color=True)
    convert(ex, 'simplemrs', 'simplemrs', indent=4)
    convert(ex, 'simplemrs', 'eds', show_status=True)
    convert(ex, 'simplemrs', 'eds', predicate_modifiers=True)


def _bidi_convert(d, srcfmt, tgtfmt):
    src = d.joinpath('ex.mrs')
    tgt = d.joinpath('ex.out')
    tgt.write_text(convert(str(src), srcfmt, tgtfmt))
    # below I intend to convert tgtfmt -> tgtfmt
    # because EDS -> non-EDS doesn't work
    convert(str(tgt), tgtfmt, tgtfmt)


def test_mkprof(mini_testsuite, empty_alt_testsuite,
                sentence_file, tmp_path, monkeypatch):
    ts1 = tmp_path.joinpath('ts1')
    ts1.mkdir()
    ts0 = mini_testsuite
    sentence_file = str(sentence_file)

    with pytest.raises(CommandError):
        mkprof(ts1, source=sentence_file)
    with pytest.raises(CommandError):
        mkprof(ts1, source='not a test suite')

    relations = str(Path(mini_testsuite).joinpath('relations'))

    mkprof(ts1, source=ts0)
    mkprof(ts1, source=None, refresh=True)
    with monkeypatch.context() as m:
        m.setattr('sys.stdin', io.StringIO('A dog barked.\n'))
        mkprof(ts1, source=None, refresh=False, schema=relations)
    mkprof(ts1, source=sentence_file, schema=relations)

    mkprof(ts1, source=ts0, full=True)
    mkprof(ts1, source=ts0, skeleton=True)
    mkprof(ts1, source=ts0, full=True, gzip=True)

    mkprof(ts1, refresh=True, schema=empty_alt_testsuite.joinpath('relations'))
    item = ts1.joinpath('item')
    assert item.read_text() == (
        '10@It rained.@1-feb-2018 15:00\n'
        '20@Rained.@01-02-18 15:00:00\n'
        '30@It snowed.@2018-2-1 (15:00:00)\n')
    mkprof(ts1, refresh=True, gzip=True)
    assert not item.with_suffix('').exists()
    assert item.with_suffix('.gz').is_file()


def test_process(mini_testsuite):
    with pytest.raises(TypeError):
        process('grm.dat')
    with pytest.raises(TypeError):
        process(source=mini_testsuite)
    with pytest.raises(CommandError):
        process('grm.dat', mini_testsuite, generate=True, transfer=True)

    # don't have a good way to mock ACE yet


def test_select(mini_testsuite):
    ts0 = mini_testsuite
    with pytest.raises(TypeError):
        select('result.mrs')
    with pytest.raises(TypeError):
        select(testsuite=ts0)
    select('result.mrs', ts0)
    select('parse.i-id result.mrs', ts0)
    from delphin import itsdb
    select('result.result-id mrs', ts0, record_class=itsdb.Row)


def test_compare(mini_testsuite):
    ts0 = mini_testsuite
    with pytest.raises(TypeError):
        compare(ts0)
    with pytest.raises(TypeError):
        compare(gold=ts0)
    compare(ts0, ts0)


def test_repp(sentence_file):
    sentence_file = str(sentence_file)  # Python2
    with pytest.raises(CommandError):
        repp(sentence_file, config='x', module='y')
    with pytest.raises(CommandError):
        repp(sentence_file, config='x', active=['y'])
    repp(sentence_file)
