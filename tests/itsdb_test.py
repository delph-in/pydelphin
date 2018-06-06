
from __future__ import print_function

import os
import tempfile

import pytest

from delphin import itsdb

_simple_relations = '''
item:
  i-id :integer :key
  i-input :string

parse:
  parse-id :integer :key  # unique parse identifier
  i-id :integer :key      # item parsed

result:
  parse-id :integer :key  # parse for this result
  result-id :integer      # result identifier
  mrs :string             # MRS for this reading
'''


@pytest.fixture
def empty_profile():
    d = tempfile.mkdtemp()
    print(_simple_relations, file=open(os.path.join(d, 'relations'), 'w'))
    return d

@pytest.fixture
def single_item_skeleton():
    d = tempfile.mkdtemp()
    print(_simple_relations, file=open(os.path.join(d, 'relations'), 'w'))
    print('0@The dog barks.', file=open(os.path.join(d, 'item'), 'w'))
    return d

@pytest.fixture
def single_item_profile():
    d = tempfile.mkdtemp()
    print(_simple_relations, file=open(os.path.join(d, 'relations'), 'w'))
    print('0@The dog barks.', file=open(os.path.join(d, 'item'), 'w'))
    print('0@0', file=open(os.path.join(d, 'parse'), 'w'))
    print(
        '0@0@[ LTOP: h0 INDEX: e2 RELS: < '
        '[ _the_q<0:3> LBL: h4 ARG0: x3 RSTR: h5 BODY: h6 ] '
        '[ _dog_n_1<4:7> LBL: h7 ARG0: x3 ] '
        '[ _bark_v_1<8:14> LBL: h1 ARG0: e2 ARG1: x3 ] > '
        'HCONS: < h0 qeq h1 h5 qeq h7 > ]',
        file=open(os.path.join(d, 'result'), 'w')
    )
    return d

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

def test_Record():
    rels = itsdb.Relations.from_string(_simple_relations)
    r = itsdb.Record(rels['item'], [0, 'sentence'])
    assert r.fields == rels['item']
    assert len(r) == 2
    assert r['i-id'] == r[0] == 0
    assert r['i-input'] == r[1] == 'sentence'
    assert r.get('i-input') == 'sentence'
    assert r.get('unknown') == None
    assert str(r) == '0@sentence'
    # incorrect number of fields
    with pytest.raises(itsdb.ItsdbError):
        itsdb.Record(rels['item'], [0])
    # None values get set to default
    r = itsdb.Record(rels['item'], [0, None])
    assert r['i-input'] == ''
    # mapped fields
    r = itsdb.Record(rels['item'], {'i-id': 0, 'i-input': 'sentence'})
    assert len(r) == 2
    assert r['i-id'] == r[0] == 0
    assert r['i-input'] == r[1] == 'sentence'
    # missing values are ok
    r = itsdb.Record(rels['item'], {'i-id': 0})
    assert len(r) == 2
    assert r['i-id'] == r[0] == 0
    assert r['i-input'] == r[1] == ''
    # missing keys are not ok
    with pytest.raises(itsdb.ItsdbError):
        r = itsdb.Record(rels['item'], {'i-input': 'sentence'})
    # invalid fields are not ok
    with pytest.raises(itsdb.ItsdbError):
        r = itsdb.Record(rels['item'], {'i-id': 0, 'surface': 'sentence'})


def test_Table(single_item_skeleton):
    rels = itsdb.Relations.from_string(_simple_relations)
    t = itsdb.Table(
        'item',
        rels['item'],
    )
    assert t.fields == rels['item']
    assert t.name == 'item'
    assert len(t) == 0

    t = itsdb.Table(
        'item',
        rels['item'],
        [(0, 'sentence')]
    )
    assert t.fields == rels['item']
    assert t.name == 'item'
    assert len(t) == 1
    assert isinstance(t[0], itsdb.Record)
    assert t[0].fields == t.fields

    itemfile = os.path.join(single_item_skeleton, 'item')
    t = itsdb.Table.from_file(itemfile, 'item', rels['item'])
    assert t.fields == rels['item']
    assert t.name == 'item'
    assert len(t) == 1
    assert isinstance(t[0], itsdb.Record)
    assert t[0]['i-input'] == 'The dog barks.'
    assert list(t.select('i-input')) == [['The dog barks.']]

    # infer name and relations if not given
    t = itsdb.Table.from_file(itemfile)
    assert t.fields == rels['item']
    assert t.name == 'item'
    assert len(t) == 1

def test_TestSuite(single_item_profile):
    rels = itsdb.Relations.from_string(_simple_relations)
    t = itsdb.TestSuite(relations=rels)
    assert len(t['item']) == 0
    assert len(t['parse']) == 0
    assert len(t['result']) == 0
    assert list(t.select('item:i-input')) == []

    t = itsdb.TestSuite(single_item_profile)
    assert len(t['item']) == 1
    assert len(t['parse']) == 1
    assert len(t['result']) == 1
    assert list(t.select('item:i-input')) == [['The dog barks.']]

def test_get_data_specifier():
    dataspec = itsdb.get_data_specifier
    assert dataspec('item') == ('item', None)
    assert dataspec('item:i-input') == ('item', ['i-input'])
    assert dataspec('item:i-id@i-input') == ('item', ['i-id', 'i-input'])
    assert dataspec(':i-id') == (None, ['i-id'])
    # for joined tables
    assert dataspec('tmp:item:i-id@output:o-surface') == ('tmp', ['item:i-id', 'output:o-surface'])
    assert dataspec(':item:i-id@output:o-surface') == (None, ['item:i-id', 'output:o-surface'])

def test_escape():
    assert itsdb.escape('') == ''
    assert itsdb.escape('abc') == 'abc'
    assert itsdb.escape('a@bc') == 'a\sbc'
    assert itsdb.escape('a\nb') == 'a\\nb'
    assert itsdb.escape('a\\b') == 'a\\\\b'
    assert itsdb.escape(' a b ') == ' a b '

def test_unescape():
    assert itsdb.unescape('') == ''
    assert itsdb.unescape('abc') == 'abc'
    assert itsdb.unescape('a\sbc') == 'a@bc'
    assert itsdb.unescape('a\\nb') == 'a\nb'
    assert itsdb.unescape('a\\\\b') == 'a\\b'
    assert itsdb.unescape(' a b ') == ' a b '

def test_decode_row():
    assert itsdb.decode_row('') == ['']
    assert itsdb.decode_row('one') == ['one']
    assert itsdb.decode_row('one@two') == ['one', 'two']
    assert itsdb.decode_row('one@@three') == ['one', '', 'three']
    assert itsdb.decode_row('one\\s@\\\\two\\nabc\\x') == ['one@', '\\two\nabc\\x']
    rels = itsdb.Relations.from_string(_simple_relations)
    assert itsdb.decode_row('10@one', fields=rels['item']) == [10, 'one']

def test_encode_row():
    assert itsdb.encode_row(['']) == ''
    assert itsdb.encode_row(['one']) == 'one'
    assert itsdb.encode_row(['one', 'two']) == 'one@two'
    assert itsdb.encode_row(['one', '', 'three']) == 'one@@three'
    assert itsdb.encode_row(['one@', '\\two\nabc']) == 'one\\s@\\\\two\\nabc'

def test_make_row(empty_profile):
    r = itsdb.get_relations(os.path.join(empty_profile, 'relations'))
    assert itsdb.make_row({'i-input': 'one', 'i-id': 100}, r['item']) == '100@one'
    assert itsdb.make_row({'i-id': 100, 'mrs': '[RELS: < > HCONS: < >]'}, r['item']) == '100@'

def test_select_rows(single_item_profile):
    p = itsdb.ItsdbProfile(single_item_profile)
    # assert list(itsdb.select_rows(None, p.read_table('item'))) == [['0', 'The dog barks.']]
    assert list(itsdb.select_rows(['i-id', 'i-input'], p.read_table('item'))) == [['0', 'The dog barks.']]
    assert list(itsdb.select_rows(['item:i-id', 'parse:parse-id'], p.join('item', 'parse'))) == [['0', '0']]

def test_match_rows():
    assert list(itsdb.match_rows(
        [{'i-id': '10', 'i-input': 'a'}, {'i-id': '20', 'i-input': 'b'}],
        [{'i-id': '20', 'i-input': 'c'}, {'i-id': '30', 'i-input': 'd'}],
        'i-id')) == [
            ('10', [{'i-id': '10', 'i-input': 'a'}], []),
            ('20', [{'i-id': '20', 'i-input': 'b'}], [{'i-id': '20', 'i-input': 'c'}]),
            ('30', [], [{'i-id': '30', 'i-input': 'd'}])
        ]

## Deprecated

def test_get_relations(empty_profile):
    r = itsdb.get_relations(os.path.join(empty_profile, 'relations'))
    assert r['item'] == (
        itsdb.Field('i-id', ':integer', True, False, None),
        itsdb.Field('i-input', ':string', False, False, None)
    )
    assert r['parse'] == (
        itsdb.Field('parse-id', ':integer', True, False, 'unique parse identifier'),
        itsdb.Field('i-id', ':integer', True, False, 'item parsed')
    )
    assert r['result'] == (
        itsdb.Field('parse-id', ':integer', True, False, 'parse for this result'),
        itsdb.Field('result-id', ':integer', False, False, 'result identifier'),
        itsdb.Field('mrs', ':string', False, False, 'MRS for this reading')
    )

def test_default_value():
    assert itsdb.default_value('foo', ':string') == ''
    assert itsdb.default_value('foo', '') == ''
    assert itsdb.default_value('foo', ':integer') == '-1'
    assert itsdb.default_value('i-wf', ':integer') == '1'

def test_filter_rows():
    assert list(itsdb.filter_rows([(['i-id'], lambda row, x: x=='10')], [{'i-id': '10'}, {'i-id': '20'}])) == [{'i-id': '10'}]
    assert list(itsdb.filter_rows([(['i-input'], lambda row, x: len(x) > 2)], [{'i-id': '10'}, {'i-id': '20'}])) == [{'i-id': '10'}, {'i-id': '20'}]
    assert list(itsdb.filter_rows([(['i-input'], lambda row, x: len(x) > 2)], [{'i-id': '10', 'i-input': 'a'}, {'i-id': '20', 'i-input': 'abc'}])) == [{'i-id': '20', 'i-input': 'abc'}]

def test_apply_rows():
    assert list(itsdb.apply_rows([(['i-id'], lambda row, x: str(int(x)+10))], [{'i-id': '10'}, {'i-id': '20'}])) == [{'i-id': '20'}, {'i-id': '30'}]
    # the following inserts any col that didn't already exist. Is this desired?
    # assert list(itsdb.apply_rows([(['i-input'], lambda row, x: x.replace(' ', ''))], [{'i-id': '10'}, {'i-id': '20'}])) == [{'i-id': '10'}, {'i-id': '20'}]
    assert list(itsdb.apply_rows([(['i-input'], lambda row, x: x.replace(' ', ''))], [{'i-id': '10', 'i-input': 'a'}, {'i-id': '20', 'i-input': 'a b  c'}])) == [{'i-id': '10', 'i-input': 'a'}, {'i-id': '20', 'i-input': 'abc'}]

def test_make_skeleton():
    pass

def test_ItsdbProfile(empty_profile, single_item_skeleton, single_item_profile):
    p = itsdb.ItsdbProfile(empty_profile)
    # tests
    p = itsdb.ItsdbProfile(single_item_skeleton)
    # tests
    p = itsdb.ItsdbProfile(single_item_profile)
    # tests

def test_ItsdbSkeleton():
    pass
