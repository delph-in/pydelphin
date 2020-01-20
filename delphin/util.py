
"""
Utility functions.
"""

from typing import (Union, Iterable, Iterator, Dict, List, Tuple, NamedTuple)
from pathlib import Path
import warnings
import importlib
import pkgutil
import codecs
import re
from itertools import permutations
from collections import deque, defaultdict
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


def _isomorphism(g1, g2, top1, top2) -> Dict[str, str]:
    """
    Return the first isomorphism found for graphs *g1* and *g2*.

    Start from *top1* and *top2*.

    *g1* and *g2* are dictionaries mapping each node id to inner
    dictionaries that map node ids to some data where there exists an
    edge between the two node target. The data is an arbitrary string
    used for matching heuristics.

    This assumes that the graphs are not multigraphs.
    """
    _iso_inv_map(g1)
    _iso_inv_map(g2)

    hypothesis: Dict[str, str] = {}
    agenda: List[Tuple[str, str]] = next(
        _iso_candidates({top1: None}, {top2: None}, g1, g2, hypothesis),
        [])
    return next(_iso_vf2(hypothesis, g1, g2, agenda), {})


def _iso_inv_map(d):
    """
    Augment *d* with inverse mappings.

    Assumes *d* is not a multigraph.
    """
    _d = {}
    for src, d2 in d.items():
        for tgt, data in d2.items():
            if tgt is not None and src != tgt:
                if tgt not in _d:
                    _d[tgt] = {}
                _d[tgt][src] = '--' + data
    for k, d2 in _d.items():
        d[k].update(d2)


def _iso_vf2(hyp, g1, g2, agenda):
    # base case
    if len(hyp) == len(g1) or not agenda:
        yield hyp
    n1, n2 = agenda.pop()
    # get edges, filter node data and self edges
    n1s = {n: d for n, d in g1[n1].items() if n is not None and n != n1}
    n2s = {n: d for n, d in g2[n2].items() if n is not None and n != n2}
    # update the current state
    new_hyp = dict(hyp)
    new_hyp[n1] = n2
    for c_agenda in _iso_candidates(n1s, n2s, g1, g2, new_hyp):
        yield from _iso_vf2(new_hyp, g1, g2, agenda + c_agenda)


def _iso_candidates(n1s, n2s, g1, g2, hyp):
    # get the inverse mapping for faster reverse lookups
    inv = {n2: n1 for n1, n2 in hyp.items()}
    for _n2s in permutations(list(n2s)):
        # filter out bad mappings
        agenda = []
        for n1, n2 in zip(list(n1s), _n2s):
            if hyp.get(n1) == n2 and inv.get(n2) == n1:
                continue  # no issue, but don't add to agenda
            elif n1 in hyp or n2 in inv:
                agenda = []  # already traversed, not compatible
                break
            elif len(g1[n1]) != len(g2[n2]):
                agenda = []  # incompatible arity
                break
            elif g1[n1].get(None) != g2[n2].get(None):
                agenda = []  # incompatible node data
                break
            elif n1s[n1] != n2s[n2]:
                agenda = []  # incompatible edge data
                break
            else:
                agenda.append((n1, n2))
        if agenda:
            yield agenda
    # Finally yield an empty agenda because there's nothing to do
    yield []


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

_Val = Union[str, int, float]


class SExprResult(NamedTuple):
    """The result of parsing an S-Expression."""
    data: Union[Tuple[_Val, _Val], List[_Val]]
    remainder: str


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
            # numbers
            if c.isdigit() or c == '-' and s[i + 1].isdigit():
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
                stack[-1].append(
                    _SExpr_unescape_string(s[i + 1 : j]))  # noqa: E203
                i = j + 1
            elif c == '(':
                stack.append([])
                i += 1
            elif c == ')':
                xs = stack.pop()
                if len(xs) == 3 and xs[1] == '.':
                    xs = tuple(xs[::2])
                if len(stack) == 0:
                    return SExprResult(xs, s[i + 1 :])  # noqa: E203
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

    def format(self, d):
        if isinstance(d, tuple) and len(d) == 2:
            return f'({d[0]} . {d[1]})'
        elif isinstance(d, (tuple, list)):
            return '({})'.format(' '.join(map(self.format, d)))
        elif isinstance(d, str):
            return d
        else:
            return repr(d)


SExpr = _SExprParser()


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
                    return False
                else:
                    break
        return True

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
                    if not self._buffer_fill():
                        raise StopIteration
        try:
            datum = popleft()
        except IndexError:
            if not self._buffer_fill():
                raise StopIteration
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
                    if not self._buffer_fill():
                        raise StopIteration
                    datum = popleft()
                if not skip(datum):
                    n -= 1
                    stackpush(datum)
                elif not drop:
                    stackpush(datum)
            buffer.extendleft(reversed(stack))
        else:
            if not self._buffer_fill(n + 1):
                raise StopIteration
            datum = buffer[n]
        return datum


_Token = Tuple[int, str, int, int, str]


class LookaheadLexer(LookaheadIterator):
    def __init__(self, iterable, error_class, n=1024):
        self._errcls = error_class
        super().__init__(iterable, n=n)

    def expect(self, *args, skip=None):
        vals = []
        for (ttype, tform) in args:
            gid, token, lineno, offset, line = self.next(skip=skip)
            err = None
            if ttype is not None and gid != ttype:
                err = str(ttype)
            elif tform is not None and token != tform:
                err = repr(tform)
            if err is not None:
                raise self._errcls('expected: ' + err,
                                   lineno=lineno,
                                   offset=offset,
                                   text=line)
            vals.append(token)
        if len(args) == 1:
            return vals[0]
        else:
            return vals

    def accept(self, arg, skip=None, drop=False):
        ttype, tform = arg
        gid, token, lineno, offset, line = self.peek(skip=skip, drop=drop)
        if ((ttype is None or gid == ttype)
                and (tform is None or token == tform)):
            self.next(skip=skip)
            return token
        return None

    def choice(self, *args, skip=None):
        gid, token, lineno, offset, line = self.next(skip=skip)
        for (ttype, tform) in args:
            if ((ttype is None or gid == ttype)
                    and (tform is None or token == tform)):
                return gid, token
        errs = [str(ttype) if ttype is not None else repr(tform)
                for ttype, tform in args]
        raise self._errcls('expected one of: ' + ', '.join(errs),
                           lineno=lineno, offset=offset, text=line)

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

    def lex(self, lineiter: Iterable[str]) -> LookaheadLexer:
        return LookaheadLexer(self.prelex(lineiter), self._errcls)

    def prelex(self, lineiter: Iterable[str]) -> Iterator[_Token]:
        """
        Lex the input string

        Yields:
            (gid, token, line_number, offset, line) where offset is the
            character position within the line
        """
        # loop optimizations
        finditer = self._re.finditer
        UNEXPECTED = self.tokentypes.UNEXPECTED

        lines = enumerate(lineiter, 1)
        lineno = 0
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
                    yield (gid, token, lineno, offset, line)
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
    return {name: f'{ns.__name__}.{name}'
            for _, name, _ in pkgutil.iter_modules(ns.__path__)}


def inspect_codecs():
    """
    Inspect all available codecs and return a description.

    The description is a mapping from a declared representation to a
    list of codecs for that representation. Each item on the list is a
    tuple of ``(codec_name, codec_module, codec_description)``. If
    there is any error when attempting to load a codec module, the
    representation will be ``(ERROR)``, the module will be ``None``,
    and the description will be the exception message.
    """
    import delphin.codecs
    codecs = namespace_modules(delphin.codecs)
    result = defaultdict(list)
    for name, fullname in codecs.items():
        try:
            mod = importlib.import_module(fullname)
            rep = mod.CODEC_INFO['representation']
            description = mod.CODEC_INFO.get('description', '')
        except Exception as ex:
            result['(error)'].append((name, None, str(ex)))
        else:
            result[rep].append((name, mod, description))
    return result


def import_codec(name: str):
    """
    Import codec *name* and return the module.
    """
    import delphin.codecs
    codecs = namespace_modules(delphin.codecs)
    fullname = codecs[name]
    return importlib.import_module(fullname)


def make_highlighter(fmt):
    try:
        import pygments
        from pygments.formatters import Terminal256Formatter as _formatter
    except ImportError:
        return str

    highlight = str  # backoff function

    if fmt == 'simplemrs':
        try:
            import delphin.highlight
        except ImportError:
            pass
        else:

            def highlight(text):
                return pygments.highlight(
                    text,
                    delphin.highlight.SimpleMRSLexer(),
                    _formatter(style=delphin.highlight.MRSStyle))

    elif fmt == 'diff':
        from pygments.lexers.diff import DiffLexer

        def highlight(text):
            # this seems to append a newline, so remove it
            return pygments.highlight(
                text,
                DiffLexer(),
                _formatter()).rstrip('\n')

    return highlight
