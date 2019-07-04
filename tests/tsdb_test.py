
import pytest

from datetime import datetime

from delphin import tsdb


def test_Field():
    with pytest.raises(TypeError):
        tsdb.Field()
    with pytest.raises(TypeError):
        tsdb.Field('x')
    f = tsdb.Field('x', ':y')
    f = tsdb.Field('x', ':y', (':key',), 'a comment')
    assert f.name == 'x'
    assert f.datatype == ':y'
    assert f.is_key
    assert f.flags == (':key',)
    assert f.comment == 'a comment'
    f = tsdb.Field('x', ':integer', (), '')
    assert f.default == '-1'
    f = tsdb.Field('i-wf', ':integer', (), '')
    assert f.default == '1'


def test_read_schema(empty_testsuite):
    r = tsdb.read_schema(empty_testsuite)
    f = tsdb.Field
    assert r == {
        'item': [f('i-id', ':integer', (':key',)),
                 f('i-input', ':string')],
        'fold': [f('fold-id', ':integer', (':key',))],
        'run': [f('run-id', ':integer', (':key',))],
        'parse': [f('parse-id', ':integer', (':key',)),
                  f('run-id', ':integer', (':key',)),
                  f('i-id', ':integer', (':key',))],
        'result': [f('parse-id', ':integer', (':key',)),
                   f('result-id', ':integer'),
                   f('mrs', ':string')]
    }


def test_write_schema(empty_testsuite, tmp_path):
    f = tsdb.Field
    r = {
        'item': [f('i-id', ':integer', (':key',)),
                 f('i-input', ':string')],
        'fold': [f('fold-id', ':integer', (':key',))],
        'run': [f('run-id', ':integer', (':key',),
                  'unique test run identifier')],
        'parse': [f('parse-id', ':integer', (':key',),
                    'unique parse identifier'),
                  f('run-id', ':integer', (':key',),
                    'test run for this parse'),
                  f('i-id', ':integer', (':key',),
                    'item parsed')],
        'result': [f('parse-id', ':integer', (':key',),
                     'parse for this result'),
                   f('result-id', ':integer', (),
                     'result identifier'),
                   f('mrs', ':string', (),
                     'MRS for this reading')]
    }
    tmp_dir = tmp_path.joinpath('test_write_schema')
    tmp_dir.mkdir()
    tsdb.write_schema(tmp_dir, r)
    orig = empty_testsuite.joinpath('relations')
    new = tmp_dir.joinpath('relations')
    assert orig.read_text() == new.read_text()


class TestDatabase():
    def test_init(self, tmp_path, mini_testsuite):
        with pytest.raises(TypeError):
            tsdb.Database()
        with pytest.raises(tsdb.TSDBError):
            dir = tmp_path.joinpath('not_a_testsuite')
            dir.mkdir()
            tsdb.Database(dir)
        tsdb.Database(mini_testsuite)

    def test_path(self, mini_testsuite):
        db = tsdb.Database(mini_testsuite)
        assert db.path == mini_testsuite

    def test__getitem__(self, mini_testsuite, empty_testsuite):
        db = tsdb.Database(mini_testsuite)
        items = db['item']
        assert len(list(items)) == 3
        # relation undefined
        with pytest.raises(tsdb.TSDBError):
            db['not_a_relation']
        # relation defined by file missing
        db = tsdb.Database(empty_testsuite)
        with pytest.raises(tsdb.TSDBError):
            db['item']


def test_escape():
    assert tsdb.escape('') == ''
    assert tsdb.escape('abc') == 'abc'
    assert tsdb.escape('a@bc') == 'a\\sbc'
    assert tsdb.escape('a\nb') == 'a\\nb'
    assert tsdb.escape('a\\b') == 'a\\\\b'
    assert tsdb.escape(' a b ') == ' a b '


def test_unescape():
    assert tsdb.unescape('') == ''
    assert tsdb.unescape('abc') == 'abc'
    assert tsdb.unescape('a\\sbc') == 'a@bc'
    assert tsdb.unescape('a\\nb') == 'a\nb'
    assert tsdb.unescape('a\\\\b') == 'a\\b'
    assert tsdb.unescape(' a b ') == ' a b '


def test_split(empty_testsuite):
    assert tsdb.split('') == (None,)
    assert tsdb.split('one') == ('one',)
    assert tsdb.split(u'あ') == (u'あ',)
    assert tsdb.split('one@two') == ('one', 'two')
    assert tsdb.split('one@@three') == ('one', None, 'three')
    assert (tsdb.split('one\\s@\\\\two\\nabc\\x')
            == ('one@', '\\two\nabc\\x'))
    rels = tsdb.read_schema(empty_testsuite)
    assert tsdb.split('10@one', fields=rels['item']) == (10, 'one')


def test_join():
    assert tsdb.join([None]) == ''
    assert tsdb.join(['one']) == 'one'
    assert tsdb.join([u'あ']) == u'あ'
    assert tsdb.join(['one', 'two']) == 'one@two'
    assert tsdb.join(['one', None, 'three']) == 'one@@three'
    assert tsdb.join(['one@', '\\two\nabc']) == 'one\\s@\\\\two\\nabc'


def test_make_record(empty_testsuite):
    r = tsdb.read_schema(empty_testsuite.joinpath('relations'))
    assert (tsdb.make_record({'i-input': 'one', 'i-id': 100}, r['item'])
            == (100, 'one'))
    assert tsdb.make_record({'i-id': 100}, r['item']) == (100, None)
    assert tsdb.make_record({'i-id': 100, 'mrs': '[RELS: < > HCONS: < >]'},
                            r['item']) == (100, None)


def test_cast():
    assert tsdb.cast(':integer', None) is None
    assert tsdb.cast(':float', None) is None
    assert tsdb.cast(':string', None) is None
    assert tsdb.cast(':date', None) is None
    assert tsdb.cast(':integer', '15') == 15
    assert tsdb.cast(':integer', '-1') == -1
    assert tsdb.cast(':integer', '') is None
    assert tsdb.cast(':float', '2.05e-3') == 0.00205
    assert tsdb.cast(':float', '') is None
    assert tsdb.cast(':string', 'Abrams slept.') == 'Abrams slept.'
    assert tsdb.cast(':string', '') is None
    assert tsdb.cast(':date', '10-6-2002') == datetime(2002, 6, 10, 0, 0)
    assert tsdb.cast(':date', '8-sep-1999') == datetime(1999, 9, 8, 0, 0)
    assert tsdb.cast(':date', 'apr-95') == datetime(1995, 4, 1, 0, 0)
    assert (tsdb.cast(':date', '01-dec-02 (15:31:01)')
            == datetime(2002, 12, 1, 15, 31, 1))
    assert (tsdb.cast(':date', '2008-10-12 10:51')
            == datetime(2008, 10, 12, 10, 51))
    assert tsdb.cast(':date', '') is None


def test_format():
    assert tsdb.format(':integer', 42) == '42'
    assert tsdb.format(':integer', 42, default='1') == '42'
    assert tsdb.format(':integer', None) == '-1'
    assert tsdb.format(':integer', None, default='1') == '1'
    assert tsdb.format(':date', datetime(1999, 9, 8)) == '8-sep-1999'


def test_open(single_item_skeleton, gzipped_single_item_skeleton):
    with pytest.raises(tsdb.TSDBError):
        tsdb.open(single_item_skeleton, 'non')

    fh = tsdb.open(single_item_skeleton, 'item')
    assert not fh.closed
    with fh:
        assert list(fh) == ['0@The dog barks.']
    assert fh.closed

    with tsdb.open(single_item_skeleton, 'item') as fh:
        assert list(fh) == ['0@The dog barks.']
    with tsdb.open(gzipped_single_item_skeleton, 'item') as fh:
        assert list(fh) == ['0@The dog barks.']


def test_write(single_item_skeleton):
    dir = single_item_skeleton
    fields = tsdb.read_schema(dir)['item']
    path = dir.joinpath('item')
    tsdb.write(dir, 'item', [(0, 'The cat meows.')], fields)
    with tsdb.open(dir, 'item') as fh:
        assert list(fh) == ['0@The cat meows.\n']
    tsdb.write(dir, 'item', [(1, 'The wolf howls.')], fields, append=True)
    with tsdb.open(dir, 'item') as fh:
        assert list(fh) == ['0@The cat meows.\n', '1@The wolf howls.\n']
    # cannot append and gzip at same time
    with pytest.raises(NotImplementedError):
        tsdb.write(dir, 'item', [], fields, gzip=True, append=True)
    tsdb.write(dir, 'item', [(0, 'The cat meows.')], fields, gzip=True)
    assert not path.with_suffix('').exists()
    assert path.with_suffix('.gz').exists()
    # cannot append to existing gzipped file
    with pytest.raises(NotImplementedError):
        tsdb.write(dir, 'item', [], fields, append=True)
    tsdb.write(dir, 'item', [(0, 'The cat meows.')], fields)
    assert path.with_suffix('').exists()
    assert not path.with_suffix('.gz').exists()
    tsdb.write(dir, 'item', [(0, 'The cat meows.')], fields, gzip=False)
    assert not path.with_suffix('.gz').exists()
    assert path.with_suffix('').exists()
    tsdb.write(dir, 'item', [], fields, gzip=True)
    assert not path.with_suffix('.gz').exists()
    assert path.with_suffix('').exists()


def test_write_database(tmp_path, mini_testsuite, empty_alt_testsuite):
    tmp_ts = tmp_path.joinpath('test_write_database')
    db = tsdb.Database(mini_testsuite)
    tsdb.write_database(db, tmp_ts)
    assert tmp_ts.is_dir()
    assert tmp_ts.joinpath('relations').is_file()
    assert tmp_ts.joinpath('item').is_file()
    assert tmp_ts.joinpath('parse').is_file()
    assert tmp_ts.joinpath('result').is_file()
    assert tmp_ts.joinpath('parse').read_text() == (
        '10@10@1\n'
        '20@20@0\n'
        '30@30@1\n')
    tsdb.write_database(db, tmp_ts, names=['item'])
    assert tmp_ts.joinpath('item').is_file()
    assert not tmp_ts.joinpath('parse').is_file()
    assert not tmp_ts.joinpath('result').is_file()
    # alt_schema drops i-wf field from mini_testsuite's schema
    alt_schema = tsdb.read_schema(empty_alt_testsuite)
    tsdb.write_database(db, tmp_ts, names=['item'], schema=alt_schema)
    alt_db = tsdb.Database(tmp_ts)
    assert len(db.schema['item']) == 4
    assert len(alt_db.schema['item']) == 3
    assert tmp_ts.joinpath('item').read_text() == (
        '10@It rained.@1-feb-2018 15:00\n'
        '20@Rained.@01-02-18 15:00:00\n'
        '30@It snowed.@2018-2-1 (15:00:00)\n')
