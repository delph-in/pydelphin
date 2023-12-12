
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
    _r = r.from_string(
        '>a',
        modules={'a': r.from_string(r'!a	b'),
                 'b': r.from_string(r'!b	c')},
        active=['a']
    )
    x = _r.apply('baba')
    assert x.string == 'bbbb'
    assert x.startmap.tolist() == [1, 0, 0, 0, 0, 0]
    assert x.endmap.tolist() == [0, 0, 0, 0, 0, -1]

    x = r.from_string(
        '>a',
        modules={'a': r.from_string(r'!a	b'),
                 'b': r.from_string(r'!b	c')},
    ).apply('baba', active=['a'])
    assert x.string == 'bbbb'
    assert x.startmap.tolist() == [1, 0, 0, 0, 0, 0]
    assert x.endmap.tolist() == [0, 0, 0, 0, 0, -1]


def test_indirect_external_group_active():
    a = r.from_string('>b', modules={'b': r.from_string(r'!a	b')})
    assert a.apply('baba').string == 'baba'
    assert r.from_string(
        '>a',
        modules={'a': a},
        active=('a', 'b')
    ).apply('baba').string == 'bbbb'


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


def test_basic_internal_groups():
    rpp = r.from_string(
        '#1\n'
        '!a	b\n'
        '#\n'
        '>1\n'
    )
    assert rpp.apply('aaa').string == 'bbb'
    assert rpp.apply('ccc').string == 'ccc'


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


def test_mask_values():
    rpp = r.from_string('=ab*\n'
                        '!_	--\n'
                        '!--	\n')
    assert next(rpp.trace('b')).mask.tolist() == [0, 0, 0]
    assert next(rpp.trace('a')).mask.tolist() == [0, 1, 0]
    assert next(rpp.trace('ab')).mask.tolist() == [0, 1, 2, 0]
    assert next(rpp.trace('aa')).mask.tolist() == [0, 1, 1, 0]
    assert next(rpp.trace('aba')).mask.tolist() == [0, 1, 2, 1, 0]

    steps = rpp.trace('_ab')
    assert next(steps).mask.tolist() == [0, 0, 1, 2, 0]     # mask op
    assert next(steps).mask.tolist() == [0, 0, 0, 1, 2, 0]  # rewrite 1
    assert next(steps).mask.tolist() == [0, 1, 2, 0]        # rewrite 2

    steps = rpp.trace('ab_')
    assert next(steps).mask.tolist() == [0, 1, 2, 0, 0]     # mask op
    assert next(steps).mask.tolist() == [0, 1, 2, 0, 0, 0]  # rewrite 1
    assert next(steps).mask.tolist() == [0, 1, 2, 0]        # rewrite 2


def test_mask_basic():
    rpp = r.from_string('!_	-\n'
                        '=[0-9]-[0-9]\n'
                        '!~	    \n'
                        '!-	 \n'
                        '!(?<=[0-9])~*(?=[0-9])	=\n'
                        '!8[-+]9	\n')
    assert rpp.apply('0-a').string == '0 a'  # mask doesn't match
    assert rpp.apply('0_a').string == '0 a'  # mask doesn't match
    assert rpp.apply('0-2').string == '0-2'  # mask matches
    assert rpp.apply('0_2').string == '0-2'  # mask matches after rewrite
    assert rpp.apply('0-2-3').string == '0-2 3'  # mask matches once
    assert rpp.apply('0-2-3-4').string == '0-2 3-4'  # mask matches twice
    # between-mask insertion (without capturing)
    assert rpp.apply('0-23-4').string == '0-2=3-4'
    # mask is intact after shifting
    assert rpp.apply('~0-1').string == '    0-1'
    # mask may not be deleted
    assert rpp.apply('8-9 8+9').string == '8-9 '


def test_mask_captures():
    rpp = r.from_string('=[0-9]-[0-9]\n'
                        '!([0-9])([0-9])	\\1 \\2\n'
                        r'!([^=]+)=(.*)$	\2=\1')
    assert rpp.apply('123-4').string == '1 23-4'  # mask not captured
    assert rpp.apply('12-3').string == '1 2-3'  # mask partially captured
    assert rpp.apply('01-23-45').string == '0 1-2 3-4 5'  # adjacent masks
    assert rpp.apply('1-2=3-4').string == '1-2=3-4'  # no swapping

    rpp = r.from_string('=[0-9]\n'
                        '!([0-9A-Fa-f])	\\1\\1\n')
    assert rpp.apply('1a').string == '1aa'  # no duplication of masks


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


def test_iterative_group_use_before_define_issue_308():
    # https://github.com/delph-in/pydelphin/issues/301
    x = r.from_string(
        '>1\n'
        '#1\n'
        r'!(^| )([()%,])([^ ])	\1\2 \3' '\n'
        r'!([^ ])([()%,])( |$)	\1 \2\3' '\n'
        '#\n'
    ).apply('(42%),')
    assert x.string == '( 42 % ) ,'


def test_iterative_group_in_other_module_issue_308():
    # https://github.com/delph-in/pydelphin/issues/301
    grp = (
        '#1\n'
        r'!(^| )([()%,])([^ ])	\1\2 \3' '\n'
        r'!([^ ])([()%,])( |$)	\1 \2\3' '\n'
        '#\n'
    )
    with pytest.raises(repp.REPPError):
        r.from_string('>1\n', modules={'i': r.from_string(grp)})
    with pytest.raises(repp.REPPError):
        r.from_string(grp, modules={'i': r.from_string('>1\n')})


def test_tokenizer_in_top_module_issue_308():
    # https://github.com/delph-in/pydelphin/issues/301
    assert len(r.from_string(r':[\t ]').tokenize('a b').tokens) == 2
    # only one tokenizer pattern allowed
    with pytest.raises(repp.REPPError):
        r.from_string(
            ':[\\t ]\n'
            ':[\\t\\f\\n ]'
        )
    # tokenizer pattern not in top-level is not used
    assert len(
        r.from_string(
            '>a',
            modules={'a': r.from_string(r':[b]')}
        ).tokenize('aba').tokens
    ) == 1


def test_tokenizer_or_meta_not_in_iterative_group_issue_308():
    # https://github.com/delph-in/pydelphin/issues/301
    assert len(r.from_string('@meta\n:[\t ]').tokenize('a b').tokens) == 2
    with pytest.raises(repp.REPPError):
        r.from_string(
            '#1\n'
            '@meta\n'
            '!a	b\n'
            '#\n'
            '>1\n'
        )
    with pytest.raises(repp.REPPError):
        r.from_string(
            '#1\n'
            ':[\\t ]\n'
            '!a	b\n'
            '#\n'
            '>1\n'
        )


def test_global_module_namespace_issue_308_inner():
    # https://github.com/delph-in/pydelphin/issues/301
    rpp = r.from_string(
        '#1\n'
        '#2\n'
        '!b	c\n'
        '#\n'
        '!a	b\n'
        '#\n'
        '>2\n'
    )
    assert rpp.apply('aaa').string == 'aaa'
    assert rpp.apply('bbb').string == 'ccc'


def test_global_module_namespace_issue_308_outer():
    rpp = r.from_string(
        '#1\n'
        '#2\n'
        '!b	c\n'
        '#\n'
        '!a	b\n'
        '#\n'
        '>1\n'
    )
    assert rpp.apply('aaa').string == 'bbb'
    assert rpp.apply('bbb').string == 'bbb'


def test_global_module_namespace_issue_308_multiple():
    rpp = r.from_string(
        '#1\n'
        '!b	c\n'
        '#\n'
        '>a\n'
        '>1\n',
        modules={
            'a': r.from_string(
                '#1\n'
                '!a	b\n'
                '#\n'
                '>1\n'
            )
        },
        active=('a'),
    )
    assert rpp.apply('aaa').string == 'ccc'


def test_global_module_namespace_issue_308_collision():
    with pytest.raises(repp.REPPError):
        r.from_string(
            '#1\n'
            '!a	b\n'
            '#\n'
            '#1\n'
            '!b	c\n'
            '#\n'
            '>1\n'
        )
    with pytest.raises(repp.REPPError):
        r.from_string(
            '#1\n'
            '!a	b\n'
            '#1\n'
            '!b	c\n'
            '#\n'
            '#\n'
            '>1\n'
        )
