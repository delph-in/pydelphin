
try:
    stringtypes = (str, unicode)  # Python 2
except NameError:
    stringtypes = (str,)  # Python 3

def safe_int(x):
    try:
        x = int(x)
    except ValueError:
        pass
    return x

# unescaping escaped strings (potentially with unicode)
#   (disabled but left here in case a need arises)
# thanks: http://stackoverflow.com/a/24519338/1441112

# import re
# import codecs

# _ESCAPE_SEQUENCE_RE = re.compile(r'''
#     ( \\U........      # 8-digit hex escapes
#     | \\u....          # 4-digit hex escapes
#     | \\x..            # 2-digit hex escapes
#     | \\[0-7]{1,3}     # Octal escapes
#     | \\N\{[^}]+\}     # Unicode characters by name
#     | \\[\\'"abfnrtv]  # Single-character escapes
#     )''', re.UNICODE | re.VERBOSE
# )

# def unescape_string(s):
#     def decode_match(match):
#         return codecs.decode(match.group(0), 'unicode-escape')
#     return _ESCAPE_SEQUENCE_RE.sub(decode_match, s)


# S-expressions
#  e.g. (:n-inputs . 3) or (S (NP (NNS Dogs)) (VP (VBZ bark)))

import re

from delphin.lib.pegre import (
    sequence,
    choice,
    literal,
    regex,
    nonterminal,
    delimited,
    bounded,
    Spacing,
    Integer,
    Float,
    DQString,
    Peg,
)

# escapes from https://en.wikipedia.org/wiki/S-expression#Use_in_Lisp
_SExpr_escape_chars = r'"\s\(\)\[\]\{\}\\;'

def _SExpr_unescape_symbol(s):
    return re.sub(r'\\([{}])'.format(_SExpr_escape_chars), r'\1', s)

def _SExpr_unescape_string(s):
    return re.sub(r'\\(["\\])', r'\1', s)

_SExpr = nonterminal('SExpr')
_Symbol = regex(r'(?:[^{ec}]+|\\.)+'.format(ec=_SExpr_escape_chars),
                value=_SExpr_unescape_symbol)
# dummy choice around DQString just to get character unescaping
_String = choice(DQString, value=_SExpr_unescape_string)

SExpr = Peg(
    grammar=dict(
        start=sequence(Spacing, _SExpr, value=lambda xs: xs[1]),
        SExpr=choice(
            # atom
            sequence(choice(Float, Integer, _String, _Symbol), Spacing,
                     value=lambda xs: xs[0]),
            # Expression
            bounded(
                regex(r'\(\s*'),
                choice(
                    # DotPair
                    sequence(_SExpr, regex(r'\.\s*'), _SExpr,
                             value=lambda xs: tuple([xs[0], xs[2]])),
                    # List
                    delimited(_SExpr, Spacing)
                ),
                regex(r'\)\s*')
            )
        )
    )
)
