# coding: utf-8

from delphin.util import safe_int, SExpr, detect_encoding

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
    assert SExpr.format((1,2)) == '(1 . 2)'
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
def empty_file(tmpdir):
    f = tmpdir.join('empty.txt')
    return str(f)


@pytest.fixture
def nocomment_file(tmpdir):
    f = tmpdir.join('nocomment.txt')
    f.write('avm := *top*.')
    return str(f)


@pytest.fixture
def utf8_file(tmpdir):
    f = tmpdir.join('utf8.txt')
    f.write('; coding: utf-8\n'
            u'a := character & [ ORTH \"あ\" ].')
    return str(f)


@pytest.fixture
def utf8var1_file(tmpdir):
    f = tmpdir.join('utf8var1.txt')
    f.write('; -*- mode: tdl; encoding: UTF-8; foo: bar -*-\n'
            u'a := character & [ ORTH \"あ\" ].')
    return str(f)


@pytest.fixture
def utf8var2_file(tmpdir):
    f = tmpdir.join('utf8var2.txt')
    f.write('# coding: utf-8\n'
            u'a=\"あ\"')
    return str(f)


@pytest.fixture
def latin1_file(tmpdir):
    f = tmpdir.join('latin1.txt')
    f.write('; coding: iso-8859-1\n'
            u'a := character & [ ORTH \"á\" ].')
    return str(f)


@pytest.fixture
def shiftjis_file(tmpdir):
    f = tmpdir.join('shift_jis.txt')
    f.write('# coding: shift_jis\n'
            u'a=\"あ\"')
    return str(f)


@pytest.fixture
def eucjp_file(tmpdir):
    f = tmpdir.join('eucjp.txt')
    f.write('# coding: euc_jp\n'
            u'a=\"あ\"')
    return str(f)


@pytest.fixture
def invalid1_file(tmpdir):
    f = tmpdir.join('invalid1.txt')
    f.write('; encode: iso-8859-1\n'
            'á')
    return str(f)


@pytest.fixture
def invalid2_file(tmpdir):
    f = tmpdir.join('invalid2.txt')
    f.write('; coding: foo')
    return str(f)

import codecs
@pytest.fixture
def invalid3_file(tmpdir):
    f = tmpdir.join('invalid3.txt')
    f.write(codecs.BOM_UTF8 + '; coding: latin-1')
    return str(f)


def test_detect_encoding(empty_file, nocomment_file, utf8_file, utf8var1_file,
    utf8var2_file, shiftjis_file, eucjp_file, latin1_file, invalid1_file):
    assert detect_encoding(empty_file) == 'utf-8'
    assert detect_encoding(nocomment_file) == 'utf-8'
    assert detect_encoding(utf8_file) == 'utf-8'
    assert detect_encoding(utf8var1_file) == 'utf-8'
    assert detect_encoding(utf8var2_file) == 'utf-8'
    assert detect_encoding(shiftjis_file) == 'shift_jis'
    assert detect_encoding(eucjp_file) == 'euc_jp'
    assert detect_encoding(latin1_file) == 'iso-8859-1'
    with pytest.raises(ValueError):
        detect_encoding(invalid1_file)
    with pytest.raises(LookupError):
        detect_encoding(invalid2_file)
    with pytest.raises(ValueError):
        detect_encoding(invalid3_file)
