# coding: utf-8

from delphin.util import safe_int, SExpr

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
