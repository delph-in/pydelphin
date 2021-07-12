# coding: utf-8

import codecs

from delphin.util import safe_int, SExpr, detect_encoding, LookaheadIterator

import pytest


def test_safe_int():
    assert safe_int('1') == 1
    assert safe_int('1.0') == '1.0'
    assert safe_int('-12345') == -12345
    assert safe_int('1a') == '1a'


def test_SExpr():
    # atoms outside of parens
    # assert SExpr.parse('a').data == 'a'
    # assert SExpr.parse('1').data == 1
    # assert SExpr.parse('1.0').data == 1.0
    # assert SExpr.parse('"a"').data == 'a'  # same as symbol?
    assert SExpr.parse('()').data == []
    assert SExpr.parse('(a)').data == ['a']
    assert SExpr.parse('(1)').data == [1]
    assert SExpr.parse('(1.0)').data == [1.0]
    assert SExpr.parse('(1e2)').data == [100]
    assert SExpr.parse('(1.2e2)').data == [120]
    assert SExpr.parse('(1.2e-2)').data == [0.012]
    assert SExpr.parse('("a")').data == ['a']  # same as symbol?
    assert SExpr.parse('( a . b )').data == ('a', 'b')
    assert SExpr.parse('( :a (b) )').data == [':a', ['b']]
    assert SExpr.parse('(a-a (b 1 2))').data == ['a-a', ['b', 1, 2]]
    assert SExpr.parse('("(a b)")').data == ['(a b)']

    assert SExpr.parse('(a\\ b c)').data == ['a b', 'c']
    assert SExpr.parse('(\\(a\\) \\[a\\] \\{a\\} \\; \\\\)').data == [
        '(a)', '[a]', '{a}', ';', '\\'
    ]
    assert SExpr.parse('(:key . "\\"\\\\\\"a\\\\\\"\\"")').data == (
        ":key", '"\\"a\\""'
    )
    assert SExpr.parse('("\\"a\\"" \\" "\\(\\)\\;\\[\\]")').data == [
        '"a"', '"', '\\(\\)\\;\\[\\]'
    ]
    # other kinds of whitespace
    assert SExpr.parse('(\ta\n.\n\n  b)').data == ('a', 'b')


def test_SExpr_format():
    assert SExpr.format([]) == '()'
    assert SExpr.format([1]) == '(1)'
    assert SExpr.format([1.0]) == '(1.0)'
    assert SExpr.format((1, 2)) == '(1 . 2)'
    assert SExpr.format(['a-a', ('b', 'c')]) == '(a-a (b . c))'

# unescape_string is disabled in delphin.util
# def test_unescape_string():
#     assert unescape_string('') == ''
#     assert unescape_string('a') == 'a'
#     assert unescape_string('"') == '"'
#     assert unescape_string('\\"') == '"'
#     assert unescape_string('\\\\') == '\\'
#     assert unescape_string('\\U00003042') == 'あ'
#     assert unescape_string('\\u3042') == 'あ'
#     assert unescape_string('\\xe3\\x81\\x82') == 'あ'
#     assert unescape_string('\\N{HIRAGANA LETTER A}') == 'あ'


@pytest.fixture
def empty_file(tmp_path):
    f = tmp_path / 'empty.txt'
    f.write_text(u'', encoding='utf-8')
    return str(f)


@pytest.fixture
def nocomment_file(tmp_path):
    f = tmp_path / 'nocomment.txt'
    f.write_text(u'avm := *top*.', encoding='utf-8')
    return str(f)


@pytest.fixture
def utf8_file(tmp_path):
    f = tmp_path / 'utf8.txt'
    f.write_text(u'; coding: utf-8\n'
                 u'a := character & [ ORTH \"あ\" ].', encoding='utf-8')
    return str(f)


@pytest.fixture
def utf8var1_file(tmp_path):
    f = tmp_path / 'utf8var1.txt'
    f.write_text(u'; -*- mode: tdl; encoding: UTF-8; foo: bar -*-\n'
                 u'a := character & [ ORTH \"あ\" ].', encoding='utf-8')
    return str(f)


@pytest.fixture
def utf8var2_file(tmp_path):
    f = tmp_path / 'utf8var2.txt'
    f.write_text(u'# coding: utf-8\n'
                 u'a=\"あ\"', encoding='utf-8')
    return str(f)


@pytest.fixture
def latin1_file(tmp_path):
    f = tmp_path / 'latin1.txt'
    f.write_text(u'; coding: iso-8859-1\n'
                 u'a := character & [ ORTH \"á\" ].', encoding='iso-8859-1')
    return str(f)


@pytest.fixture
def shiftjis_file(tmp_path):
    f = tmp_path / 'shift_jis.txt'
    f.write_text(u'; coding: shift_jis\n'
                 u'a=\"あ\"', encoding='shift_jis')
    return str(f)


@pytest.fixture
def eucjp_file(tmp_path):
    f = tmp_path / 'eucjp.txt'
    f.write_text(u'; coding: euc_jp\n'
                 u'a=\"あ\"', encoding='euc_jp')
    return str(f)


@pytest.fixture
def invalid1_file(tmp_path):
    f = tmp_path / 'invalid1.txt'
    f.write_text(u'; encode: iso-8859-1\n'
                 u'á', encoding='iso-8859-1')
    return str(f)


@pytest.fixture
def invalid2_file(tmp_path):
    f = tmp_path / 'invalid2.txt'
    f.write_text(u'; coding: foo', encoding='utf-8')
    return str(f)


@pytest.fixture
def invalid3_file(tmp_path):
    f = tmp_path / 'invalid3.txt'
    f.write_bytes(codecs.BOM_UTF8 + b'; coding: latin-1')
    return str(f)


def test_detect_encoding(
    empty_file, nocomment_file, utf8_file, utf8var1_file,
    utf8var2_file, shiftjis_file, eucjp_file, latin1_file, invalid1_file,
    invalid2_file, invalid3_file
):
    assert detect_encoding(empty_file) == 'utf-8'
    assert detect_encoding(nocomment_file) == 'utf-8'
    assert detect_encoding(utf8_file) == 'utf-8'
    assert detect_encoding(utf8var1_file) == 'utf-8'
    assert detect_encoding(utf8var2_file) == 'utf-8'
    assert detect_encoding(shiftjis_file) == 'shift_jis'
    assert detect_encoding(eucjp_file) == 'euc_jp'
    assert detect_encoding(latin1_file) == 'iso-8859-1'
    assert detect_encoding(invalid1_file) == 'utf-8'
    with pytest.raises(LookupError):
        detect_encoding(invalid2_file)
    with pytest.raises(ValueError):
        detect_encoding(invalid3_file)


class TestLookaheadIterator:
    def test_empty(self):
        # https://github.com/delph-in/pydelphin/issues/275
        li = LookaheadIterator(iter([]))
        with pytest.raises(StopIteration):
            li.peek()
        with pytest.raises(StopIteration):
            li.next()

    def test_single_item(self):
        li = LookaheadIterator(iter([1]))
        assert li.peek() == 1
        assert li.next() == 1
        with pytest.raises(StopIteration):
            li.peek()
        with pytest.raises(StopIteration):
            li.next()
