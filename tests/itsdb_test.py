# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

import os
import datetime
import io
import gzip

import pytest

from delphin.interface import Processor, Response
from delphin import itsdb

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
  mrs :string                           # MRS for this reading
'''


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
                    'start': datetime.datetime(2018, 6, 6, 12, 20, 49, 41208),
                    'end': datetime.datetime(2018, 6, 6, 12, 20, 49, 97405)
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


@pytest.fixture
def empty_profile(tmpdir):
    ts = tmpdir.mkdir('empty')
    ts.join('relations').write(_simple_relations)
    return str(ts)


@pytest.fixture
def single_item_skeleton(tmpdir):
    ts = tmpdir.mkdir('skeleton')
    ts.join('relations').write(_simple_relations)
    ts.join('item').write('0@The dog barks.')
    return str(ts)


@pytest.fixture
def gzipped_single_item_skeleton(tmpdir):
    ts = tmpdir.mkdir('gz_skeleton')
    ts.join('relations').write(_simple_relations)
    fh = io.TextIOWrapper(
        gzip.GzipFile(str(ts.join('item.gz')), 'w'),
        encoding='utf-8')
    print('0@The dog barks.', file=fh)
    fh.close()
    return str(ts)


@pytest.fixture
def single_item_profile(tmpdir):
    ts = tmpdir.mkdir('single')
    ts.join('relations').write(_simple_relations)
    ts.join('item').write('0@The dog barks.')
    ts.join('run').write('0')
    ts.join('parse').write('0@0@0')
    ts.join('result').write(
        '0@0@[ LTOP: h0 INDEX: e2 RELS: < '
        '[ _the_q<0:3> LBL: h4 ARG0: x3 RSTR: h5 BODY: h6 ] '
        '[ _dog_n_1<4:7> LBL: h7 ARG0: x3 ] '
        '[ _bark_v_1<8:14> LBL: h1 ARG0: e2 ARG1: x3 ] > '
        'HCONS: < h0 qeq h1 h5 qeq h7 > ]')
    return str(ts)


def test_Field():
    f = itsdb.Field('x', ':y', True, False, 'a comment')
    assert f.name == 'x'
    assert f.datatype == ':y'
    assert f.key is True
    assert f.partial == False
    assert f.comment == 'a comment'
    f = itsdb.Field('x', ':integer', False, False, '')
    assert f.default_value() == -1
    f = itsdb.Field('i-wf', ':integer', False, False, '')
    assert f.default_value() == 1


def test_Relations():
    f = itsdb.Field
    r = itsdb.Relations([
        ('item', [f('i-id', ':integer', True, False, ''),
                  f('i-input', ':string', False, False, '')]),
        ('parse', [f('parse-id', ':integer', True, False, 'unique parse identifier'),
                   f('i-id', ':integer', True, False, 'item parsed')])
    ])
    assert len(r) == 2
    assert 'item' in r
    assert 'parse' in r
    assert len(r['item']) == 2
    assert len(r['parse']) == 2
    assert r['item'][0].name == 'i-id'
    assert str(r) == (
        'item:\n'
        '  i-id :integer :key\n'
        '  i-input :string\n'
        '\n'
        'parse:\n'
        '  parse-id :integer :key                # unique parse identifier\n'
        '  i-id :integer :key                    # item parsed'
    )


def test_Relations_find():
    r = itsdb.Relations.from_string(_simple_relations)
    assert r.find('i-id') == ['item', 'parse']
    assert r.find('mrs') == ['result']
    with pytest.raises(KeyError):
        r.find('foo')


def test_Relations_path():
    r = itsdb.Relations.from_string(_simple_relations)
    assert r.path('item', 'result') == [('parse', 'i-id'), ('result', 'parse-id')]
    assert r.path('parse', 'item') == [('item', 'i-id')]
    assert r.path('item+parse', 'result') == [('result', 'parse-id')]
    assert r.path('item', 'parse+result') == [('parse', 'i-id')]
    assert r.path('parse', 'parse') == []
    assert r.path('item+parse', 'parse+result') == [('result', 'parse-id')]
    with pytest.raises(KeyError):
        r.path('foo', 'result')
    with pytest.raises(KeyError):
        r.path('item', 'bar')
    with pytest.raises(itsdb.ITSDBError):
        r.path('item', 'fold')


def test_Record():
    rels = itsdb.Relations.from_string(_simple_relations)
    r = itsdb.Record(rels['item'], [0, 'sentence'])
    assert r.fields == rels['item']
    assert len(r) == 2
    assert r['i-id'] == r[0] == 0
    assert r.get('i-id', cast=False) == '0'
    assert r['i-input'] == r[1] == 'sentence'
    assert r.get('i-input') == 'sentence'
    assert r.get('unknown') is None
    assert str(r) == '0@sentence'
    assert r == itsdb.Record(rels['item'], [0, 'sentence'])
    assert r != itsdb.Record(rels['item'], [1, 'sentence'])
    assert r != itsdb.Record(rels['item'], [0, 'string'])
    # incorrect number of fields
    with pytest.raises(itsdb.ITSDBError):
        itsdb.Record(rels['item'], [0])
    # None values get set to default, and
    # non-string values are left as-is
    r = itsdb.Record(rels['item'], [0, None])
    assert r['i-id'] == 0
    assert r['i-input'] == ''
    # mapped fields
    r = itsdb.Record.from_dict(rels['item'], {'i-id': 0, 'i-input': 'sentence'})
    assert len(r) == 2
    assert r['i-id'] == r[0] == 0
    assert r['i-input'] == r[1] == 'sentence'
    # missing values are ok
    r = itsdb.Record.from_dict(rels['item'], {'i-id': 0})
    assert len(r) == 2
    assert r['i-id'] == r[0] == 0
    assert r['i-input'] == r[1] == ''
    # missing keys are not ok
    with pytest.raises(itsdb.ITSDBError):
        r = itsdb.Record.from_dict(rels['item'], {'i-input': 'sentence'})
    # invalid fields are not ok
    with pytest.raises(itsdb.ITSDBError):
        r = itsdb.Record.from_dict(rels['item'], {'i-id': 0, 'surface': 'sentence'})


class TestTable(object):
    def test_init(self):
        fields = itsdb.Relations.from_string(_simple_relations)['item']
        with pytest.raises(TypeError):
            itsdb.Table()  # no relations
        # empty table
        table = itsdb.Table(fields=fields)
        assert len(table) == 0
        assert table.name == 'item'
        assert table.fields == fields
        assert table.path is None
        assert table.encoding is None
        # table with a record
        table = itsdb.Table(fields=fields, records=[(10, 'Birds chirp.')])
        assert len(table) == 1
        assert table[0]['i-id'] == 10
        assert table[0]['i-input'] == 'Birds chirp.'

    def test_from_file(self, empty_profile, single_item_skeleton,
                       gzipped_single_item_skeleton):
        # I'm not sure this should be an error if 'item' is defined
        # in the relations file
        with pytest.raises(itsdb.ITSDBError):
            itsdb.Table.from_file(os.path.join(empty_profile, 'item'))
        # table attached to a file
        table = itsdb.Table.from_file(os.path.join(single_item_skeleton, 'item'))
        assert len(table) == 1
        assert str(table.path) == os.path.join(single_item_skeleton, 'item')
        assert table.name == 'item'
        assert table.encoding == 'utf-8'
        # table attached to gzipped file given normalized filename
        table = itsdb.Table.from_file(os.path.join(gzipped_single_item_skeleton, 'item'))
        assert len(table) == 1
        assert str(table.path) == os.path.join(gzipped_single_item_skeleton, 'item.gz')
        assert table.name == 'item'

    def test_write(self, tmpdir):
        fields = itsdb.Relations.from_string(_simple_relations)['item']
        table = itsdb.Table(fields, records=[(10, 'Birds chirp.')])
        path = tmpdir.join('item')
        with pytest.raises(itsdb.ITSDBError):
            table.write()  # cannot write to detached table without *path*
        table.write(path=str(path))  # can write with *path*
        assert path.check()
        assert open(str(path)).read() == '10@Birds chirp.\n'
        # writing a new record to the path overwrites
        table.write(records=[(20, 'Cats meow.')], path=str(path))
        assert open(str(path)).read() == '20@Cats meow.\n'
        # unless append=True
        table.write(records=[(30, 'Cows moo.')], path=str(path), append=True)
        assert open(str(path)).read() == '20@Cats meow.\n30@Cows moo.\n'
        # gzip compresses and deletes any uncompressed version
        table.write(path=str(path), gzip=True)
        assert not path.check()
        assert tmpdir.join('item.gz').check()
        # attached tables may be written without *path*
        table = itsdb.Table.from_file(str(path), fields=fields)
        table.write(records=[(10, 'Birds chirp.')], gzip=False)
        assert path.check()
        assert not tmpdir.join('item.gz').check()
        assert str(table.path) == str(path)
        assert open(str(path)).read() == '10@Birds chirp.\n'
        # ensure path is updated when gzip option is used
        table.write(gzip=True)
        assert str(table.path) == str(path) + '.gz'
        table.write(gzip=False)
        assert str(table.path) == str(path)

    def test_attach(self, empty_profile):
        fields = itsdb.Relations.from_string(_simple_relations)['item']
        item_fn = os.path.join(empty_profile, 'item')
        # attach empty table to empty file
        table = itsdb.Table(fields)
        assert not os.path.exists(item_fn)
        table.attach(item_fn)
        assert os.path.exists(item_fn)  # attaching creates the file
        table.write()
        assert open(item_fn).read() == ''
        # attach already attached table
        with pytest.raises(itsdb.ITSDBError):
            table.attach(item_fn)
        os.unlink(item_fn)
        # attach non-empty table to empty file
        table = itsdb.Table(fields, records=[(10, 'Birds chirp.')])
        table.attach(item_fn)
        assert open(item_fn).read() == ''  # nothing written yet
        table.write()
        assert open(item_fn).read() == '10@Birds chirp.\n'
        # attach empty table to non-empty file
        table = itsdb.Table(fields)
        assert len(table) == 0
        table.attach(item_fn)
        assert len(table) == 1
        # attaching with .gz filename
        table2 = itsdb.Table(fields)
        table2.attach(item_fn + '.gz')
        assert len(table2) == 1
        assert str(table2.path) == item_fn
        # attaching to gzipped tables
        table.write(gzip=True)
        table2 = itsdb.Table(fields)
        table2.attach(table.path)
        assert len(table2) == 1
        assert str(table2.path) == item_fn + '.gz'
        table.write(gzip=False)  # just reset for the next test
        # attach non-empty table to non-empty file
        table = itsdb.Table(fields, records=[(20, 'Wolves howl.')])
        with pytest.raises(itsdb.ITSDBError):
            table.attach(item_fn)
        assert open(item_fn).read() == '10@Birds chirp.\n'

    def test_detach(self, tmpdir, single_item_skeleton):
        fields = itsdb.Relations.from_string(_simple_relations)['item']
        empty_fn = tmpdir.mkdir('tmp').join('item')
        item_fn = os.path.join(single_item_skeleton, 'item')
        # detach unchanged table from empty file
        table = itsdb.Table(fields)
        table.attach(str(empty_fn))
        assert len(table) == 0
        table.write()
        assert open(str(empty_fn)).read() == ''
        table.detach()
        assert len(table) == 0
        # detach changed table from empty file
        table = itsdb.Table(fields)
        table.attach(str(empty_fn))
        assert len(table) == 0
        table.append((10, 'Birds chirp.'))
        assert len(table) == 1
        assert open(str(empty_fn)).read() == ''
        table.detach()
        assert len(table) == 1
        assert open(str(empty_fn)).read() == ''
        # detach unchanged table from non-empty file
        table = itsdb.Table(fields)
        table.attach(item_fn)
        assert len(table) == 1
        table.detach()
        assert len(table) == 1
        # detach changed table from non-empty file
        table = itsdb.Table(fields)
        table.attach(item_fn)
        assert len(table) == 1
        assert table[0]['i-input'] == 'The dog barks.'
        table[0]['i-input'] = 'The bird chirps.'
        table.append((20, 'Cats meow.'))
        table.detach()
        assert len(table) == 2
        assert table[0]['i-input'] == 'The bird chirps.'
        assert open(item_fn).read() == '0@The dog barks.'

    def test_is_attached(self, single_item_skeleton, gzipped_single_item_skeleton):
        fields = itsdb.Relations.from_string(_simple_relations)['item']
        table = itsdb.Table(fields)
        assert not table.is_attached()
        # explicit attachment
        table.attach(os.path.join(single_item_skeleton, 'item'))
        assert table.is_attached()
        # explicit detachment
        table.detach()
        assert not table.is_attached()
        # from_file attachment
        table = itsdb.Table.from_file(os.path.join(single_item_skeleton, 'item'))
        assert table.is_attached()
        # from_file attachment with gzipped file
        table = itsdb.Table.from_file(os.path.join(gzipped_single_item_skeleton, 'item'))
        assert table.is_attached()
        # writing does not attach
        table = itsdb.Table(fields, [(10, 'Birds chirp.')])
        table.write(path=os.path.join(single_item_skeleton, 'item'))
        assert not table.is_attached()

    def test_list_changes(self, empty_profile, single_item_skeleton):
        fields = itsdb.Relations.from_string(_simple_relations)['item']
        table = itsdb.Table(fields)
        # detached tables do not track changes
        with pytest.raises(itsdb.ITSDBError):
            table.list_changes()
        table.append((10, 'Dogs bark.'))
        with pytest.raises(itsdb.ITSDBError):
            table.list_changes()
        # attching to a new file makes uncommitted records into changes
        table.attach(os.path.join(empty_profile, 'item'))
        assert len(table.list_changes()) == 1
        # writing an attached table clears changes
        table.write()
        assert table.list_changes() == []
        # attaching newly to a testsuite has no changes
        table = itsdb.Table.from_file(os.path.join(single_item_skeleton, 'item'))
        assert table.list_changes() == []
        # appending introduces a change
        table.append((10, 'Dogs bark.'))
        assert table.list_changes() == [(1, table[1])]
        # modifying a record introduces a change
        table[0]['i-input'] = 'The dog had barked.'
        assert table.list_changes() == [(0, table[0]), (1, table[1])]
        # detaching makes changes untrackable again
        table.detach()
        with pytest.raises(itsdb.ITSDBError):
            table.list_changes()

    def test_append(self, single_item_skeleton):
        fields = itsdb.Relations.from_string(_simple_relations)['item']
        # on bare table
        table = itsdb.Table(fields)
        assert len(table) == 0
        table.append((10, 'The dog barks.'))
        assert len(table) == 1
        assert table[-1]['i-input'] == 'The dog barks.'
        table.append((20, 'The cat meows.'))
        assert len(table) == 2
        assert table[-1]['i-input'] == 'The cat meows.'
        # on attached table
        table = itsdb.Table.from_file(os.path.join(single_item_skeleton, 'item'))
        assert len(table) == 1
        table.append((20, 'The bird chirps.'))
        assert len(table) == 2
        assert table[-1]['i-input'] == 'The bird chirps.'

    def test_extend(self, single_item_skeleton):
        fields = itsdb.Relations.from_string(_simple_relations)['item']
        # on bare table
        table = itsdb.Table(fields)
        assert len(table) == 0
        table.extend([(10, 'The dog barks.')])
        assert len(table) == 1
        assert table[-1]['i-input'] == 'The dog barks.'
        def record_generator():
            yield (20, 'The cat meows.')
            yield (20, 'The horse whinnies.')
            yield (20, 'The elephant trumpets.')
        table.extend(record_generator())
        assert len(table) == 4
        assert table[-1]['i-input'] == 'The elephant trumpets.'
        # on attached table
        table = itsdb.Table.from_file(os.path.join(single_item_skeleton, 'item'))
        assert len(table) == 1
        table.extend(record_generator())
        assert len(table) == 4
        assert table[-1]['i-input'] == 'The elephant trumpets.'

    def test_select(self, single_item_skeleton):
        fields = itsdb.Relations.from_string(_simple_relations)['item']
        # empty table
        table = itsdb.Table(fields)
        assert list(table.select('item:i-id')) == []
        # detached
        table.append((10, 'The bird chirps.'))
        assert list(table.select('item:i-id')) == [[10]]
        # attached and synced
        table = itsdb.Table.from_file(os.path.join(single_item_skeleton, 'item'))
        assert list(table.select('item:i-id')) == [[0]]
        # attached with unsynced records
        table.append((1, 'The bear growls.'))
        assert list(table.select('item:i-id')) == [[0], [1]]

    def test_getitem(self, empty_profile, single_item_skeleton):
        fields = itsdb.Relations.from_string(_simple_relations)['item']
        # empty table
        table = itsdb.Table(fields)
        with pytest.raises(IndexError):
            table[0]
        # detached
        table.append((10, 'The bird chirps.'))
        assert table[0] == (10, 'The bird chirps.')
        assert table[-1] == (10, 'The bird chirps.')
        # attached and synced
        table = itsdb.Table.from_file(os.path.join(single_item_skeleton, 'item'))
        assert table[0] == (0, 'The dog barks.')
        # attached with unsynced records
        table.append((1, 'The bear growls.'))
        assert table[-1] == (1, 'The bear growls.')
        # slice
        assert table[:] == [(0, 'The dog barks.'), (1, 'The bear growls.')]
        assert table[0:1] == [(0, 'The dog barks.')]
        assert table[::2] == [(0, 'The dog barks.')]
        assert table[::-1] == [(1, 'The bear growls.'), (0, 'The dog barks.')]

    def test_setitem(self, empty_profile, single_item_skeleton):
        fields = itsdb.Relations.from_string(_simple_relations)['item']
        # empty table
        table = itsdb.Table(fields)
        with pytest.raises(IndexError):
            table[0] = (10, 'The bird chirps.')
        # detached
        table.append((10, 'The bird chirps.'))
        table[0] = (10, 'The bird chirped.')
        assert len(table) == 1
        assert table[0] == (10, 'The bird chirped.')
        # attached
        table = itsdb.Table.from_file(os.path.join(single_item_skeleton, 'item'))
        assert table[0] == (0, 'The dog barks.')
        table[0] = (0, 'The dog barked.')
        assert table[0] == (0, 'The dog barked.')
        # slice
        table = itsdb.Table(fields)
        table[:] = [(0, 'The whale sings.')]
        assert len(table) == 1
        assert table[0] == (0, 'The whale sings.')
        table[0:5] = [(0, 'The whale sang.'), (1, 'The bear growls.')]
        assert len(table) == 2
        assert table[-1] == (1, 'The bear growls.')
        table[-1:] = []
        assert len(table) == 1
        assert table[-1] == (0, 'The whale sang.')


class TestSuite(object):
    def test_init(self, single_item_profile):
        rels = itsdb.Relations.from_string(_simple_relations)
        t = itsdb.TestSuite(relations=rels)
        assert len(t['item']) == 0
        assert len(t['parse']) == 0
        assert len(t['result']) == 0

        t = itsdb.TestSuite(single_item_profile)
        assert len(t['item']) == 1
        assert len(t['parse']) == 1
        assert len(t['result']) == 1

    def test_reload(self, single_item_profile):
        t = itsdb.TestSuite(single_item_profile)
        assert t['item'][0]['i-input'] == 'The dog barks.'
        t['item'][0]['i-input'] = 'The dog sleeps.'
        assert t['item'][0]['i-input'] == 'The dog sleeps.'
        t.reload()
        assert t['item'][0]['i-input'] == 'The dog barks.'

    def test_write(self, single_item_profile, tmpdir):
        t = itsdb.TestSuite(single_item_profile)
        assert t['item'][0]['i-input'] == 'The dog barks.'
        t['item'][0]['i-input'] = 'The dog sleeps.'
        assert t['item'][0]['i-input'] == 'The dog sleeps.'
        t.write()
        t.reload()
        assert t['item'][0]['i-input'] == 'The dog sleeps.'
        t['item'][0]['i-input'] = 'The cat sleeps.'
        t.write('parse')
        t.reload()
        assert t['item'][0]['i-input'] == 'The dog sleeps.'
        t['item'][0]['i-input'] = 'The cat sleeps.'
        t.write(['item', 'parse'])
        assert t['item'][0]['i-input'] == 'The cat sleeps.'
        record = itsdb.Record.from_dict(
            t.relations['item'], {'i-id': 0, 'i-input': 'The cat meows.'}
        )
        t.write({'item': [record]})
        t.reload()
        assert t['item'][0]['i-input'] == 'The cat meows.'
        d = tmpdir.mkdir('alt')
        altrels = itsdb.Relations.from_string(_alt_relations)
        t.write(path=str(d), relations=altrels)
        assert d.join('relations').read_text('utf-8') == _alt_relations
        assert sorted(x.basename for x in d.listdir()) == [
            'item', 'parse', 'relations', 'result']
        ts = itsdb.TestSuite(str(d))
        assert 'i-date' in ts['item'].fields

    def test_process(self, parser_cpu, single_item_skeleton):
        ts = itsdb.TestSuite(single_item_skeleton)
        assert len(ts['parse']) == 0
        assert len(ts['result']) == 0
        ts.process(parser_cpu)
        assert len(ts['parse']) == 1
        assert len(ts['result']) == 2
        assert ts['parse'][0]['parse-id'] == 0
        assert ts['parse'][0]['run-id'] == 0
        assert ts['result'][0]['parse-id'] == 0
        assert ts['result'][0]['result-id'] == 0
        assert ts['result'][1]['parse-id'] == 0
        assert ts['result'][1]['result-id'] == 1


def test_get_data_specifier():
    dataspec = itsdb.get_data_specifier
    assert dataspec('item') == ('item', None)
    assert dataspec('item:i-input') == ('item', ['i-input'])
    assert dataspec('item:i-id@i-input') == ('item', ['i-id', 'i-input'])
    assert dataspec(':i-id') == (None, ['i-id'])
    # for joined tables
    assert dataspec('tmp:item:i-id@output:o-surface') == ('tmp', ['item:i-id', 'output:o-surface'])
    assert dataspec(':item:i-id@output:o-surface') == (None, ['item:i-id', 'output:o-surface'])
    # unicode (see #164)
    assert dataspec(u'item:i-id') == ('item', ['i-id'])


def test_escape():
    assert itsdb.escape('') == ''
    assert itsdb.escape('abc') == 'abc'
    assert itsdb.escape('a@bc') == 'a\\sbc'
    assert itsdb.escape('a\nb') == 'a\\nb'
    assert itsdb.escape('a\\b') == 'a\\\\b'
    assert itsdb.escape(' a b ') == ' a b '


def test_unescape():
    assert itsdb.unescape('') == ''
    assert itsdb.unescape('abc') == 'abc'
    assert itsdb.unescape('a\\sbc') == 'a@bc'
    assert itsdb.unescape('a\\nb') == 'a\nb'
    assert itsdb.unescape('a\\\\b') == 'a\\b'
    assert itsdb.unescape(' a b ') == ' a b '


def test_decode_row():
    assert itsdb.decode_row('') == ['']
    assert itsdb.decode_row('one') == ['one']
    assert itsdb.decode_row(u'あ') == [u'あ']
    assert itsdb.decode_row('one@two') == ['one', 'two']
    assert itsdb.decode_row('one@@three') == ['one', '', 'three']
    assert itsdb.decode_row('one\\s@\\\\two\\nabc\\x') == ['one@', '\\two\nabc\\x']
    rels = itsdb.Relations.from_string(_simple_relations)
    assert itsdb.decode_row('10@one', fields=rels['item']) == [10, 'one']


def test_encode_row():
    assert itsdb.encode_row(['']) == ''
    assert itsdb.encode_row(['one']) == 'one'
    assert itsdb.encode_row([u'あ']) == u'あ'
    assert itsdb.encode_row(['one', 'two']) == 'one@two'
    assert itsdb.encode_row(['one', '', 'three']) == 'one@@three'
    assert itsdb.encode_row(['one@', '\\two\nabc']) == 'one\\s@\\\\two\\nabc'


def test_make_row(empty_profile):
    r = itsdb.Relations.from_file(os.path.join(empty_profile, 'relations'))
    assert itsdb.make_row({'i-input': 'one', 'i-id': 100}, r['item']) == '100@one'
    assert itsdb.make_row({'i-id': 100, 'mrs': '[RELS: < > HCONS: < >]'}, r['item']) == '100@'


def test_select_rows(single_item_profile):
    p = itsdb.TestSuite(single_item_profile)
    assert list(itsdb.select_rows(['i-id', 'i-input'], p['item'])) == [[0, 'The dog barks.']]
    assert list(itsdb.select_rows(['item:i-id', 'parse:parse-id'], itsdb.join(p['item'], p['parse']))) == [[0, 0]]


def test_match_rows():
    assert list(itsdb.match_rows(
        [{'i-id': '10', 'i-input': 'a'}, {'i-id': '20', 'i-input': 'b'}],
        [{'i-id': '20', 'i-input': 'c'}, {'i-id': '30', 'i-input': 'd'}],
        'i-id')) == [
            ('10', [{'i-id': '10', 'i-input': 'a'}], []),
            ('20', [{'i-id': '20', 'i-input': 'b'}], [{'i-id': '20', 'i-input': 'c'}]),
            ('30', [], [{'i-id': '30', 'i-input': 'd'}])
        ]


def test_join(single_item_profile):
    p = itsdb.TestSuite(single_item_profile)

    j = itsdb.join(p['parse'], p['result'])
    assert j.name == 'parse+result'
    assert len(j) == 1
    assert len(j.fields) == len(p['parse'].fields) + len(p['result'].fields) - 1
    r = j[0]
    assert r['parse:run-id'] == r['run-id']
    assert r['result:mrs'] == r['mrs']
    assert r['parse:parse-id'] == r['result:parse-id'] == r['parse-id']

    j2 = itsdb.join(p['item'], j)
    assert j2.name == 'item+parse+result'
    assert len(j2) == 1
    assert len(j2.fields) == len(j.fields) + len(p['item'].fields) - 1
    r = j2[0]
    assert r['item:i-input'] == r['i-input']
    assert r['item:i-id'] == r['parse:i-id']

    j3 = itsdb.join(j, p['item'])
    assert j3.name == 'parse+result+item'
