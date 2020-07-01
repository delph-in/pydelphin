
from datetime import datetime
import io
import gzip

import pytest

from delphin.interface import Processor, Response


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: mark this test as slow"
    )


_simple_relations = '''item:
  i-id :integer :key
  i-input :string

fold:
  fold-id :integer :key

run:
  run-id :integer :key                  # unique test run identifier

parse:
  parse-id :integer :key                # unique parse identifier
  run-id :integer :key                  # test run for this parse
  i-id :integer :key                    # item parsed

result:
  parse-id :integer :key                # parse for this result
  result-id :integer                    # result identifier
  mrs :string                           # MRS for this reading
'''

_alt_relations = '''item:
  i-id :integer :key
  i-input :string
  i-date :date

parse:
  parse-id :integer :key                # unique parse identifier
  run-id :integer :key                  # test run for this parse
  i-id :integer :key                    # item parsed

result:
  parse-id :integer :key                # parse for this result
  result-id :integer                    # result identifier
    mrs :string                           # MRS for this reading'''


@pytest.fixture
def empty_testsuite(tmp_path):
    ts = tmp_path.joinpath('empty')
    ts.mkdir()
    ts.joinpath('relations').write_text(_simple_relations)
    return ts


@pytest.fixture
def empty_alt_testsuite(tmp_path):
    altrels = tmp_path.joinpath('empty_alt')
    altrels.mkdir()
    altrels.joinpath('relations').write_text(_alt_relations)
    return altrels


@pytest.fixture
def single_item_skeleton(tmp_path):
    ts = tmp_path.joinpath('skeleton')
    ts.mkdir()
    ts.joinpath('relations').write_text(_simple_relations)
    ts.joinpath('item').write_text('0@The dog barks.\n')
    return ts


@pytest.fixture
def gzipped_single_item_skeleton(tmp_path):
    ts = tmp_path.joinpath('gz_skeleton')
    ts.mkdir()
    ts.joinpath('relations').write_text(_simple_relations)
    fh = io.TextIOWrapper(
        gzip.GzipFile(str(ts.joinpath('item.gz')), 'w'),
        encoding='utf-8')
    print('0@The dog barks.\n', end='', file=fh)
    fh.close()
    return ts


@pytest.fixture
def single_item_profile(tmp_path):
    ts = tmp_path.joinpath('single')
    ts.mkdir()
    ts.joinpath('relations').write_text(_simple_relations)
    ts.joinpath('item').write_text('0@The dog barks.')
    ts.joinpath('run').write_text('0')
    ts.joinpath('parse').write_text('0@0@0')
    ts.joinpath('result').write_text(
        '0@0@[ LTOP: h0 INDEX: e2 RELS: < '
        '[ _the_q<0:3> LBL: h4 ARG0: x3 RSTR: h5 BODY: h6 ] '
        '[ _dog_n_1<4:7> LBL: h7 ARG0: x3 ] '
        '[ _bark_v_1<8:14> LBL: h1 ARG0: e2 ARG1: x3 ] > '
        'HCONS: < h0 qeq h1 h5 qeq h7 > ]\n')
    return ts


@pytest.fixture
def mini_testsuite(tmp_path):
    ts = tmp_path.joinpath('ts0')
    ts.mkdir()
    rel = ts.joinpath('relations')
    item = ts.joinpath('item')
    parse = ts.joinpath('parse')
    result = ts.joinpath('result')
    rel.write_text(
        'item:\n'
        '  i-id :integer :key\n'
        '  i-input :string\n'
        '  i-wf :integer\n'
        '  i-date :date\n'
        '\n'
        'parse:\n'
        '  parse-id :integer :key\n'
        '  i-id :integer :key\n'
        '  readings :integer\n'
        '\n'
        'result:\n'
        '  parse-id :integer :key\n'
        '  result-id :integer\n'
        '  mrs :string\n')
    item.write_text(
        '10@It rained.@1@1-feb-2018 15:00\n'
        '20@Rained.@0@01-02-18 15:00:00\n'
        '30@It snowed.@1@2018-2-1 (15:00:00)\n')
    parse.write_text(
        '10@10@1\n'
        '20@20@0\n'
        '30@30@1\n')
    result.write_text(
        '10@0@'
        '[ TOP: h0 INDEX: e2 [ e TENSE: past ]'
        '  RELS: < [ _rain_v_1<3:9> LBL: h1 ARG0: e2 ] >'
        '  HCONS: < h0 qeq h1 > ]\n'
        '30@0@'
        '[ TOP: h0 INDEX: e2 [ e TENSE: past ]'
        '  RELS: < [ _snow_v_1<3:9> LBL: h1 ARG0: e2 ] >'
        '  HCONS: < h0 qeq h1 > ]\n')
    return ts


@pytest.fixture
def parser_cpu():
    class DummyParser(Processor):
        task = 'parse'

        def process_item(self, datum, keys=None):
            return Response(
                NOTES=[],
                WARNINGS=[],
                ERRORS=[],
                input='The dog barks',
                surface=None,
                keys={
                    'i-id': 0
                },
                run={
                    'run-id': 0,
                    'platform': 'gcc 4.2',
                    'application': 'ACE 0.9.27 via PyDelphin v0.7.0',
                    'environment': '--tsdb-notes --tsdb-stdout --report-labels',
                    'grammar': 'ERG (1214)',
                    'avms': 9280,
                    'lexicon': 38259,
                    'lrules': 81,
                    'rules': 212,
                    'user': 'goodmami',
                    'host': 'tpy',
                    'os': 'Linux-4.15.0-23-generic-x86_64-with-Ubuntu-18.04-bionic',
                    'start': datetime(2018, 6, 6, 12, 20, 49, 41208),
                    'end': datetime(2018, 6, 6, 12, 20, 49, 97405)
                },
                pedges=31,
                aedges=63,
                ninputs=3,
                ntokens=8,
                tokens={
                    'initial': '(1, 0, 1, <0:3>, 1, "The", 0, "null", "DT" 1.0) (2, 1, 2, <4:7>, 1, "dog", 0, "null", "NN" 1.0) (3, 2, 3, <8:13>, 1, "barks", 0, "null", "VBZ" 1.0)',
                    'internal': '(31, 1, 2, <4:7>, 1, "dog", 0, "null") (33, 2, 3, <8:13>, 1, "barks", 0, "null") (34, 1, 2, <4:7>, 1, "dog", 0, "null") (35, 2, 3, <8:13>, 1, "barks", 0, "null") (36, 0, 1, <0:3>, 1, "the", 0, "null") (37, 1, 2, <4:7>, 1, "dog", 0, "null") (38, 2, 3, <8:13>, 1, "barks", 0, "null") (39, 0, 1, <0:3>, 1, "the", 0, "null")'
                },
                readings=2,
                total=11,
                tcpu=11,
                treal=11,
                unifications=30617,
                copies=171,
                others=980812,
                results=[
                    {
                        'result-id': 0,
                        'derivation': '(731 sb-hd_mc_c 0.404299 0 3 (729 sp-hd_n_c 0.997967 0 2 (51 the_1 -0.486623 0 1 ("the" 36 "token [ +FORM \\"the\\" +FROM \\"0\\" +TO \\"3\\" +ID *diff-list* [ LIST *list* LAST *list* ] +TNT null_tnt [ +TAGS *null* +PRBS *null* +MAIN tnt_main [ +TAG \\"DT\\" +PRB \\"1.0\\" ] ] +CLASS alphabetic [ +INITIAL + +CASE capitalized+lower ] +TRAIT token_trait [ +UW - +IT italics +LB bracket_null +RB bracket_null +HD token_head [ +LL ctype [ -CTYPE- string ] +TG string +TI \\"0\\" ] ] +PRED predsort +CARG \\"The\\" +TICK bool ]")) (728 n_sg_ilr 1.169754 1 2 (40 dog_n1 0.031966 1 2 ("dog" 31 "token [ +FORM \\"dog\\" +FROM \\"4\\" +TO \\"7\\" +ID *diff-list* [ LIST *list* LAST *list* ] +TNT null_tnt [ +TAGS *null* +PRBS *null* +MAIN tnt_main [ +TAG \\"NN\\" +PRB \\"1.0\\" ] ] +CLASS alphabetic [ +INITIAL - +CASE non_capitalized+lower ] +TRAIT token_trait [ +UW - +IT italics +LB bracket_null +RB bracket_null +HD token_head [ +LL ctype [ -CTYPE- string ] +TG string +TI \\"4\\" ] ] +PRED predsort +CARG \\"dog\\" +TICK bool ]")))) (730 v_3s-fin_olr -0.423270 2 3 (43 bark_v1 0.000000 2 3 ("barks" 33 "token [ +FORM \\"barks\\" +FROM \\"8\\" +TO \\"13\\" +ID *diff-list* [ LIST *list* LAST *list* ] +TNT null_tnt [ +TAGS *null* +PRBS *null* +MAIN tnt_main [ +TAG \\"VBZ\\" +PRB \\"1.0\\" ] ] +CLASS alphabetic [ +INITIAL - +CASE non_capitalized+lower ] +TRAIT token_trait [ +UW - +IT italics +LB bracket_null +RB bracket_null +HD token_head [ +LL ctype [ -CTYPE- string ] +TG string +TI \\"8\\" ] ] +PRED predsort +CARG \\"barks\\" +TICK bool ]"))))',
                        'tree': '("S" ("N" ("DET" ("the")) ("N" ("N" ("dog")))) ("VP" ("V" ("barks"))))',
                        'mrs': '[ LTOP: h0 INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ] RELS: < [ _the_q<0:3> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: sg IND: + ] RSTR: h5 BODY: h6 ]  [ _dog_n_1<4:7> LBL: h7 ARG0: x3 ]  [ _bark_v_1<8:13> LBL: h1 ARG0: e2 ARG1: x3 ] > HCONS: < h0 qeq h1 h5 qeq h7 > ]',
                        'flags': [(':ascore', 0.404299), (':probability', 0.830799)]
                    },
                    {
                        'result-id': 1,
                        'derivation': '(735 np_frg_c -1.187003 0 3 (734 sp-hd_n_c -1.354913 0 3 (51 the_1 -1.467909 0 1 ("the" 36 "token [ +FORM \\"the\\" +FROM \\"0\\" +TO \\"3\\" +ID *diff-list* [ LIST *list* LAST *list* ] +TNT null_tnt [ +TAGS *null* +PRBS *null* +MAIN tnt_main [ +TAG \\"DT\\" +PRB \\"1.0\\" ] ] +CLASS alphabetic [ +INITIAL + +CASE capitalized+lower ] +TRAIT token_trait [ +UW - +IT italics +LB bracket_null +RB bracket_null +HD token_head [ +LL ctype [ -CTYPE- string ] +TG string +TI \\"0\\" ] ] +PRED predsort +CARG \\"The\\" +TICK bool ]")) (733 n-hdn_cpd_c -0.345921 1 3 (40 dog_n1 0.000000 1 2 ("dog" 31 "token [ +FORM \\"dog\\" +FROM \\"4\\" +TO \\"7\\" +ID *diff-list* [ LIST *list* LAST *list* ] +TNT null_tnt [ +TAGS *null* +PRBS *null* +MAIN tnt_main [ +TAG \\"NN\\" +PRB \\"1.0\\" ] ] +CLASS alphabetic [ +INITIAL - +CASE non_capitalized+lower ] +TRAIT token_trait [ +UW - +IT italics +LB bracket_null +RB bracket_null +HD token_head [ +LL ctype [ -CTYPE- string ] +TG string +TI \\"4\\" ] ] +PRED predsort +CARG \\"dog\\" +TICK bool ]")) (732 n_pl_olr -0.035850 2 3 (42 bark_n1 0.000000 2 3 ("barks" 33 "token [ +FORM \\"barks\\" +FROM \\"8\\" +TO \\"13\\" +ID *diff-list* [ LIST *list* LAST *list* ] +TNT null_tnt [ +TAGS *null* +PRBS *null* +MAIN tnt_main [ +TAG \\"VBZ\\" +PRB \\"1.0\\" ] ] +CLASS alphabetic [ +INITIAL - +CASE non_capitalized+lower ] +TRAIT token_trait [ +UW - +IT italics +LB bracket_null +RB bracket_null +HD token_head [ +LL ctype [ -CTYPE- string ] +TG string +TI \\"8\\" ] ] +PRED predsort +CARG \\"barks\\" +TICK bool ]"))))))',
                        'tree': '("XP" ("N" ("DET" ("the")) ("N" ("N" ("dog")) ("N" ("N" ("barks"))))))',
                        'mrs': '[ LTOP: h0 INDEX: e2 [ e SF: prop-or-ques TENSE: untensed MOOD: indicative PROG: - PERF: - ] RELS: < [ unknown<0:13> LBL: h1 ARG0: e2 ARG: x4 [ x PERS: 3 NUM: pl ] ]  [ _the_q<0:3> LBL: h5 ARG0: x4 RSTR: h6 BODY: h7 ]  [ compound<4:13> LBL: h8 ARG0: e9 [ e SF: prop TENSE: untensed MOOD: indicative PROG: - PERF: - ] ARG1: x4 ARG2: x10 [ x IND: + ] ]  [ udef_q<4:7> LBL: h11 ARG0: x10 RSTR: h12 BODY: h13 ]  [ _dog_n_1<4:7> LBL: h14 ARG0: x10 ]  [ _bark_n_1<8:13> LBL: h8 ARG0: x4 ] > HCONS: < h0 qeq h1 h6 qeq h8 h12 qeq h14 > ]',
                        'flags': [(':ascore', -1.187003), (':probability', 0.169201)]
                    }
                ]
            )

    return DummyParser()
