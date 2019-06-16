# -*- coding: utf-8 -*-

import pytest

from delphin import tsdb
from delphin import itsdb


class TestTestSuite(object):
    def test_init(self, single_item_profile):
        with pytest.raises(itsdb.ITSDBError):
            itsdb.TestSuite()

        t = itsdb.TestSuite(schema=single_item_profile.joinpath('relations'))
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


def test_Record(empty_testsuite):
    ts = itsdb.TestSuite(str(empty_testsuite))
    item = ts['item']
    r = itsdb.Record(item.fields, [0, 'sentence'])
    assert r.fields == item.fields
    assert r.keys() == ['i-id', 'i-input']
    assert len(r) == 2
    assert r['i-id'] == r[0] == 0
    assert r['i-input'] == r[1] == 'sentence'
    assert str(r) == '0@sentence'
    assert r == itsdb.Record(item.fields, [0, 'sentence'])
    assert r != itsdb.Record(item.fields, [1, 'sentence'])
    assert r != itsdb.Record(item.fields, [0, 'string'])
    # incorrect number of fields
    with pytest.raises(itsdb.ITSDBError):
        itsdb.Record(item.fields, [0])
    # None values get set to default, and
    # non-string values are left as-is
    r = itsdb.Record(item.fields, [0, None])
    assert r['i-id'] == 0
    assert r['i-input'] is None


class TestTable(object):
    def test_init(self, empty_testsuite):
        fields = tsdb.read_schema(empty_testsuite)['item']
        with pytest.raises(TypeError):
            itsdb.Table()
        with pytest.raises(TypeError):
            itsdb.Table(empty_testsuite)
        with pytest.raises(TypeError):
            itsdb.Table(empty_testsuite, 'item')
        # empty table
        table = itsdb.Table(empty_testsuite, 'item', fields)
        assert len(table) == 0
        assert table.name == 'item'
        assert table.fields == fields
        assert table.dir == empty_testsuite
        assert table.encoding == 'utf-8'

    def test_clear(self, single_item_skeleton):
        fields = tsdb.read_schema(single_item_skeleton)['item']
        table = itsdb.Table(single_item_skeleton, 'item', fields)
        assert len(table) == 1
        table.clear()
        assert len(table) == 0

    def test_append(self, empty_testsuite):
        fields = tsdb.read_schema(empty_testsuite)['item']
        table = itsdb.Table(empty_testsuite, 'item', fields)
        assert len(table) == 0
        table.append((10, 'The dog barks.'))
        assert len(table) == 1
        assert table[-1]['i-input'] == 'The dog barks.'
        table.append((20, 'The cat meows.'))
        assert len(table) == 2
        assert table[-1]['i-input'] == 'The cat meows.'

    def test_extend(self, empty_testsuite):
        fields = tsdb.read_schema(empty_testsuite)['item']
        # on bare table
        table = itsdb.Table(empty_testsuite, 'item', fields)
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

    def test_update(self, single_item_skeleton):
        pass

    def test_select(self, single_item_skeleton):
        fields = tsdb.read_schema(single_item_skeleton)['item']
        table = itsdb.Table(single_item_skeleton, 'item', fields)
        assert list(table.select('i-id')) == [[0]]
        table.append((1, 'The bear growls.'))
        assert list(table.select('i-id')) == [[0], [1]]
        # respect order
        assert list(table.select('i-input', 'i-id')) == [
            ['The dog barks.', 0],
            ['The bear growls.', 1]]

    def test_getitem(self, empty_testsuite, single_item_skeleton):
        fields = tsdb.read_schema(empty_testsuite)['item']
        # empty table
        table = itsdb.Table(empty_testsuite, 'item', fields)
        with pytest.raises(IndexError):
            table[0]
        table.append((10, 'The bird chirps.'))
        assert table[0] == (10, 'The bird chirps.')
        assert table[-1] == (10, 'The bird chirps.')
        # existing records
        table = itsdb.Table(single_item_skeleton, 'item', fields)
        assert table[0] == (0, 'The dog barks.')
        table.append((1, 'The bear growls.'))
        assert table[-1] == (1, 'The bear growls.')
        # slice
        assert table[:] == [(0, 'The dog barks.'), (1, 'The bear growls.')]
        assert table[0:1] == [(0, 'The dog barks.')]
        assert table[::2] == [(0, 'The dog barks.')]
        assert table[::-1] == [(1, 'The bear growls.'), (0, 'The dog barks.')]

    def test_setitem(self, empty_testsuite, single_item_skeleton):
        fields = tsdb.read_schema(empty_testsuite)['item']
        # empty table
        table = itsdb.Table(empty_testsuite, 'item', fields)
        with pytest.raises(IndexError):
            table[0] = (10, 'The bird chirps.')
        table.append((10, 'The bird chirps.'))
        table[0] = (10, 'The bird chirped.')
        assert len(table) == 1
        assert table[0] == (10, 'The bird chirped.')
        # existing records
        table = itsdb.Table(single_item_skeleton, 'item', fields)
        assert table[0] == (0, 'The dog barks.')
        table[0] = (0, 'The dog barked.')
        assert table[0] == (0, 'The dog barked.')
        # slice
        table = itsdb.Table(empty_testsuite, 'item', fields)
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

# def test_get_data_specifier():
#     dataspec = itsdb.get_data_specifier
#     assert dataspec('item') == ('item', None)
#     assert dataspec('item:i-input') == ('item', ['i-input'])
#     assert dataspec('item:i-id@i-input') == ('item', ['i-id', 'i-input'])
#     assert dataspec(':i-id') == (None, ['i-id'])
#     # for joined tables
#     assert dataspec('tmp:item:i-id@output:o-surface') == ('tmp', ['item:i-id', 'output:o-surface'])
#     assert dataspec(':item:i-id@output:o-surface') == (None, ['item:i-id', 'output:o-surface'])
#     # unicode (see #164)
#     assert dataspec(u'item:i-id') == ('item', ['i-id'])

# def test_select_rows(single_item_profile):
#     p = itsdb.TestSuite(single_item_profile)
#     assert list(itsdb.select_rows(['i-id', 'i-input'], p['item'])) == [[0, 'The dog barks.']]
#     assert list(itsdb.select_rows(['item:i-id', 'parse:parse-id'], itsdb.join(p['item'], p['parse']))) == [[0, 0]]

# def test_join(single_item_profile):
#     p = itsdb.TestSuite(single_item_profile)

#     j = itsdb.join(p['parse'], p['result'])
#     assert j.name == 'parse+result'
#     assert len(j) == 1
#     assert len(j.fields) == len(p['parse'].fields) + len(p['result'].fields) - 1
#     r = j[0]
#     assert r['parse:run-id'] == r['run-id']
#     assert r['result:mrs'] == r['mrs']
#     assert r['parse:parse-id'] == r['result:parse-id'] == r['parse-id']

#     j2 = itsdb.join(p['item'], j)
#     assert j2.name == 'item+parse+result'
#     assert len(j2) == 1
#     assert len(j2.fields) == len(j.fields) + len(p['item'].fields) - 1
#     r = j2[0]
#     assert r['item:i-input'] == r['i-input']
#     assert r['item:i-id'] == r['parse:i-id']

#     j3 = itsdb.join(j, p['item'])
#     assert j3.name == 'parse+result+item'
