
from __future__ import absolute_import

import warnings, codecs, io
import re
from datetime import datetime

from collections import deque
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


def parse_datetime(s):
    if re.match(r':?(today|now)', s):
        return datetime.now()

    # YYYY-MM-DD HH:MM:SS
    m = re.match(
        r'''
        (?P<y>[0-9]{4})
        -(?P<m>[0-9]{1,2}|\w{3})
        (?:-(?P<d>[0-9]{1,2}))?
        (?:\s*\(?
        (?P<H>[0-9]{2}):(?P<M>[0-9]{2})(?::(?P<S>[0-9]{2}))?
        \)?)?''', s, flags=re.VERBOSE)
    if m is None:
        # DD-MM-YYYY HH:MM:SS
        m = re.match(
            r'''
            (?:(?P<d>[0-9]{1,2})-)?
            (?P<m>[0-9]{1,2}|\w{3})
            -(?P<y>[0-9]{2}(?:[0-9]{2})?)
            (?:\s*\(?
                (?P<H>[0-9]{2}):(?P<M>[0-9]{2})(?::(?P<S>[0-9]{2}))?
            \)?)?''', s, flags=re.VERBOSE)
    if m is not None:
        return datetime.strptime(_date_fix(m), '%Y-%m-%d %H:%M:%S')

    return None


def _date_fix(mo):
    y = mo.group('y')
    if len(y) == 2:
        y = '20' + y  # buggy in ~80yrs or if using ~20yr-old data :)
    m = mo.group('m')
    if len(m) == 3:  # assuming 3-letter abbreviations
        m = str(datetime.strptime(m, '%b').month)
    d = mo.group('d') or '01'
    H = mo.group('H') or '00'
    M = mo.group('M') or '00'
    S = mo.group('S') or '00'
    return '{}-{}-{} {}:{}:{}'.format(y, m, d, H, M, S)



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

from delphin.lib.pegre import PegreResult

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


class LookaheadIterator(object):
    """
    Wrapper around an iterator or generator that allows for peeking
    at the nth token of any n, and the ability to skip intervening
    tokens (e.g., what is the 3rd token that is not a comment?).
    """
    def __init__(self, iterable, n=1024):
        assert n > 0
        self._iterable = iterable
        self._n = n
        self._buffer = deque()
        self._buffer_fill()

    def _buffer_fill(self, n=None):
        # append up to buffer length n
        if n is None:
            n = self._n
        iterable = self._iterable
        buffer = self._buffer
        append = buffer.append
        for i in range(max(n - len(buffer), 0)):
            try:
                datum = next(iterable)
                append(datum)
            except StopIteration:
                if len(buffer) == 0:
                    raise
                else:
                    break

    def next(self, skip=None):
        """
        Remove the next datum from the buffer and return it.
        """
        buffer = self._buffer
        popleft = buffer.popleft
        if skip is not None:
            while True:
                try:
                    if not skip(buffer[0]):
                        break
                    popleft()
                except IndexError:
                    self._buffer_fill()
        try:
            datum = popleft()
        except IndexError:
            self._buffer_fill()
            datum = popleft()
        return datum

    def peek(self, n=0, skip=None, drop=False):
        """
        Return the *n*th datum from the buffer.
        """
        buffer = self._buffer
        popleft = buffer.popleft
        datum = None
        if skip is not None:
            stack = []
            stackpush = stack.append
            while n >= 0:
                try:
                    datum = popleft()
                except IndexError:
                    self._buffer_fill()
                    datum = popleft()
                if not skip(datum):
                    n -= 1
                    stackpush(datum)
                elif not drop:
                    stackpush(datum)
            buffer.extendleft(reversed(stack))
        else:
            self._buffer_fill(n + 1)
            datum = buffer[n]
        return datum


# modified from https://www.python.org/dev/peps/pep-0263/#defining-the-encoding
_encoding_symbol_re = re.compile(
    b'^.*?coding[:=][ \\t]*([-_.a-zA-Z0-9]+)', re.IGNORECASE)

def detect_encoding(filename, default_encoding='utf-8', comment_char=b';'):
    encoding = None
    with io.open(filename, 'rb') as fh:
        line1 = fh.readline()
    # strip off any UTF-8 BOM and leading spaces
    if line1.startswith(codecs.BOM_UTF8):
        line1 = line1[len(codecs.BOM_UTF8):].lstrip()
        has_bom = True
    else:
        line1 = line1.lstrip()
        has_bom = False

    if line1.startswith(comment_char):
        re_match1 = _encoding_symbol_re.search(line1)
        if re_match1:
            match = re_match1.group(1).decode('ascii').lower()
            if codecs.lookup(match):
                encoding = match

    if has_bom:
        if encoding and encoding != 'utf-8':
            raise ValueError("Declared encoding does not match BOM")
        else:
            encoding = 'utf-8'

    if not encoding:
        encoding = default_encoding

    return encoding

