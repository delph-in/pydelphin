import warnings
from functools import wraps

def deprecated(message=None, final_version=None, alternative=None):
    if message is None:
        message = "Function '{name}' is deprecated"
        if final_version is not None:
            message += " and will be removed from version {version}"
        if alternative is not None:
            message += '; use the following instead: {alternative}'

    def deprecated_decorator(f):
        @wraps(f)
        def deprecated_wrapper(*args, **kwargs):
            warnings.warn(
                message.format(
                    name=f.__name__,
                    version=final_version,
                    alternative=alternative
                ),
                DeprecationWarning,
                stacklevel=2
            )
            return f(*args, **kwargs)
        return deprecated_wrapper
    return deprecated_decorator

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
    PegreResult
)

# escapes from https://en.wikipedia.org/wiki/S-expression#Use_in_Lisp
_SExpr_escape_chars = r'"\s\(\)\[\]\{\}\\;'
_SExpr_symbol_re = re.compile(r'(?:[^{}]+|\\.)+'.format(_SExpr_escape_chars))

def _SExpr_unescape_symbol(s):
    return re.sub(r'\\([{}])'.format(_SExpr_escape_chars), r'\1', s)

def _SExpr_unescape_string(s):
    return re.sub(r'\\(["\\])', r'\1', s)

class SExprParser(object):
    def parse(self, s):
        i = 0
        n = len(s)
        while i < n and s[i].isspace(): i += 1
        if i == n: return PegreResult('', [], None)
        assert s[i] == '('
        i += 1
        while i < n and s[i].isspace(): i += 1
        stack = [[]]
        while i < n:
            c = s[i]
            if c.isdigit() or c == '-' and s[i+1].isdigit():  # numbers
                j = i + 1
                while s[j].isdigit(): j += 1
                c = s[j]
                if c in '.eE':  # float
                    if c == '.':
                        j += 1
                        while s[j].isdigit(): j += 1
                    if c in 'eE':
                        j += 1
                        if s[j] in '+=': j += 1
                        while s[j].isdigit(): j += 1
                    stack[-1].append(float(s[i:j]))
                else:  # int
                    stack[-1].append(int(s[i:j]))
                i = j
            elif c == '"':  # quoted strings
                j = i + 1
                while s[j] != '"':
                    if s[j] == '\\':
                        j += 2
                    else:
                        j += 1
                stack[-1].append(_SExpr_unescape_string(s[i+1:j]))
                i = j + 1
            elif c == '(':
                stack.append([])
                i += 1
            elif c == ')':
                xs = stack.pop()
                if len(xs) == 3 and xs[1] == '.':
                    xs = tuple(xs[::2])
                if len(stack) == 0:
                    return PegreResult(s[i+1:], xs, None)
                else:
                    stack[-1].append(xs)
                i += 1
            elif c.isspace():
                i += 1
            else:
                m = _SExpr_symbol_re.match(s, pos=i)
                if m is None:
                    raise ValueError('Invalid S-Expression: ' + s)
                stack[-1].append(_SExpr_unescape_symbol(m.group(0)))
                i += len(m.group(0))

SExpr = SExprParser()

# _SExpr = nonterminal('SExpr')
# _Symbol = regex(r'(?:[^{ec}]+|\\.)+'.format(ec=_SExpr_escape_chars),
#                 value=_SExpr_unescape_symbol)
# # dummy choice around DQString just to get character unescaping
# _String = choice(DQString, value=_SExpr_unescape_string)

# SExpr = Peg(
#     grammar=dict(
#         start=sequence(Spacing, _SExpr, value=lambda xs: xs[1]),
#         SExpr=choice(
#             # atom
#             sequence(choice(Float, Integer, _String, _Symbol), Spacing,
#                      value=lambda xs: xs[0]),
#             # Expression
#             bounded(
#                 regex(r'\(\s*'),
#                 choice(
#                     # DotPair
#                     sequence(_SExpr, regex(r'\.\s*'), _SExpr,
#                              value=lambda xs: tuple([xs[0], xs[2]])),
#                     # List
#                     delimited(_SExpr, Spacing)
#                 ),
#                 regex(r'\)\s*')
#             )
#         )
#     )
# )

# attach an additional method for convenience
def _format_SExpr(d):
    if isinstance(d, tuple) and len(d) == 2:
        return '({} . {})'.format(d[0], d[1])
    elif isinstance(d, (tuple, list)):
        return '({})'.format(' '.join(map(_format_SExpr, d)))
    elif isinstance(d, stringtypes):
        return d
    else:
        return repr(d)

SExpr.format = _format_SExpr
