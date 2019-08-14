
"""
Utility functions.
"""

from typing import Union
from pathlib import Path
import warnings
import pkgutil
import codecs
import re
from collections import deque, namedtuple
from functools import wraps
from enum import IntEnum

# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401


PathLike = Union[str, Path]


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


def safe_int(x):
    try:
        x = int(x)
    except ValueError:
        pass
    return x


# inspired by NetworkX is_connected():
# https://networkx.github.io/documentation/latest/_modules/networkx/algorithms/components/connected.html#is_connected
def _bfs(g, start=None):
    if not g:
        return {start} if start is not None else set()
    seen = set()
    if start is None:
        start = next(iter(g))
    agenda = deque([start])
    while agenda:
        x = agenda.popleft()
        if x not in seen:
            seen.add(x)
            agenda.extend(y for y in g.get(x, []) if y not in seen)
    return seen


def _connected_components(nodes, edges):
    if not edges:
        return [{node} for node in nodes]
    g = {n: set() for n in nodes}
    for n1, n2 in edges:
        g[n1].add(n2)
        g[n2].add(n1)
    # find connected components
    components = []
    seen = set()
    for n in nodes:
        if n not in seen:
            component = _bfs(g, n)
            seen.update(component)
            components.append(component)
    return components


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

SExprResult = namedtuple('SExprResult', 'data remainder')

# escapes from https://en.wikipedia.org/wiki/S-expression#Use_in_Lisp
_SExpr_escape_chars = r'"\s\(\)\[\]\{\}\\;'
_SExpr_symbol_re = re.compile(r'(?:[^{}]+|\\.)+'.format(_SExpr_escape_chars))


def _SExpr_unescape_symbol(s):
    return re.sub(r'\\([{}])'.format(_SExpr_escape_chars), r'\1', s)


def _SExpr_unescape_string(s):
    return re.sub(r'\\(["\\])', r'\1', s)


class _SExprParser(object):
    def parse(self, s):
        i = 0
        n = len(s)
        while i < n and s[i].isspace():
            i += 1
        if i == n:
            return SExprResult([], '')
        assert s[i] == '('
        i += 1
        while i < n and s[i].isspace():
            i += 1
        stack = [[]]
        while i < n:
            c = s[i]
            if c.isdigit() or c == '-' and s[i+1].isdigit():  # numbers
                j = i + 1
                while s[j].isdigit():
                    j += 1
                c = s[j]
                if c in '.eE':  # float
                    if c == '.':
                        j += 1
                        while s[j].isdigit():
                            j += 1
                    if c in 'eE':
                        j += 1
                        if s[j] in '+=':
                            j += 1
                        while s[j].isdigit():
                            j += 1
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
                    return SExprResult(xs, s[i+1:])
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


# attach an additional method for convenience
def _format_SExpr(d):
    if isinstance(d, tuple) and len(d) == 2:
        return '({} . {})'.format(d[0], d[1])
    elif isinstance(d, (tuple, list)):
        return '({})'.format(' '.join(map(_format_SExpr, d)))
    elif isinstance(d, str):
        return d
    else:
        return repr(d)


SExpr = _SExprParser()
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


class LookaheadLexer(LookaheadIterator):
    def __init__(self, iterable, error_class, n=1024):
        self._errcls = error_class
        super().__init__(iterable, n=n)

    def expect(self, *args, skip=None):
        vals = []
        for (ttype, tform) in args:
            gid, token, lineno, offset, pos = self.next(skip=skip)
            err = None
            if ttype is not None and gid != ttype:
                err = str(ttype)
            elif tform is not None and token != tform:
                err = repr(tform)
            if err is not None:
                raise self._errcls('expected: ' + err,
                                   lineno=lineno,
                                   offset=offset,
                                   text=token)
            vals.append(token)
        if len(args) == 1:
            return vals[0]
        else:
            return vals

    def accept(self, arg, skip=None, drop=False):
        ttype, tform = arg
        gid, token, lineno, offset, pos = self.peek(skip=skip, drop=drop)
        if ((ttype is None or gid == ttype)
                and (tform is None or token == tform)):
            self.next(skip=skip)
            return token
        return None

    def choice(self, *args, skip=None):
        gid, token, lineno, offset, pos = self.next(skip=skip)
        for (ttype, tform) in args:
            if ((ttype is None or gid == ttype)
                    and (tform is None or token == tform)):
                return gid, token
        errs = [str(ttype) if ttype is not None else repr(tform)
                for ttype, tform in args]
        raise self._errcls('expected one of: ' + ', '.join(errs),
                           lineno=lineno, text=token)

    def expect_type(self, *args, skip=None):
        return self.expect(*((arg, None) for arg in args), skip=skip)

    def expect_form(self, *args, skip=None):
        return self.expect(*((None, arg) for arg in args), skip=skip)

    def accept_type(self, arg, skip=None, drop=False):
        return self.accept((arg, None), skip=skip, drop=drop)

    def accept_form(self, arg, skip=None, drop=False):
        return self.accept((None, arg), skip=skip, drop=drop)

    def choice_type(self, *args, skip=None):
        return self.choice(*((arg, None) for arg in args), skip=skip)

    def choice_form(self, *args, skip=None):
        return self.choice(*((None, arg) for arg in args), skip=skip)


class Lexer(object):
    def __init__(self, tokens, error_class=None):
        self.tokens = tokens
        self.tokentypes = None

        if error_class is None:
            from delphin.exceptions import PyDelphinSyntaxError as error_class
        self._errcls = error_class

        self._configure()

    def _configure(self):
        patterns = []
        types = []
        desc = {}
        for group, token in enumerate(self.tokens, 1):
            pattern, name = token

            numgroups = re.compile(pattern).groups
            if numgroups == 0:
                pattern = '(' + pattern + ')'
            elif numgroups != 1:
                raise ValueError(
                    'pattern does not have 0 or 1 group: ' + pattern)
            patterns.append(pattern)

            name, _, description = name.partition(':')
            if description:
                desc[name] = description
            types.append(name)

        self._re = re.compile('|'.join(patterns))
        e = IntEnum('TokenTypes', types)
        e.__str__ = lambda self, desc=desc: desc.get(self.name, self.name)
        self.tokentypes = e

    def lex(self, lineiter):
        return LookaheadLexer(self.prelex(lineiter), self._errcls)

    def prelex(self, lineiter):
        """
        Lex the input string

        Yields:
            (gid, token, line_number, offset, pos) where offset is the
            character position within the line and pos is the
            character position in the full input
        """
        # loop optimizations
        finditer = self._re.finditer
        UNEXPECTED = self.tokentypes.UNEXPECTED

        lines = enumerate(lineiter, 1)
        lineno = line_pos = 0
        try:
            for lineno, line in lines:
                matches = finditer(line)
                for m in matches:
                    gid = m.lastindex
                    offset = m.start()
                    if gid == UNEXPECTED:
                        raise self._errcls(
                            'unexpected input',
                            lineno=lineno,
                            offset=offset,
                            text=line)
                    token = m.group(gid)
                    yield (gid, token, lineno, offset, line_pos + offset)
                line_pos += len(line) + 1  # +1 for newline character
        except StopIteration:
            pass


# modified from https://www.python.org/dev/peps/pep-0263/#defining-the-encoding
_encoding_symbol_re = re.compile(
    b'^.*?coding[:=][ \\t]*([-_.a-zA-Z0-9]+)', re.IGNORECASE)


def detect_encoding(filename, default_encoding='utf-8', comment_char=b';'):
    encoding = None
    with open(filename, 'rb') as fh:
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


def namespace_modules(ns):
    """Return the name to fullname mapping of modules in package *ns*."""
    return {name: '{}.{}'.format(ns.__name__, name)
            for _, name, _ in pkgutil.iter_modules(ns.__path__)}
