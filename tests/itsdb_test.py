
from __future__ import print_function

import pytest
import os
import tempfile
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
    f = itsdb.Field('x', ':y', True, [':other'], 'a comment')
    assert f.name == 'x'
    assert f.datatype == ':y'
    assert f.key is True
    assert f.other == [':other']
    assert f.comment == 'a comment'

def test_get_relations(empty_profile):
    r = itsdb.get_relations(os.path.join(empty_profile, 'relations'))
    assert r['item'] == [
        itsdb.Field('i-id', ':integer', True, [], None),
        itsdb.Field('i-input', ':string', False, [], None)
    ]
    assert r['parse'] == [
        itsdb.Field('parse-id', ':integer', True, [], 'unique parse identifier'),
        itsdb.Field('i-id', ':integer', True, [], 'item parsed')
    ]
    assert r['result'] == [
        itsdb.Field('parse-id', ':integer', True, [], 'parse for this result'),
        itsdb.Field('result-id', ':integer', False, [], 'result identifier'),
        itsdb.Field('mrs', ':string', False, [], 'MRS for this reading')
    ]

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
