import re
import warnings
from pathlib import Path
from typing import Generator, Union

from delphin import util
from delphin.tdl._exceptions import TDLError, TDLSyntaxError, TDLWarning
from delphin.tdl._model import (
    AVM,
    EMPTY_LIST_TYPE,
    LIST_TYPE,
    BlockComment,
    Conjunction,
    ConsList,
    Coreference,
    DiffList,
    FileInclude,
    InstanceEnvironment,
    LetterSet,
    LexicalRuleDefinition,
    LineComment,
    Regex,
    String,
    Term,
    TypeAddendum,
    TypeDefinition,
    TypeEnvironment,
    TypeIdentifier,
    WildCard,
    _Environment,
    _MorphSet,
)

# NOTE: be careful rearranging subpatterns in _tdl_lex_re; some must
#       appear before others, e.g., """ before ", <! before <, etc.,
#       to prevent short-circuiting from blocking the larger patterns
# NOTE: some patterns only match the beginning (e.g., """, #|, etc.)
#       as they require separate handling for proper lexing
# NOTE: only use one capture group () for each pattern; if grouping
#       inside the pattern is necessary, use non-capture groups (?:)
_identifier_pattern = r'''[^\s!"#$%&'(),.\/:;<=>[\]^|]+'''
_tdl_lex_re = re.compile(
    r'''# regex-pattern                gid  description
    (""")                            #   1  start of multiline docstring
    |(\#\|)                          #   2  start of multiline comment
    |;([^\n]*)                       #   3  single-line comment
    |"([^"\\]*(?:\\.[^"\\]*)*)"      #   4  double-quoted "strings"
    |'({identifier})                 #   5  single-quoted 'symbols
    |\^([^$\\]*(?:\\.|[^$\\]*)*)\$   #   6  regular expression
    |(:[=<])                         #   7  type def operator
    |(:\+)                           #   8  type addendum operator
    |(\.\.\.)                        #   9  list ellipsis
    |(\.)                            #  10  dot operator
    |(&)                             #  11  conjunction operator
    |(,)                             #  12  list delimiter
    |(\[)                            #  13  AVM open
    |(<!)                            #  14  diff list open
    |(<)                             #  15  cons list open
    |(\])                            #  16  AVM close
    |(!>)                            #  17  diff list close
    |(>)                             #  18  cons list close
    |\#({identifier})                #  19  coreference
    |%\s*\((.*)\)                    #  20  letter-set or wild-card
    |%(prefix|suffix)                #  21  start of affixing pattern
    |\(([^ ]+\s+(?:[^ )\\]|\\.)+)\)  #  22  affix subpattern
    |(\/)                            #  23  defaults (currently unused)
    |({identifier})                  #  24  identifiers and symbols
    |(:begin)                        #  25  start a :type or :instance block
    |(:end)                          #  26  end a :type or :instance block
    |(:type|:instance)               #  27  environment type
    |(:status)                       #  28  instance status
    |(:include)                      #  29  file inclusion
    |([^\s])                         #  30  unexpected
    '''.format(identifier=_identifier_pattern),
    flags=re.VERBOSE | re.UNICODE)


# Parsing helper functions

def _is_comment(data):
    """helper function for filtering out comments"""
    return 2 <= data[0] <= 3


def _peek(tokens, n=0):
    """peek and drop comments"""
    return tokens.peek(n=n, skip=_is_comment, drop=True)


def _next(tokens):
    """pop the next token, dropping comments"""
    return tokens.next(skip=_is_comment)


def _shift(tokens):
    """pop the next token, then peek the gid of the following"""
    after = tokens.peek(n=1, skip=_is_comment, drop=True)
    tok = tokens._buffer.popleft()
    return tok[0], tok[1], tok[2], after[0]


def _lex(stream):
    """
    Lex the input stream according to _tdl_lex_re.

    Yields
        (gid, token, line_number)
    """
    lines = enumerate(stream, 1)
    line_no = pos = 0
    try:
        while True:
            if pos == 0:
                line_no, line = next(lines)
            matches = _tdl_lex_re.finditer(line, pos)
            pos = 0  # reset; only used for multiline patterns
            for m in matches:
                gid = m.lastindex
                if gid <= 2:  # potentially multiline patterns
                    if gid == 1:  # docstring
                        s, start_line_no, line_no, line, pos = _bounded(
                            '"""', '"""', line, m.end(), line_no, lines)
                    elif gid == 2:  # comment
                        s, start_line_no, line_no, line, pos = _bounded(
                            '#|', '|#', line, m.end(), line_no, lines)
                    yield (gid, s, line_no)
                    break
                elif gid == 30:
                    raise TDLSyntaxError(
                        lineno=line_no,
                        offset=m.start(),
                        text=line)
                else:
                    # token = None
                    # if not (6 < gid < 20):
                    #     token = m.group(gid)
                    token = m.group(gid)
                    yield (gid, token, line_no)
    except StopIteration:
        pass


def _bounded(p1, p2, line, pos, line_no, lines):
    """Collect the contents of a bounded multiline string"""
    substrings = []
    start_line_no = line_no
    end = pos
    while not line.startswith(p2, end):
        if line[end] == '\\':
            end += 2
        else:
            end += 1
        if end >= len(line):
            substrings.append(line[pos:])
            try:
                line_no, line = next(lines)
            except StopIteration:
                pattern = 'docstring' if p1 == '"""' else 'block comment'
                raise TDLSyntaxError(
                    f'unterminated {pattern}',
                    lineno=start_line_no
                ) from None
            pos = end = 0
    substrings.append(line[pos:end])
    end += len(p2)
    return ''.join(substrings), start_line_no, line_no, line, end


# Parsing functions

ParseEvent = tuple[
    str,
    Union[str, TypeDefinition, _MorphSet, _Environment, FileInclude],
    int
]


def iterparse(path: util.PathLike,
              encoding: str = 'utf-8') -> Generator[ParseEvent, None, None]:
    """
    Parse the TDL file at *path* and iteratively yield parse events.

    Parse events are `(event, object, lineno)` tuples, where `event`
    is a string (`"TypeDefinition"`, `"TypeAddendum"`,
    `"LexicalRuleDefinition"`, `"LetterSet"`, `"WildCard"`,
    `"BeginEnvironment"`, `"EndEnvironment"`, `"FileInclude"`,
    `"LineComment"`, or `"BlockComment"`), `object` is the interpreted
    TDL object, and `lineno` is the line number where the entity began
    in *path*.

    Args:
        path: path to a TDL file
        encoding (str): the encoding of the file (default: `"utf-8"`)
    Yields:
        `(event, object, lineno)` tuples
    Example:
        >>> lex = {}
        >>> for event, obj, lineno in tdl.iterparse('erg/lexicon.tdl'):
        ...     if event == 'TypeDefinition':
        ...         lex[obj.identifier] = obj
        ...
        >>> lex['eucalyptus_n1']['SYNSEM.LKEYS.KEYREL.PRED']
        <String object (_eucalyptus_n_1_rel) at 140625748595960>
    """
    path = Path(path).expanduser()
    with path.open(encoding=encoding) as fh:
        yield from _parse(fh, path)


def _parse(f, path):
    tokens = util.LookaheadIterator(_lex(f))
    try:
        yield from _parse_tdl(tokens, path)
    except TDLSyntaxError as ex:
        ex.filename = str(path)
        raise
    except RecursionError as exc:
        raise TDLError(
            "excessively recursive TDL structure (perhaps there's "
            "a very long list); try increasing Python's recursion "
            "limit with sys.setrecursionlimit(n)"
        ) from exc


def _parse_tdl(tokens, path):
    environment = None
    envstack = []
    try:
        line_no = 1
        while True:
            obj = None
            try:
                gid, token, line_no = tokens.next()
            except StopIteration:  # normal EOF
                break
            if gid == 2:
                yield ('BlockComment', BlockComment(token), line_no)
            elif gid == 3:
                yield ('LineComment', LineComment(token), line_no)
            elif gid == 20:
                obj = _parse_letterset(token, line_no)
                yield (obj.__class__.__name__, obj, line_no)
            elif gid == 24:
                obj = _parse_tdl_definition(token, tokens)
                yield (obj.__class__.__name__, obj, line_no)
            elif gid == 25:
                envstack.append(environment)
                _environment = _parse_tdl_begin_environment(tokens)
                if environment is not None:
                    environment.entries.append(_environment)
                environment = _environment
                yield ('BeginEnvironment', environment, line_no)
            elif gid == 26:
                _parse_tdl_end_environment(tokens, environment)
                yield ('EndEnvironment', environment, line_no)
                environment = envstack.pop()
            elif gid == 29:
                obj = _parse_tdl_include(tokens, path.parent)
                yield ('FileInclude', obj, line_no)
            else:
                raise TDLSyntaxError(
                    f'unexpected token: {token}',
                    lineno=line_no)
            if environment is not None and obj is not None:
                environment.entries.append(obj)
    except StopIteration:
        raise TDLSyntaxError('unexpected end of input.') from None


def _parse_tdl_definition(identifier, tokens):
    gid, token, line_no, nextgid = _shift(tokens)

    if gid == 7 and nextgid == 21:  # lex rule with affixes
        atype, pats = _parse_tdl_affixes(tokens)
        conjunction, nextgid = _parse_tdl_conjunction(tokens)
        obj = LexicalRuleDefinition(
            identifier, atype, pats, conjunction)

    elif gid == 7:
        if token == ':<':
            warnings.warn(
                'Subtype operator :< encountered at line {} for '
                '{}; Continuing as if it were the := operator.'
                .format(line_no, identifier),
                TDLWarning,
                stacklevel=2,
            )
        conjunction, nextgid = _parse_tdl_conjunction(tokens)
        if isinstance(conjunction, Term):
            conjunction = Conjunction([conjunction])
        if len(conjunction.types()) == 0:
            raise TDLSyntaxError(
                f'no supertypes defined on {identifier}',
                lineno=line_no)
        obj = TypeDefinition(identifier, conjunction)

    elif gid == 8:
        if nextgid == 1 and _peek(tokens, n=1)[0] == 10:
            # docstring will be handled after the if-block
            conjunction = Conjunction()
        else:
            conjunction, nextgid = _parse_tdl_conjunction(tokens)
        obj = TypeAddendum(identifier, conjunction)

    else:
        raise TDLSyntaxError("expected: := or :+",
                             lineno=line_no)

    if nextgid == 1:  # pre-dot docstring
        _, token, _, nextgid = _shift(tokens)
        obj.docstring = token
    if nextgid != 10:  # . dot
        raise TDLSyntaxError('expected: .', lineno=line_no)
    tokens.next()

    return obj


def _parse_letterset(token, line_no):
    end = r'\s+((?:[^) \\]|\\.)+)\)'
    m = re.match(r'\s*letter-set\s*\((!.)' + end, token)
    if m is not None:
        chars = re.sub(r'\\(.)', r'\1', m.group(2))
        return LetterSet(m.group(1), chars)
    else:
        m = re.match(r'\s*wild-card\s*\((\?.)' + end, token)
        if m is not None:
            chars = re.sub(r'\\(.)', r'\1', m.group(2))
            return WildCard(m.group(1), chars)
    # if execution reached here there was a problems
    raise TDLSyntaxError(
        f'invalid letter-set or wild-card: {token}',
        lineno=line_no)


def _parse_tdl_affixes(tokens):
    gid, token, line_no, nextgid = _shift(tokens)
    assert gid == 21
    affixtype = token
    affixes = []
    while nextgid == 22:
        gid, token, line_no, nextgid = _shift(tokens)
        match, replacement = token.split(None, 1)
        affixes.append((match, replacement))
    return affixtype, affixes


def _parse_tdl_conjunction(tokens):
    terms = []
    while True:
        term, nextgid = _parse_tdl_term(tokens)
        terms.append(term)
        if nextgid == 11:  # & operator
            tokens.next()
        else:
            break
    if len(terms) == 1:
        return terms[0], nextgid
    else:
        return Conjunction(terms), nextgid


def _parse_tdl_term(tokens):
    doc = None

    gid, token, line_no, nextgid = _shift(tokens)

    # docstrings are not part of the conjunction so check separately
    if gid == 1:  # docstring
        doc = token
        gid, token, line_no, nextgid = _shift(tokens)

    if gid == 4:  # string
        term = String(token, docstring=doc)
    elif gid == 5:  # quoted symbol
        warnings.warn(
            f'Single-quoted symbol encountered at line {line_no}; '
            'Continuing as if it were a regular symbol.',
            TDLWarning,
            stacklevel=2,
        )
        term = TypeIdentifier(token, docstring=doc)
    elif gid == 6:  # regex
        term = Regex(token, docstring=doc)
    elif gid == 13:  # AVM open
        featvals, nextgid = _parse_tdl_feature_structure(tokens)
        term = AVM(featvals, docstring=doc)
    elif gid == 14:  # diff list open
        values, _, nextgid = _parse_tdl_list(tokens, break_gid=17)
        term = DiffList(values, docstring=doc)
    elif gid == 15:  # cons list open
        values, end, nextgid = _parse_tdl_list(tokens, break_gid=18)
        term = ConsList(values, end=end, docstring=doc)
    elif gid == 19:  # coreference
        term = Coreference(token, docstring=doc)
    elif gid == 24:  # identifier
        term = TypeIdentifier(token, docstring=doc)
    else:
        raise TDLSyntaxError('expected a TDL conjunction term.',
                             lineno=line_no, text=token)
    return term, nextgid


def _parse_tdl_feature_structure(tokens):
    feats = []
    gid, token, line_no, nextgid = _shift(tokens)
    if gid != 16:  # ] feature structure terminator
        while True:
            if gid != 24:  # identifier (attribute name)
                raise TDLSyntaxError('Expected a feature name',
                                     lineno=line_no, text=token)
            path = [token]
            while nextgid == 10:  # . dot
                tokens.next()
                gid, token, line_no, nextgid = _shift(tokens)
                assert gid == 24
                path.append(token)
            attr = '.'.join(path)

            conjunction, nextgid = _parse_tdl_conjunction(tokens)
            feats.append((attr, conjunction))

            if nextgid == 12:  # , list delimiter
                tokens.next()
                gid, token, line_no, nextgid = _shift(tokens)
            elif nextgid == 16:
                gid, _, _, nextgid = _shift(tokens)
                break
            else:
                raise TDLSyntaxError('expected: , or ]',
                                     lineno=line_no)

    assert gid == 16

    return feats, nextgid


def _parse_tdl_list(tokens, break_gid):
    values = []
    end = None
    nextgid = _peek(tokens)[0]
    if nextgid == break_gid:
        _, _, _, nextgid = _shift(tokens)
    else:
        while True:
            if nextgid == 9:  # ... ellipsis
                _, _, _, nextgid = _shift(tokens)
                end = LIST_TYPE
                break
            else:
                term, nextgid = _parse_tdl_conjunction(tokens)
                values.append(term)

            if nextgid == 10:  # . dot
                tokens.next()
                end, nextgid = _parse_tdl_conjunction(tokens)
                break
            elif nextgid == break_gid:
                break
            elif nextgid == 12:  # , comma delimiter
                _, _, _, nextgid = _shift(tokens)
            else:
                raise TDLSyntaxError('expected: comma or end of list')

        gid, _, line_no, nextgid = _shift(tokens)
        if gid != break_gid:
            raise TDLSyntaxError('expected: end of list',
                                 lineno=line_no)

    if len(values) == 0 and end is None:
        end = EMPTY_LIST_TYPE

    return values, end, nextgid


def _parse_tdl_begin_environment(tokens):
    gid, envtype, lineno = tokens.next()
    if gid != 27:
        raise TDLSyntaxError('expected: :type or :instance',
                             lineno=lineno, text=envtype)
    gid, token, lineno = tokens.next()
    if envtype == ':instance':
        status = envtype[1:]
        if token == ':status':
            status = tokens.next()[1]
            gid, token, lineno = tokens.next()
        elif gid != 10:
            raise TDLSyntaxError('expected: :status or .',
                                 lineno=lineno)
        env = InstanceEnvironment(status)
    else:
        env = TypeEnvironment()
    if gid != 10:
        raise TDLSyntaxError('expected: .', lineno=lineno, text=token)
    return env


def _parse_tdl_end_environment(tokens, env):
    _, envtype, lineno = tokens.next()
    if envtype == ':type' and not isinstance(env, TypeEnvironment):
        raise TDLSyntaxError('expected: :type', lineno=lineno, text=envtype)
    elif envtype == ':instance' and not isinstance(env, InstanceEnvironment):
        raise TDLSyntaxError('expected: :instance',
                             lineno=lineno, text=envtype)
    gid, _, lineno = tokens.next()
    if gid != 10:
        raise TDLSyntaxError('expected: .', lineno=lineno)
    return envtype


def _parse_tdl_include(tokens, basedir):
    gid, value, lineno = tokens.next()
    if gid != 4:
        raise TDLSyntaxError('expected: a quoted filename',
                             lineno=lineno, text=value)
    gid, _, lineno = tokens.next()
    if gid != 10:
        raise TDLSyntaxError('expected: .', lineno=lineno)
    return FileInclude(value, basedir=basedir)
