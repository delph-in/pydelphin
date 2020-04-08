# -*- coding: utf-8 -*-

import pathlib
from datetime import datetime

import pytest

from delphin import tsdb
from delphin import itsdb


@pytest.fixture
def single_item_table(single_item_skeleton):
    fields = tsdb.read_schema(single_item_skeleton)['item']
    table = itsdb.Table(single_item_skeleton, 'item', fields)
    return table


@pytest.fixture
def empty_item_table(empty_testsuite):
    fields = tsdb.read_schema(empty_testsuite)['item']
    table = itsdb.Table(empty_testsuite, 'item', fields)
    return table


class TestTestSuite(object):
    def test_init(self, single_item_profile):
        with pytest.raises(itsdb.ITSDBError):
            itsdb.TestSuite()

        rel = pathlib.Path(single_item_profile, 'relations')
        t = itsdb.TestSuite(schema=rel)
        assert len(t['item']) == 0
        assert len(t['parse']) == 0
        assert len(t['result']) == 0

        t = itsdb.TestSuite(single_item_profile)
        assert len(t['item']) == 1
        assert len(t['parse']) == 1
        assert len(t['result']) == 1

    def test_in_transaction(self, empty_testsuite):
        t = itsdb.TestSuite(empty_testsuite)
        item = t['item']
        assert not t.in_transaction
        item.append((10, 'Dogs bark.'))
        assert t.in_transaction
        t.commit()
        assert not t.in_transaction
        item.update(-1, {'i-input': 'Cats meow.'})
        assert t.in_transaction
        t.commit()
        assert not t.in_transaction
        item[-1:] = []
        assert t.in_transaction
        item.append((10, 'Dogs bark.'))
        t.commit()
        item.clear()
        assert t.in_transaction

    def test_reload(self, single_item_profile):
        t = itsdb.TestSuite(single_item_profile)
        assert t['item'][0]['i-input'] == 'The dog barks.'
        t['item'][0] = (0, 'The dog sleeps.')
        assert t['item'][0]['i-input'] == 'The dog sleeps.'
        t.reload()
        assert t['item'][0]['i-input'] == 'The dog barks.'

    def test_commit(self, single_item_profile, empty_alt_testsuite):
        t = itsdb.TestSuite(single_item_profile)
        item = t['item']
        # uncommitted changes do not persist
        assert item[0]['i-input'] == 'The dog barks.'
        item[0] = (0, 'The dog sleeps.')
        assert item[0]['i-input'] == 'The dog sleeps.'
        assert t.in_transaction
        t.reload()
        assert item[0]['i-input'] == 'The dog barks.'
        assert not t.in_transaction
        # committing them makes them persist
        item[0] = (0, 'The dog sleeps.')
        assert t.in_transaction
        t.commit()
        assert not t.in_transaction
        t.reload()
        assert item[0]['i-input'] == 'The dog sleeps.'

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

    def test_processed_items(self, mini_testsuite):
        ts = itsdb.TestSuite(mini_testsuite)
        responses = list(ts.processed_items())
        assert len(responses) == 3
        assert responses[0]['i-input'] == 'It rained.'
        assert len(responses[0].results()) == 1
        assert responses[0].result(0)['mrs'] == (
            '[ TOP: h0 INDEX: e2 [ e TENSE: past ]'
            '  RELS: < [ _rain_v_1<3:9> LBL: h1 ARG0: e2 ] >'
            '  HCONS: < h0 qeq h1 > ]')
        assert len(responses[1].results()) == 0
        assert len(responses[2].results()) == 1


def test_Row(empty_alt_testsuite):
    ts = itsdb.TestSuite(str(empty_alt_testsuite))
    item = ts['item']
    r = itsdb.Row(item.fields, [0, 'sentence', datetime(2009, 9, 7)])
    assert r.fields == item.fields
    assert r.keys() == ['i-id', 'i-input', 'i-date']
    assert len(r) == 3
    assert r['i-id'] == r[0] == 0
    assert r['i-input'] == r[1] == 'sentence'
    assert r['i-date'] == r[2] == datetime(2009, 9, 7)
    assert str(r) == '0@sentence@7-sep-2009'
    assert r == (0, 'sentence', datetime(2009, 9, 7))
    assert r.data == ('0', 'sentence', '7-sep-2009')
    assert r == itsdb.Row(item.fields, [0, 'sentence', datetime(2009, 9, 7)])
    assert r != itsdb.Row(item.fields, [1, 'sentence', datetime(2009, 9, 7)])
    assert r != itsdb.Row(item.fields, [0, 'string', datetime(2009, 9, 7)])
    assert r != itsdb.Row(item.fields, [0, 'sentence', datetime(2009, 7, 9)])
    # incorrect number of fields
    with pytest.raises(itsdb.ITSDBError):
        itsdb.Row(item.fields, [0])
    # None values get set to default, and
    # non-string values are left as-is
    r = itsdb.Row(item.fields, [0, None, None])
    assert r['i-id'] == 0
    assert r['i-input'] is None
    assert r['i-date'] is None


class TestTable(object):
    def test_init(self, empty_item_table):
        dir = empty_item_table.dir
        fields = empty_item_table.fields
        with pytest.raises(TypeError):
            itsdb.Table()
        with pytest.raises(TypeError):
            itsdb.Table(dir)
        with pytest.raises(TypeError):
            itsdb.Table(dir, 'item')
        # empty table
        table = itsdb.Table(dir, 'item', fields)
        assert len(table) == 0
        assert table.name == 'item'
        assert table.fields == fields
        assert table.dir == dir
        assert table.encoding == 'utf-8'

    def test_clear(self, single_item_table):
        assert len(single_item_table) == 1
        single_item_table.clear()
        assert len(single_item_table) == 0

    def test_append(self, empty_item_table):
        table = empty_item_table
        assert len(table) == 0
        table.append((10, 'The dog barks.'))
        assert len(table) == 1
        assert table[-1]['i-input'] == 'The dog barks.'
        table.append((20, 'The cat meows.'))
        assert len(table) == 2
        assert table[-1]['i-input'] == 'The cat meows.'

    def test_extend(self, empty_item_table):
        table = empty_item_table
        assert len(table) == 0
        table.extend([(10, 'The dog barks.')])
        assert len(table) == 1
        assert table[-1]['i-input'] == 'The dog barks.'

        def row_generator():
            yield (20, 'The cat meows.')
            yield (20, 'The horse whinnies.')
            yield (20, 'The elephant trumpets.')

        table.extend(row_generator())
        assert len(table) == 4
        assert table[-1]['i-input'] == 'The elephant trumpets.'

    def test_update(self, single_item_table):
        table = single_item_table
        assert table[0] == (0, 'The dog barks.')
        table.update(0, {'i-input': 'The dog sleeps.'})
        assert table[0] == (0, 'The dog sleeps.')

    def test_select(self, single_item_table):
        table = single_item_table
        assert list(table.select('i-id')) == [[0]]
        table.append((1, 'The bear growls.'))
        assert list(table.select('i-id')) == [[0], [1]]
        # respect order
        assert list(table.select('i-input', 'i-id')) == [
            ['The dog barks.', 0],
            ['The bear growls.', 1]]

    def test__iter__(self, single_item_table):
        table = single_item_table
        assert list(table) == [(0, 'The dog barks.')]
        table.append((10, 'The cat meows.'))
        assert list(table) == [(0, 'The dog barks.'), (10, 'The cat meows.')]
        table.clear()
        assert list(table) == []

    def test__getitem__(self, empty_item_table, single_item_table):
        table = empty_item_table
        with pytest.raises(IndexError):
            table[0]
        table.append((10, 'The bird chirps.'))
        assert table[0] == (10, 'The bird chirps.')
        assert table[-1] == (10, 'The bird chirps.')
        # existing rows
        table = single_item_table
        assert table[0] == (0, 'The dog barks.')
        table.append((1, 'The bear growls.'))
        assert table[-1] == (1, 'The bear growls.')
        # slice
        assert table[:] == [(0, 'The dog barks.'), (1, 'The bear growls.')]
        assert table[0:1] == [(0, 'The dog barks.')]
        assert table[::2] == [(0, 'The dog barks.')]
        assert table[::-1] == [(1, 'The bear growls.'), (0, 'The dog barks.')]

    def test__setitem__(self, empty_item_table, single_item_table):
        table = empty_item_table
        with pytest.raises(IndexError):
            table[0] = (10, 'The bird chirps.')
        table.append((10, 'The bird chirps.'))
        table[0] = (10, 'The bird chirped.')
        assert len(table) == 1
        assert table[0] == (10, 'The bird chirped.')
        # existing rows
        table = single_item_table
        assert table[0] == (0, 'The dog barks.')
        table[0] = (0, 'The dog barked.')
        assert table[0] == (0, 'The dog barked.')
        # slice
        table = empty_item_table
        table[:] = [(0, 'The whale sings.')]
        assert len(table) == 1
        assert table[0] == (0, 'The whale sings.')
        table[0:5] = [(0, 'The whale sang.'), (1, 'The bear growls.')]
        assert len(table) == 2
        assert table[-1] == (1, 'The bear growls.')
        table[-1:] = []
        assert len(table) == 1
        assert table[-1] == (0, 'The whale sang.')


def test_match_rows():
    rows1 = [{'i-id': '10', 'i-input': 'a'}, {'i-id': '20', 'i-input': 'b'}]
    rows2 = [{'i-id': '20', 'i-input': 'c'}, {'i-id': '30', 'i-input': 'd'}]
    assert list(itsdb.match_rows(rows1, rows2, 'i-id')) == [
        ('10',
         [{'i-id': '10', 'i-input': 'a'}],
         []),
        ('20',
         [{'i-id': '20', 'i-input': 'b'}],
         [{'i-id': '20', 'i-input': 'c'}]),
        ('30',
         [],
         [{'i-id': '30', 'i-input': 'd'}])
    ]


def test_bad_date_issue_279b(tmp_path, empty_alt_testsuite):
    tmp_ts = tmp_path.joinpath('test_bad_date_issue_279b')
    tmp_ts.mkdir()
    schema = tsdb.read_schema(empty_alt_testsuite)
    fields = schema['item']
    tsdb.write_schema(tmp_ts, schema)
    tsdb.write(
        tmp_ts, 'item', [(0, 'The cat meows.', 'September 8, 1999')], fields)
    ts = itsdb.TestSuite(tmp_ts)
    assert list(ts['item'].select('i-date', cast=False)) == [
        ('September 8, 1999',)
    ]
    with pytest.warns(tsdb.TSDBWarning):
        ts['item'][0]['i-date']

    # Ideally the following would not raise an assertion error, but
    # the invalid date gets stored as `None` in memory which then gets
    # written to disk. Unfortunately the fix is not obvious at this
    # time, so I'm going to sidestep the issue for now and just say
    # that PyDelphin will not write profiles with invalid values.
    #
    # tsdb.write_database(ts, tmp_ts)
    # ts.reload()
    # assert list(ts['item'].select('i-date', cast=False)) == [
    #     ('September 8, 1999',)
    # ]


