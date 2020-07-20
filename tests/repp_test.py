
import pytest
# The regex library should be used if available; if not, tests may
# need to be skipped.
try:
    import regex
except ImportError:
    regex = None

from delphin import repp
from delphin.lnk import Lnk

r = repp.REPP


def test_no_rules():
    x = r().apply('abc')
    assert x.string == 'abc'
    assert x.startmap.tolist() == [1, 0, 0, 0, 0]
    assert x.endmap.tolist() == [0, 0, 0, 0, -1]

    x = r.from_string('').apply('abc')
    assert x.string == 'abc'
    assert x.startmap.tolist() == [1, 0, 0, 0, 0]
    assert x.endmap.tolist() == [0, 0, 0, 0, -1]


def test_no_match():
    x = r.from_string(r'!a	b').apply('ccc')  # no match
    assert x.string == 'ccc'
    assert x.startmap.tolist() == [1, 0, 0, 0, 0]
    assert x.endmap.tolist() == [0, 0, 0, 0, -1]


def test_basic_same_len():
    x = r.from_string(r'!a	b').apply('baba')
    assert x.string == 'bbbb'
    assert x.startmap.tolist() == [1, 0, 0, 0, 0, 0]
    assert x.endmap.tolist() == [0, 0, 0, 0, 0, -1]


def test_basic_len_change():
    x = r.from_string(r'!a	aa').apply('baba')
    assert x.string == 'baabaa'
    assert x.startmap.tolist() == [1, 0, 0, -1, -1, -1, -2, -2]
    assert x.endmap.tolist() == [0, 0, 0, -1, -1, -1, -2, -3]


def test_empty_replacement_issue_252():
    # https://github.com/delph-in/pydelphin/issues/252
    x = r.from_string(r'!a	').apply('ab')
    assert x.string == 'b'
    assert x.startmap.tolist() == [1, 1, 1]
    assert x.endmap.tolist() == [0, 1, 0]


def test_single_capturing_group():
    x = r.from_string(r'!(\w+)	[\1]').apply('abc def')
    assert x.string == '[abc] [def]'
    assert x.startmap.tolist() == [
        1,  0, -1, -1, -1, -1, -2, -2, -3, -3, -3, -3, -4
    ]
    assert x.endmap.tolist() == [
        0, -1, -1, -1, -1, -2, -2, -3, -3, -3, -3, -4, -5
    ]


def test_skipped_capturing_group_issue_250():
    # https://github.com/delph-in/pydelphin/issues/250
    x = r.from_string(r'!(b)(a)	B\2r').apply('baba')
    assert x.string == 'BarBar'
    assert x.startmap.tolist() == [
        1,  0, -1, -2, -1, -2, -3, -2
    ]
    assert x.endmap.tolist() == [
        0,  1,  0, -1,  0, -1, -2, -3
    ]


def test_len_change_with_capturing_group():
    x = r.from_string(r"!wo(n't)	will \1").apply("I won't go")
    assert x.string == "I will n't go"
    assert x.startmap.tolist() == [
        1, 0, 0, 0, -1, -2, -3, -4, -3, -3, -3, -3, -3, -3, -3
    ]
    assert x.endmap.tolist() == [
        0, 0, 0, 1,  0, -1, -2, -3, -3, -3, -3, -3, -3, -3, -4
    ]

    x = r.from_string(r"!wo(n't)	will \1").tokenize("I won't go")
    assert len(x.tokens) == 4
    assert x.tokens[0].form == 'I'
    assert x.tokens[0].lnk == Lnk.charspan(0, 1)
    assert x.tokens[1].form == 'will'
    assert x.tokens[1].lnk == Lnk.charspan(2, 4)
    assert x.tokens[2].form == "n't"
    assert x.tokens[2].lnk == Lnk.charspan(4, 7)
    assert x.tokens[3].form == 'go'
    assert x.tokens[3].lnk == Lnk.charspan(8, 10)


@pytest.mark.skipif(regex is None, reason='regex library is not available')
def test_local_inline_flags():
    rpp = r.from_string(r'!a((?i)b)a	c')
    assert rpp.apply('aba').string == 'c'
    assert rpp.apply('aBa').string == 'c'
    assert rpp.apply('AbA').string == 'AbA'


def test_basic_external_group_active():
    x = r.from_string(
        '>a',
        modules={'a': r.from_string(r'!a	b')},
        active=['a']
    ).apply('baba')
    assert x.string == 'bbbb'
    assert x.startmap.tolist() == [1, 0, 0, 0, 0, 0]
    assert x.endmap.tolist() == [0, 0, 0, 0, 0, -1]

    x = r.from_string(
        '>a',
        modules={'a': r.from_string(r'!a	b')}
    ).apply('baba', active=['a'])
    assert x.string == 'bbbb'
    assert x.startmap.tolist() == [1, 0, 0, 0, 0, 0]
    assert x.endmap.tolist() == [0, 0, 0, 0, 0, -1]


def test_basic_external_group_inactive():
    x = r.from_string(
        '>a',
        modules={'a': r.from_string(r'!a	b')}
    ).apply('baba')
    assert x.string == 'baba'
    assert x.startmap.tolist() == [1, 0, 0, 0, 0, 0]
    assert x.endmap.tolist() == [0, 0, 0, 0, 0, -1]


def test_multiple_external_groups():
    x = r.from_string(
        '>a\n>b\n>c',
        modules={'a': r.from_string('!a	b'),
                 'b': r.from_string('!b	c'),
                 'c': r.from_string('!c	d')},
        active=['a', 'b', 'c']
    ).apply('baba')
    assert x.string == 'dddd'
    assert x.startmap.tolist() == [1, 0, 0, 0, 0, 0]
    assert x.endmap.tolist() == [0, 0, 0, 0, 0, -1]

    x = r.from_string(
        '>a\n>b\n>c',
        modules={'a': r.from_string('!a	b'),
                 'b': r.from_string('!b	c'),
                 'c': r.from_string('!c	d')},
        active=['a']
    ).apply('baba')
    assert x.string == 'bbbb'
    assert x.startmap.tolist() == [1, 0, 0, 0, 0, 0]
    assert x.endmap.tolist() == [0, 0, 0, 0, 0, -1]


def test_without_iterative_groups():
    x = r.from_string(
        r'!(^| )([()%,])([^ ])	\1\2 \3' '\n'
        r'!([^ ])([()%,])( |$)	\1 \2\3'
    ).apply('(42%),')
    assert x.string == '( 42%) ,'
    assert x.startmap.tolist() == [
        1, 0,  0, -1, -1, -1, -1, -1, -2, -2
    ]
    assert x.endmap.tolist() == [
        0, 0, -1, -1, -1, -1, -1, -2, -2, -3
    ]


def test_with_iterative_groups():
    x = r.from_string(
        '#1\n'
        r'!(^| )([()%,])([^ ])	\1\2 \3' '\n'
        r'!([^ ])([()%,])( |$)	\1 \2\3' '\n'
        '#\n'
        '>1'
    ).apply('(42%),')
    assert x.string == '( 42 % ) ,'
    assert x.startmap.tolist() == [
        1, 0,  0, -1, -1, -1, -2, -2, -3, -3, -4, -4
    ]
    assert x.endmap.tolist() == [
        0, 0, -1, -1, -1, -2, -2, -3, -3, -4, -4, -5
    ]

    x = r.from_string(
        '#1\n'
        r'!(^| )([()%,])([^ ])	\1\2 \3' '\n'
        r'!([^ ])([()%,])( |$)	\1 \2\3' '\n'
        '#\n'
        '>1'
    ).tokenize('(42%),')
    assert len(x.tokens) == 5
    assert x.tokens[0].form == '('
    assert x.tokens[0].lnk == Lnk.charspan(0, 1)
    assert x.tokens[1].form == '42'
    assert x.tokens[1].lnk == Lnk.charspan(1, 3)
    assert x.tokens[2].form == '%'
    assert x.tokens[2].lnk == Lnk.charspan(3, 4)
    assert x.tokens[3].form == ')'
    assert x.tokens[3].lnk == Lnk.charspan(4, 5)
    assert x.tokens[4].form == ','
    assert x.tokens[4].lnk == Lnk.charspan(5, 6)


def test_trace():
    x = r.from_string(r'''
!(\w+)	[\1]
!\[([^\]]+)\]	*\1*
''')
    steps = list(x.trace('abc def'))
    assert len(steps) == 4
    # first rule of module
    assert isinstance(steps[0], repp.REPPStep)
    assert steps[0].input == 'abc def'
    assert steps[0].output == '[abc] [def]'
    # second rule of module
    assert isinstance(steps[1], repp.REPPStep)
    assert steps[1].input == '[abc] [def]'
    assert steps[1].output == '*abc* *def*'
    # module group
    assert isinstance(steps[2], repp.REPPStep)
    assert steps[2].input == 'abc def'
    assert steps[2].output == '*abc* *def*'
    # final result
    assert isinstance(steps[3], repp.REPPResult)
    assert steps[3].string == '*abc* *def*'


def test_unmatched_group_issue_301():
    # https://github.com/delph-in/pydelphin/issues/301
    x = r.from_string(r'!(a)(b)*	\1 \2')
    assert x.apply('ab').string == 'a b'
    assert x.apply('a').string == 'a '
