
"""
Utility functions.
"""

from typing import (
    Any,
    Union,
    Iterable,
    Iterator,
    Set,
    Dict,
    List,
    Tuple,
    NamedTuple,
)
from pathlib import Path
import warnings
import importlib
import pkgutil
import codecs
import re
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


_IsoGraph = Dict[str, Dict[Union[None, str], str]]
_IsoMap = Dict[str, str]
_IsoPairs = List[Tuple[str, str]]


def _vf2(g1: _IsoGraph, g2: _IsoGraph) -> _IsoMap:
    """See Cordella, Foggia, Sansone, and Vento 2004"""

    # augment graph with inverse edges, making it effectively undirected
    _vf2_inv_map(g1)
    _vf2_inv_map(g2)

    # VF2 is defined recursively but it is simple to make iterative
    mapping: _IsoMap = {}
    prev_n = None
    candidates = _vf2_candidates(mapping, g1, g2)
    states: List[Tuple[Union[None, str], _IsoPairs]] = []
    while len(mapping) < len(g2):
        pair_found = False
        while candidates and not pair_found:
            n, m = candidates.pop()
            if _vf2_feasible(mapping, g1, g2, n, m):
                pair_found = True

        if pair_found:
            # make new state
            mapping[n] = m
            states.append((prev_n, candidates))
            prev_n = n
            candidates = _vf2_candidates(mapping, g1, g2)
        elif prev_n is None:
            # end of the line; abort
            break
        else:
            # restore old state
            del mapping[prev_n]
            prev_n, candidates = states.pop()

    return mapping


def _vf2_inv_map(d: _IsoGraph) -> None:
    """
    Augment *d* with inverse mappings.

    Assumes *d* is not a multigraph.
    """
    _d: _IsoGraph = {}
    for src, d2 in d.items():
        for tgt, data in d2.items():
            if tgt is not None and src != tgt:
                if tgt not in _d:
                    _d[tgt] = {}
                _d[tgt][src] = '--' + data
    for k, d2 in _d.items():
        d[k].update(d2)


def _vf2_feasible(
        mapping: _IsoMap,
        g1: _IsoGraph,
        g2: _IsoGraph,
        n: str,
        m: str,
) -> bool:
    e1 = g1[n]  # edges from n in g1
    e2 = g2[m]  # edges from m in g2
    inv_map = {b: a for a, b in mapping.items()}  # inverse of bijection
    # semantic feasibility of nodes
    if e1.get(None, '') != e2.get(None, ''):
        return False
    # accounts for r_in, r_out
    if len(e1) != len(e2):
        return False
    # accounts for r_new (only 1 extra level of lookahead)
    if (len(_vf2_new(mapping, g1, n)) != len(_vf2_new(inv_map, g2, m))):
        return False
    # accounts for r_pred, r_succ
    if not (_vf2_consistent(mapping, g1, g2, n, m)
            and _vf2_consistent(inv_map, g2, g1, m, n)):
        return False
    return True


def _vf2_new(mapping: _IsoMap, g: _IsoGraph, a: str) -> Set[str]:
    new = set()
    agenda = [a]
    while agenda:
        cur = agenda.pop()
        for a_ in g[cur]:
            if not (a_ is None or a == cur or a in mapping or a in new):
                agenda.append(a_)
                new.add(a_)
    return new


def _vf2_consistent(
        mapping: _IsoMap,
        ga: _IsoGraph,
        gb: _IsoGraph,
        a: str,
        b: str,
) -> bool:
    for a_, data in ga[a].items():
        if a_ not in mapping:
            continue
        if mapping[a_] not in gb[b]:
            return False
        if gb[b][mapping[a_]] != data:  # semantic feasibility of edges
            return False
    return True


def _vf2_candidates(
        mapping: _IsoMap,
        g1: _IsoGraph,
        g2: _IsoGraph,
) -> _IsoPairs:
    # sides of the mapping as sets
    m1: Set[str] = set(mapping)
    m2: Set[str] = set(mapping.values())
    # combination of incoming and outgoing edges
    t1: Set[str] = set()
    t2: Set[str] = set()
    for n, m in mapping.items():
        t1.update(n_ for n_ in g1[n] if n_ is not None and n_ not in m1)
        t2.update(m_ for m_ in g2[m] if m_ is not None and m_ not in m2)

    # sorting t1 speeds up matches with t2 side when graphs are the same
    if t1 and t2:
        m = min(t2)
        return [(n1, m) for n1 in sorted(t1, reverse=True)]

    unmapped = set(g2) - m2
    if unmapped:
        m = min(set(g2) - m2)
        return [(n1, m) for n1 in sorted(set(g1) - m1, reverse=True)]
    else:
        return []


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

_Atom = Union[str, int, float]
_SExpr = Union[_Atom, '_Cons']
# The following would be nice, but Mypy doesn't do recursive types yet:
#     https://github.com/python/mypy/issues/731
# _Cons = Union[Tuple[_SExpr, _SExpr], List[_SExpr]]
_Cons = Union[Tuple[Any, Any], List[Any]]


class SExprResult(NamedTuple):
    """The result of parsing an S-Expression."""
    data: _Cons
    remainder: str


# escapes from https://en.wikipedia.org/wiki/S-expression#Use_in_Lisp
_SExpr_escape_chars = r'"\s\(\)\[\]\{\}\\;'
_SExpr_symbol_re = re.compile(r'(?:[^{}]+|\\.)+'.format(_SExpr_escape_chars))


def _SExpr_unescape_symbol(s):
    return re.sub(r'\\([{}])'.format(_SExpr_escape_chars), r'\1', s)


def _SExpr_unescape_string(s):
    return re.sub(r'\\(["\\])', r'\1', s)


def _SExpr_parse(s: str) -> SExprResult:
    s = s.lstrip()
    data: _Cons = []
    if not s:
        return SExprResult(data, '')
    assert s.startswith('(')
    i = 1
    n = len(s)
    stack: List[List[_SExpr]] = []
    vals: List[_SExpr] = []
    while i < n:
        c = s[i]
        # numbers
        if c.isdigit() or c == '-' and (i + 1 < n) and s[i + 1].isdigit():
            num, i = _SExpr_parse_number(s, i)
            vals.append(num)
        # quoted strings
        elif c == '"':
            string, i = _SExpr_parse_string(s, i)
            vals.append(string)
        # start new list
        elif c == '(':
            stack.append(vals)
            vals = []
            i += 1
        # end list
        elif c == ')':
            if len(vals) == 3 and vals[1] == '.':
                data = (vals[0], vals[2])  # simplify dotted pair
            else:
                data = vals
            if len(stack) == 0:
                break
            else:
                stack[-1].append(data)
                vals = stack.pop()
            i += 1
        # ignore whitespace
        elif c.isspace():
            i += 1
        # any other symbol
        else:
            sym, i = _SExpr_parse_symbol(s, i)
            vals.append(sym)

    return SExprResult(data, s[i+1:])


def _SExpr_parse_number(s: str, i: int) -> Tuple[Union[int, float], int]:
    j = i + 1  # start at next character
    while s[j].isdigit():
        j += 1
    c = s[j]

    if c not in '.eE':  # int
        return int(s[i:j]), j

    # float
    if c == '.':
        j += 1
        while s[j].isdigit():
            j += 1
        c = s[j]

    if c in 'eE':
        j += 1
        if s[j] in '+-':
            j += 1
        while s[j].isdigit():
            j += 1

    return float(s[i:j]), j


def _SExpr_parse_string(s: str, i: int) -> Tuple[str, int]:
    j = i + 1
    while s[j] != '"':
        if s[j] == '\\':
            j += 2
        else:
            j += 1
    return _SExpr_unescape_string(s[i+1:j]), j + 1


def _SExpr_parse_symbol(s: str, i: int) -> Tuple[str, int]:
    m = _SExpr_symbol_re.match(s, pos=i)
    if m is None:
        raise ValueError('Invalid S-Expression: ' + s)
    return _SExpr_unescape_symbol(m.group(0)), m.end()


class _SExprParser(object):

    def parse(self, s: str) -> SExprResult:
        return _SExpr_parse(s.lstrip())

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
