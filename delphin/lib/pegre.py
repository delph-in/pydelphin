# Pegre is available at: https://github.com/goodmami/pegre
# This version may have minor modifications.
#
# The license of Pegre is as follows:
#
# The MIT License (MIT)
#
# Copyright (c) 2016 Michael Wayne Goodman
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import re
from functools import wraps
from collections import namedtuple

try:
    stringtypes = (str, unicode)
except NameError:
    stringtypes = (str,)

__all__ = [
    'Ignore',
    'literal',
    'regex',
    'nonterminal',
    'and_next',
    'not_next',
    'sequence',
    'choice',
    'optional',
    'zero_or_more',
    'one_or_more',
    'bounded',
    'delimited',
    'Peg',
]

PegreResult = namedtuple('PegreResult', ('remainder', 'data', 'span'))

class PegreError(Exception):
    def __init__(self, message, position):
        self.message = message
        self.position = position
    def __str__(self):
        return 'At position {}: {}'.format(self.position, self.message)

class PegreChoiceError(PegreError):
    def __init__(self, failures, position):
        message = '\n' + '\n'.join(
            '  At position {}: {}'.format(pos, msg)
            for msg, pos in failures
        )
        PegreError.__init__(self, message, position)

Ignore = object()  # just a singleton for identity checking

def valuemap(f):
    """
    Decorator to help PEG functions handle value conversions.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'value' in kwargs:
            val = kwargs['value']
            del kwargs['value']
            _f = f(*args, **kwargs)
            def valued_f(*args, **kwargs):
                result = _f(*args, **kwargs)
                s, obj, span = result
                if callable(val):
                    return PegreResult(s, val(obj), span)
                else:
                    return PegreResult(s, val, span)
            return valued_f
        else:
            return f(*args, **kwargs)
    return wrapper

@valuemap
def literal(x):
    """
    Create a PEG function to consume a literal.
    """
    xlen = len(x)
    msg = 'Expected: "{}"'.format(x)
    def match_literal(s, grm=None, pos=0):
        if s[:xlen] == x:
            return PegreResult(s[xlen:], x, (pos, pos+xlen))
        raise PegreError(msg, pos)
    return match_literal

@valuemap
def regex(r):
    """
    Create a PEG function to match a regular expression.
    """
    if isinstance(r, stringtypes):
        p = re.compile(r)
    else:
        p = r
    msg = 'Expected to match: {}'.format(p.pattern)
    def match_regex(s, grm=None, pos=0):
        m = p.match(s)
        if m is not None:
            start, end = m.span()
            data = m.groupdict() if p.groupindex else m.group()
            return PegreResult(s[m.end():], data, (pos+start, pos+end))
        raise PegreError(msg, pos)
    return match_regex

@valuemap
def nonterminal(n):
    """
    Create a PEG function to match a nonterminal.
    """
    def match_nonterminal(s, grm=None, pos=0):
        if grm is None: grm = {}
        expr = grm[n]
        return expr(s, grm, pos)
    return match_nonterminal

@valuemap
def and_next(e):
    """
    Create a PEG function for positive lookahead.
    """
    def match_and_next(s, grm=None, pos=0):
        try:
            e(s, grm, pos)
        except PegreError as ex:
            raise PegreError('Positive lookahead failed', pos)
        else:
            return PegreResult(s, Ignore, (pos, pos))
    return match_and_next

@valuemap
def not_next(e):
    """
    Create a PEG function for negative lookahead.
    """
    def match_not_next(s, grm=None, pos=0):
        try:
            e(s, grm, pos)
        except PegreError as ex:
            return PegreResult(s, Ignore, (pos, pos))
        else:
            raise PegreError('Negative lookahead failed', pos)
    return match_not_next

@valuemap
def sequence(*es):
    """
    Create a PEG function to match a sequence.
    """
    def match_sequence(s, grm=None, pos=0):
        data = []
        start = pos
        for e in es:
            s, obj, span = e(s, grm, pos)
            pos = span[1]
            if obj is not Ignore:
                data.append(obj)
        return PegreResult(s, data, (start, pos))
    return match_sequence

@valuemap
def choice(*es):
    """
    Create a PEG function to match an ordered choice.
    """
    msg = 'Expected one of: {}'.format(', '.join(map(repr, es)))
    def match_choice(s, grm=None, pos=0):
        errs = []
        for e in es:
            try:
                return e(s, grm, pos)
            except PegreError as ex:
                errs.append((ex.message, ex.position))
        if errs:
            raise PegreChoiceError(errs, pos)
    return match_choice

@valuemap
def optional(e, default=Ignore):
    """
    Create a PEG function to optionally match an expression.
    """
    def match_optional(s, grm=None, pos=0):
        try:
            return e(s, grm, pos)
        except PegreError:
            return PegreResult(s, default, (pos, pos))
    return match_optional

@valuemap
def zero_or_more(e, delimiter=None):
    """
    Create a PEG function to match zero or more expressions.

    Args:
        e: the expression to match
        delimiter: an optional expression to match between the
            primary *e* matches.
    """
    if delimiter is None:
        delimiter = lambda s, grm, pos: (s, Ignore, (pos, pos))
    def match_zero_or_more(s, grm=None, pos=0):
        start = pos
        try:
            s, obj, span = e(s, grm, pos)
            pos = span[1]
            data = [] if obj is Ignore else [obj]
        except PegreError:
            return PegreResult(s, [], (pos, pos))
        try:
            while True:
                s, obj, span = delimiter(s, grm, pos)
                pos = span[1]
                if obj is not Ignore:
                    data.append(obj)
                s, obj, span = e(s, grm, pos)
                pos = span[1]
                if obj is not Ignore:
                    data.append(obj)
        except PegreError:
            pass
        return PegreResult(s, data, (start, pos))
    return match_zero_or_more

@valuemap
def one_or_more(e, delimiter=None):
    """
    Create a PEG function to match one or more expressions.

    Args:
        e: the expression to match
        delimiter: an optional expression to match between the
            primary *e* matches.
    """
    if delimiter is None:
        delimiter = lambda s, grm, pos: (s, Ignore, (pos, pos))
    msg = 'Expected one or more of: {}'.format(repr(e))
    def match_one_or_more(s, grm=None, pos=0):
        start = pos
        s, obj, span = e(s, grm, pos)
        pos = span[1]
        data = [] if obj is Ignore else [obj]
        try:
            while True:
                s, obj, span = delimiter(s, grm, pos)
                pos = span[1]
                if obj is not Ignore:
                    data.append(obj)
                s, obj, span = e(s, grm, pos)
                pos = span[1]
                if obj is not Ignore:
                    data.append(obj)
        except PegreError:
            pass
        return PegreResult(s, data, (start, pos))
    return match_one_or_more

@valuemap
def bounded(pre, expr, post):
    return sequence(pre, expr, post, value=lambda x: x[1])

@valuemap
def delimited(expr, delim):
    return zero_or_more(expr, delimiter=delim, value=lambda x: x[::2])


class Peg(object):
    """
    A class to assist in parsing using a grammar of PEG functions.
    """
    def __init__(self, grammar, start='start'):
        self.start = start
        self.grammar = grammar

    def parse(self, s, start=None):
        if start is None: start = self.start
        result = self.grammar[start](s, self.grammar, 0)
        return result

# common definitions
Spacing  = regex(r'\s*')
Integer  = regex(r'-?\d+', value=int)
Float    = regex(r'-?(0|[1-9]\d*)(\.\d+[eE][-+]?|\.|[eE][-+]?)\d+',
                 value=float)
DQString = regex(r'"[^"\\]*(?:\\.[^"\\]*)*"', value=lambda s: s[1:-1])
SQString = regex(r"'[^'\\]*(?:\\.[^'\\]*)*'", value=lambda s: s[1:-1])

