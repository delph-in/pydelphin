
import re
from functools import wraps
from collections import Sequence

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
                    return (s, val(obj), span)
                else:
                    return (s, val, span)
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
    def match_literal(s, grm, pos):
        if s[:xlen] == x:
            return (s[xlen:], x, (pos, pos+xlen))
        raise PegreError(msg, pos)
    return match_literal

@valuemap
def regex(r):
    """
    Create a PEG function to match a regular expression.
    """
    if isinstance(r, str):
        p = re.compile(r)
    else:
        p = r
    msg = 'Expected to match: {}'.format(p.pattern)
    def match_regex(s, grm, pos):
        m = p.match(s)
        if m is not None:
            start, end = m.span()
            return (s[m.end():], m.group(), (pos+start, pos+end))
        raise PegreError(msg, pos)
    return match_regex

@valuemap
def nonterminal(n):
    """
    Create a PEG function to match a nonterminal.
    """
    def match_nonterminal(s, grm, pos):
        expr = grm[n]
        return expr(s, grm, pos)
    return match_nonterminal

@valuemap
def and_next(e):
    """
    Create a PEG function for positive lookahead.
    """
    def match_and_next(s, grm, pos):
        if e(s, grm, pos):
            return (s, Ignore, (pos, pos))
        raise PegreError(msg, pos)
    return match_and_next

@valuemap
def not_next(e):
    """
    Create a PEG function for negative lookahead.
    """
    def match_not_next(s, grm, pos):
        if not e(s, grm, pos):
            return (s, Ignore, (pos, pos))
        raise PegreError(msg, pos)
    return match_not_next

@valuemap
def sequence(*es):
    """
    Create a PEG function to match a sequence.
    """
    def match_sequence(s, grm, pos):
        data = []
        start = pos
        for e in es:
            s, obj, span = e(s, grm, pos)
            pos = span[1]
            if obj is not Ignore:
                data.append(obj)
        return (s, data, (start, pos))
    return match_sequence

@valuemap
def choice(*es):
    """
    Create a PEG function to match an ordered choice.
    """
    msg = 'Expected one of: {}'.format(', '.join(map(repr, es)))
    def match_choice(s, grm, pos):
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
    def match_optional(s, grm, pos):
        try:
            return e(s, grm, pos)
        except PegreError:
            return (s, default, (pos, pos))
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
    def match_zero_or_more(s, grm, pos):
        start = pos
        try:
            s, obj, span = e(s, grm, pos)
            pos = span[1]
            data = [] if obj is Ignore else [obj]
        except PegreError:
            return (s, [], (pos, pos))
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
        return (s, data, (start, pos))
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
    def match_one_or_more(s, grm, pos):
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
        return (s, data, (start, pos))
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

    def parse(self, s):
        result = self.grammar[self.start](s, self.grammar, 0)
        return result[1]
