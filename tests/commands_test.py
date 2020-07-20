
from __future__ import unicode_literals

import io
import pathlib

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
    return str(d)


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
def item_relations(tmp_path):
    f = tmp_path.joinpath('item-relations')
    f.write_text('''item:
  i-id :integer :key
  i-difficulty :integer
  i-input :string
  i-length :integer
  i-wf :integer
  i-date :date''')
    return f


@pytest.fixture
def sentence_file(tmp_path):
    f = tmp_path.joinpath('sents.txt')
    f.write_text('A dog barked.\n*Dog barked.')
    return str(f)


@pytest.fixture
def csv_file(tmp_path):
    f = tmp_path.joinpath('csv.txt')
    f.write_text(
        'i-wf@i-input@i-date\n'
        '1@A dog barked.@25-may-2020\n'
        '0@Dog barked.@25-may-2020')
    return str(f)


def test_convert(dir_with_mrs, mini_testsuite, ace_output, ace_tsdb_stdout,
                 monkeypatch):
    ex = str(pathlib.Path(dir_with_mrs, 'ex.mrs'))
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
    convert(ex, 'simplemrs', 'eds')
    convert(ex, 'simplemrs', 'eds-json')
    convert(ex, 'simplemrs', 'eds-penman')
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
    src = pathlib.Path(d, 'ex.mrs')
    tgt = pathlib.Path(d, 'ex.out')
    tgt.write_text(convert(str(src), srcfmt, tgtfmt))
    convert(str(tgt), tgtfmt, srcfmt)


def test_mkprof_sentence_file(item_relations, sentence_file, tmp_path):
    ts = tmp_path.joinpath('ts')
    with pytest.raises(CommandError):
        mkprof(ts, source=sentence_file)
    mkprof(ts, source=sentence_file, schema=item_relations)
    assert ts.joinpath('item').read_text() == (
        '1@1@A dog barked.@3@1@\n'
        '2@1@Dog barked.@2@0@\n')


def test_mkprof_csv_file(item_relations, csv_file, tmp_path):
    ts = tmp_path.joinpath('ts')
    with pytest.raises(CommandError):
        mkprof(ts, source=csv_file, delimiter='@')
    mkprof(ts, source=csv_file, delimiter='@', schema=item_relations)
    assert ts.joinpath('item').read_text() == (
        '1@1@A dog barked.@3@1@25-may-2020\n'
        '2@1@Dog barked.@2@0@25-may-2020\n')


def test_mkprof_stdin(item_relations, tmp_path, monkeypatch):
    ts = tmp_path.joinpath('ts')
    with monkeypatch.context() as m:
        m.setattr('sys.stdin', io.StringIO('A dog barked.\n'))
        mkprof(ts, source=None, refresh=False, schema=item_relations)
    assert ts.joinpath('item').read_text() == '1@1@A dog barked.@3@1@\n'


def test_mkprof_refresh(mini_testsuite, empty_alt_testsuite):
    ts = mini_testsuite
    mkprof(ts, source=None, refresh=True)
    mkprof(ts, source=None, refresh=True,
           schema=pathlib.Path(empty_alt_testsuite, 'relations'))
    item = ts.joinpath('item')
    assert item.read_text() == (
        '10@It rained.@1-feb-2018 15:00\n'
        '20@Rained.@01-02-18 15:00:00\n'
        '30@It snowed.@2018-2-1 (15:00:00)\n')
    mkprof(ts, refresh=True, gzip=True)
    assert not item.with_suffix('').exists()
    assert item.with_suffix('.gz').is_file()


def test_mkprof_source(mini_testsuite, tmp_path):
    ts = tmp_path.joinpath('ts')

    with pytest.raises(CommandError):
        mkprof(ts, source='not a test suite')

    mkprof(ts, source=mini_testsuite)
    mkprof(ts, source=mini_testsuite, full=True)
    mkprof(ts, source=mini_testsuite, skeleton=True)
    mkprof(ts, source=mini_testsuite, full=True, gzip=True)


def test_mkprof_issue_273(mini_testsuite, tmp_path):
    # https://github.com/delph-in/pydelphin/issues/273
    from delphin import itsdb
    ts1_ = tmp_path.joinpath('ts1')
    ts1_.mkdir()
    ts1 = str(ts1_)
    ts0 = mini_testsuite
    # this is when the condition occurs on a single row
    mkprof(ts1, source=ts0, full=True, where='mrs ~ "_snow_v_1"')
    item = pathlib.Path(ts1, 'item')
    assert item.read_text() == (
        '30@It snowed.@1@2018-2-1 (15:00:00)\n')
    # this is when the condition occurs on multiple rows
    _ts0 = itsdb.TestSuite(ts0)
    _ts0['parse'].update(2, {'readings': 2})
    _ts0['result'].append(
        (30,
         1,
         '[ TOP: h0 INDEX e2 [ e TENSE: past ]'
         '  RELS: < [ pronoun_q<0:2> LBL h3 ARG0: x4 RSTR: h5 BODY: h6 ]'
         '          [ pron<0:2> LBL: h7 ARG0: x4 ]'
         '          [ _snow_v_1<3:9> LBL: h1 ARG0: e2 ARG1: x4 ] >'
         '  HCONS: < h0 qeq h1 h5 qeq h7 > ]'))
    _ts0.commit()
    mkprof(ts1, source=ts0, full=True, where='mrs ~ "_snow_v_1"')
    item = pathlib.Path(ts1, 'item')
    assert item.read_text() == (
        '30@It snowed.@1@2018-2-1 (15:00:00)\n')


def test_mkprof_issue_288(item_relations, tmp_path):
    # https://github.com/delph-in/pydelphin/issues/288
    ts = tmp_path.joinpath('ts')
    tsv = tmp_path.joinpath('sents')
    tsv.write_text('i-wf\ti-input\ti-date\n'
                   '1\tA dog barked.\t25-may-2020\n'
                   '0\tDog barked.\t25-may-2020')
    mkprof(ts, source=tsv, delimiter='\t', schema=item_relations)
    assert ts.joinpath('item').read_text() == (
        '1@1@A dog barked.@3@1@25-may-2020\n'
        '2@1@Dog barked.@2@0@25-may-2020\n')


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
    sentence_file = sentence_file
    with pytest.raises(CommandError):
        repp(sentence_file, config='x', module='y')
    with pytest.raises(CommandError):
        repp(sentence_file, config='x', active=['y'])
    repp(sentence_file)
