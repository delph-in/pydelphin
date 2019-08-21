
from delphin import repp
from delphin.lnk import Lnk

def test_REPP():
    r = repp.REPP

    # single-module REPP

    x = r().apply('abc')
    assert x.string == 'abc'
    assert x.startmap.tolist() == [1,0,0,0,0]
    assert x.endmap.tolist() == [0,0,0,0,-1]

    x = r.from_string('').apply('abc')
    assert x.string == 'abc'
    assert x.startmap.tolist() == [1,0,0,0,0]
    assert x.endmap.tolist() == [0,0,0,0,-1]

    x = r.from_string(r'!a	b').apply('ccc')  # no match
    assert x.string == 'ccc'
    assert x.startmap.tolist() == [1, 0, 0, 0, 0]
    assert x.endmap.tolist() == [0, 0, 0, 0, -1]

    x = r.from_string(r'!a	b').apply('baba')
    assert x.string == 'bbbb'
    assert x.startmap.tolist() == [1,0,0,0,0,0]
    assert x.endmap.tolist() == [0,0,0,0,0,-1]

    x = r.from_string(r'!a	aa').apply('baba')
    assert x.string == 'baabaa'
    assert x.startmap.tolist() == [1,0,0,-1,-1,-1,-2,-2]
    assert x.endmap.tolist()  == [0,0,0,-1,-1,-1,-2,-3]

    x = r.from_string(r'!(\w+)	[\1]').apply('abc def')
    assert x.string == '[abc] [def]'
    assert x.startmap.tolist() == [1, 0,-1,-1,-1,-1,-2,-2,-3,-3,-3,-3,-4]
    assert x.endmap.tolist()   == [0,-1,-1,-1,-1,-2,-2,-3,-3,-3,-3,-4,-5]

    # From issue #250
    x = r.from_string(r'!(b)(a)	B\2r').apply('baba')
    assert x.string == 'BarBar'
    assert x.startmap.tolist() == [1, 0,-1,-2,-1,-2,-3,-2]
    assert x.endmap.tolist()   == [0, 1, 0,-1, 0,-1,-2,-3]

    x = r.from_string(r"!wo(n't)	will \1").apply("I won't go")
    assert x.string == "I will n't go"
    assert x.startmap.tolist() == [1,0,0,0,-1,-2,-3,-4,-3,-3,-3,-3,-3,-3,-3]
    assert x.endmap.tolist()   == [0,0,0,1, 0,-1,-2,-3,-3,-3,-3,-3,-3,-3,-4]

    x = r.from_string(r"!wo(n't)	will \1").tokenize("I won't go")
    assert len(x.tokens) == 4
    assert x.tokens[0].form == 'I'
    assert x.tokens[0].lnk == Lnk.charspan(0,1)
    assert x.tokens[1].form == 'will'
    assert x.tokens[1].lnk == Lnk.charspan(2,4)
    assert x.tokens[2].form == "n't"
    assert x.tokens[2].lnk == Lnk.charspan(4,7)
    assert x.tokens[3].form == 'go'
    assert x.tokens[3].lnk == Lnk.charspan(8,10)

    # additional modules/groups

    x = r.from_string('>a', modules={'a': r.from_string(r'!a	b')}, active=['a']).apply('baba')
    assert x.string == 'bbbb'
    assert x.startmap.tolist() == [1,0,0,0,0,0]
    assert x.endmap.tolist() == [0,0,0,0,0,-1]

    x = r.from_string('>a', modules={'a': r.from_string(r'!a	b')}).apply('baba', active=['a'])
    assert x.string == 'bbbb'
    assert x.startmap.tolist() == [1,0,0,0,0,0]
    assert x.endmap.tolist() == [0,0,0,0,0,-1]

    x = r.from_string('>a', modules={'a': r.from_string(r'!a	b')}).apply('baba')
    assert x.string == 'baba'
    assert x.startmap.tolist() == [1,0,0,0,0,0]
    assert x.endmap.tolist() == [0,0,0,0,0,-1]

    x = r.from_string('>a\n>b\n>c', modules={'a': r.from_string('!a	b'), 'b': r.from_string('!b	c'), 'c': r.from_string('!c	d')}, active=['a','b','c']).apply('baba')
    assert x.string == 'dddd'
    assert x.startmap.tolist() == [1,0,0,0,0,0]
    assert x.endmap.tolist() == [0,0,0,0,0,-1]

    x = r.from_string('>a\n>b\n>c', modules={'a': r.from_string('!a	b'), 'b': r.from_string('!b	c'), 'c': r.from_string('!c	d')}, active=['a']).apply('baba')
    assert x.string == 'bbbb'
    assert x.startmap.tolist() == [1,0,0,0,0,0]
    assert x.endmap.tolist() == [0,0,0,0,0,-1]

    # iterative groups

    x = r.from_string(
        r'!(^| )([()%,])([^ ])	\1\2 \3' '\n'
        r'!([^ ])([()%,])( |$)	\1 \2\3'
	).apply('(42%),')
    assert x.string == '( 42%) ,'
    assert x.startmap.tolist() == [1,0, 0,-1,-1,-1,-1,-1,-2,-2]
    assert x.endmap.tolist()   == [0,0,-1,-1,-1,-1,-1,-2,-2,-3]

    x = r.from_string(
        '#1\n'
        r'!(^| )([()%,])([^ ])	\1\2 \3' '\n'
        r'!([^ ])([()%,])( |$)	\1 \2\3' '\n'
        '#\n'
        '>1'
    ).apply('(42%),')
    assert x.string == '( 42 % ) ,'
    assert x.startmap.tolist() == [1,0, 0,-1,-1,-1,-2,-2,-3,-3,-4,-4]
    assert x.endmap.tolist()   == [0,0,-1,-1,-1,-2,-2,-3,-3,-4,-4,-5]

    # tokenization

    x = r.from_string(
        '#1\n'
        r'!(^| )([()%,])([^ ])	\1\2 \3' '\n'
        r'!([^ ])([()%,])( |$)	\1 \2\3' '\n'
        '#\n'
        '>1'
    ).tokenize('(42%),')
    assert len(x.tokens) == 5
    assert x.tokens[0].form == '('
    assert x.tokens[0].lnk == Lnk.charspan(0,1)
    assert x.tokens[1].form == '42'
    assert x.tokens[1].lnk == Lnk.charspan(1,3)
    assert x.tokens[2].form == '%'
    assert x.tokens[2].lnk == Lnk.charspan(3,4)
    assert x.tokens[3].form == ')'
    assert x.tokens[3].lnk == Lnk.charspan(4,5)
    assert x.tokens[4].form == ','
    assert x.tokens[4].lnk == Lnk.charspan(5,6)
