
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
    assert itsdb.get_data_specifier('item') == ('item', None)
    assert itsdb.get_data_specifier('item:i-input') == ('item', ['i-input'])
    assert itsdb.get_data_specifier('item:i-id@i-input') == ('item', ['i-id', 'i-input'])
    assert itsdb.get_data_specifier(':i-id') == (None, ['i-id'])

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

def test_make_row():
    pass

def test_default_value():
    pass

def test_filter_rows():
    pass

def test_apply_rows():
    pass

def test_select_rows():
    pass

def test_match_rows():
    pass

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
