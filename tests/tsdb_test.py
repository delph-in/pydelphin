
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
    assert f.key
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


def test_decode_row(empty_testsuite):
    assert tsdb.decode_row('') == (None,)
    assert tsdb.decode_row('one') == ('one',)
    assert tsdb.decode_row(u'あ') == (u'あ',)
    assert tsdb.decode_row('one@two') == ('one', 'two')
    assert tsdb.decode_row('one@@three') == ('one', None, 'three')
    assert (tsdb.decode_row('one\\s@\\\\two\\nabc\\x')
            == ('one@', '\\two\nabc\\x'))
    rels = tsdb.read_schema(empty_testsuite)
    assert tsdb.decode_row('10@one', fields=rels['item']) == (10, 'one')


def test_encode_row():
    assert tsdb.encode_row([None]) == ''
    assert tsdb.encode_row(['one']) == 'one'
    assert tsdb.encode_row([u'あ']) == u'あ'
    assert tsdb.encode_row(['one', 'two']) == 'one@two'
    assert tsdb.encode_row(['one', None, 'three']) == 'one@@three'
    assert tsdb.encode_row(['one@', '\\two\nabc']) == 'one\\s@\\\\two\\nabc'


def test_make_row(empty_testsuite):
    r = tsdb.read_schema(empty_testsuite.joinpath('relations'))
    assert (tsdb.make_row({'i-input': 'one', 'i-id': 100}, r['item'])
            == (100, 'one'))
    assert tsdb.make_row({'i-id': 100}, r['item']) == (100, None)
    assert tsdb.make_row({'i-id': 100, 'mrs': '[RELS: < > HCONS: < >]'},
                         r['item']) == (100, None)


def test_cast():
    assert tsdb.cast(':integer', None) is None
    assert tsdb.cast(':float', None) is None
    assert tsdb.cast(':string', None) is None
    assert tsdb.cast(':date', None) is None
    assert tsdb.cast(':integer', '15') == 15
    assert tsdb.cast(':float', '2.05e-3') == 0.00205
    assert tsdb.cast(':string', 'Abrams slept.') == 'Abrams slept.'
    assert tsdb.cast(':date', '10-6-2002') == datetime(2002, 6, 10, 0, 0)
    assert tsdb.cast(':date', '8-sep-1999') == datetime(1999, 9, 8, 0, 0)
    assert tsdb.cast(':date', 'apr-95') == datetime(1995, 4, 1, 0, 0)
    assert (tsdb.cast(':date', '01-dec-02 (15:31:01)')
            == datetime(2002, 12, 1, 15, 31, 1))
    assert (tsdb.cast(':date', '2008-10-12 10:51')
            == datetime(2008, 10, 12, 10, 51))


def test_open_table(single_item_skeleton, gzipped_single_item_skeleton):
    with pytest.raises(tsdb.TSDBError):
        with tsdb.open_table(single_item_skeleton, 'non') as fh:
            pass
    with tsdb.open_table(single_item_skeleton, 'item') as fh:
        assert list(fh) == ['0@The dog barks.']
    with tsdb.open_table(gzipped_single_item_skeleton, 'item') as fh:
        assert list(fh) == ['0@The dog barks.']


def test_write_table(single_item_skeleton):
    dir = single_item_skeleton
    fields = tsdb.read_schema(dir)['item']
    path = dir.joinpath('item')
    tsdb.write_table(dir, 'item', [(0, 'The cat meows.')], fields)
    with tsdb.open_table(dir, 'item') as fh:
        assert list(fh) == ['0@The cat meows.']
    tsdb.write_table(dir, 'item', [(1, 'The wolf howls.')], fields,
                     append=True)
    with tsdb.open_table(dir, 'item') as fh:
        assert list(fh) == ['0@The cat meows.\n', '1@The wolf howls.']

    tsdb.write_table(dir, 'item', [(0, 'The cat meows.')], fields, gzip=True)
    assert not path.with_suffix('').exists()
    assert path.with_suffix('.gz').exists()
    tsdb.write_table(dir, 'item', [(0, 'The cat meows.')], fields)
    assert not path.with_suffix('').exists()
    assert path.with_suffix('.gz').exists()
    tsdb.write_table(dir, 'item', [(0, 'The cat meows.')], fields, gzip=False)
    assert not path.with_suffix('.gz').exists()
    assert path.with_suffix('').exists()


class TestTable():
    def test_init(self, mini_testsuite):
        schema = tsdb.read_schema(mini_testsuite)
        table = tsdb.Table(mini_testsuite, 'item', schema['item'])
        assert table.dir == mini_testsuite
        assert table.name == 'item'
        assert table.fields == schema['item']

    def test__iter__(self, mini_testsuite):
        schema = tsdb.read_schema(mini_testsuite)
        item = tsdb.Table(mini_testsuite, 'item', schema['item'])
        assert len(list(item)) == 3

    def test_select(self, mini_testsuite):
        schema = tsdb.read_schema(mini_testsuite)
        item = tsdb.Table(mini_testsuite, 'item', schema['item'])
        assert list(item.select('i-id')) == [('10',), ('20',), ('30',)]
        assert list(item.select('i-input', 'i-id')) == [
            ('It rained.', '10'),
            ('Rained.', '20'),
            ('It snowed.', '30')]


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

    def test__getitem__(self, mini_testsuite):
        db = tsdb.Database(mini_testsuite)
        item = db['item']
        assert item.name == 'item'
        with pytest.raises(tsdb.TSDBError):
            db['not_a_table']
