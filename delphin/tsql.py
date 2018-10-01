
from datetime import datetime
import re

from delphin.exceptions import TSQLSyntaxError
from delphin.util import LookaheadIterator


def query(query, ts):
    queryobj = _parse_query(LookaheadIterator(_lex(query)))
    return queryobj


def select(query, ts):
    queryobj = _parse_select(LookaheadIterator(_lex(query)))
    return queryobj


_keywords = list(map(re.escape,
                     ('info', 'set', 'retrieve', 'select', 'insert',
                      'from', 'where', 'report', '*', '.')))
_operators = list(map(re.escape,
                      ('==', '=', '!=', '~', '!~', '<=', '<', '>=', '>',
                       '&&', '&', 'and', '||', '|', 'or', '!', 'not')))

_tsql_lex_re = re.compile(
    r'''# regex-pattern                      gid  description
    ({keywords})                           #   1  keywords
    |({operators})                         #   2  operators
    |(\(|\))                               #   3  parentheses
    |"([^"\\]*(?:\\.[^"\\]*)*)"            #   4  double-quoted "strings"
    |'([^'\\]*(?:\\.[^'\\]*)*)'            #   5  single-quoted 'strings'
    |({yyyy}-{m}(?:-{d})?(?:{t}|{tt})?)    #   6  yyyy-mm-dd date
    |((?:{d}-)?{m}-{yy}(?:{t}|{tt})?)      #   7  dd-mm-yy date
    |(:today|now)                          #   8  keyword date
    |([+-]?\d+)                            #   9  integers
    |((?:{id}:)?{id}(?:@(?:{id}:)?{id})*)  #  10  identifier (extended def)
    |([^\s])                               #  11  unexpected
    '''.format(keywords='|'.join(_keywords),
               operators='|'.join(_operators),
               d=r'[0-9]{1,2}',
               m=(r'(?:[0-9]{1,2}|'
                  r'jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)'),
               yy=r'(?:[0-9]{2})?[0-9]{2}',
               yyyy=r'[0-9]{4}',
               t=r'\s*\([0-9]{2}:[0-9]{2}(?::[0-9]{2})?\)',
               tt=r'\s+[0-9]{2}:[0-9]{2}(?::[0-9]{2})',
               id=r'[a-zA-Z][-_a-zA-Z0-9]*'),
    flags=re.VERBOSE|re.IGNORECASE)


def _lex(s):
    """
    Lex the input string according to _tsql_lex_re.

    Yields
        (gid, token, line_number)
    """
    s += '.'  # make sure there's a terminator to know when to stop parsing
    lines = enumerate(s.splitlines(), 1)
    lineno = pos = 0
    try:
        for lineno, line in lines:
            matches = _tsql_lex_re.finditer(line)
            for m in matches:
                gid = m.lastindex
                if gid == 11:
                    raise TSQLSyntaxError('unexpected input',
                                          lineno=lineno,
                                          offset=m.start(),
                                          text=line)
                else:
                    token = m.group(gid)
                    yield (gid, token, lineno)
    except StopIteration:
        pass


def _parse_query(tokens):
    gid, token, lineno = tokens.next()
    _expect(gid == 1 and token in 'info set retrieve select insert'.split(),
            token, lineno, 'a query type')
    if token not in ('retrieve', 'select'):
        raise TSQLSyntaxError("'{}' queries are not supported".format(token),
                              lineno=lineno)
    else:
        result = _parse_select(tokens)

    gid, token, lineno = tokens.next()
    _expect(gid == 2 and token == '.', token, lineno, "'.'")

    return result


def _parse_select(tokens):
    _, token, lineno = tokens.peek()  # maybe used in error below

    projection = _parse_select_projection(tokens)
    tables = _parse_select_from(tokens)
    condition = _parse_select_where(tokens)

    if projection == '*' and tables is None and condition is None:
        raise TSQLSyntaxError(
            "'select *' requires a 'from' or 'where' statement",
            lineno=lineno, text=token)

    return {'querytype': 'select',
            'projection': projection,
            'tables': tables,
            'where': condition}


def _parse_select_projection(tokens):
    gid, token, lineno = tokens.next()
    if token == '*':
        projection = token
    elif gid == 10:
        projection = [token]
        while tokens.peek()[0] == 10:
            _, col, _ = tokens.next()
            projection.append(col)
        projection = _prepare_columns(projection)
    else:
        raise TSQLSyntaxError("expected '*' or column identifiers",
                              lineno=lineno, text=token)
    return projection


def _prepare_columns(cols):
    columns = []
    for col in cols:
        table = ''
        for part in col.split('@'):
            tblname, _, colname = part.rpartition(':')
            if tblname:
                table = tblname + ':'
            columns.append(table + colname)
    return columns


def _parse_select_from(tokens):
    if tokens.peek()[1] == 'from':
        tokens.next()
        tables = []
        while tokens.peek()[0] == 10:
            _, table, _ = tokens.next()
            tables.append(table)
    else:
        tables = None
    return tables


def _parse_select_where(tokens):
    if tokens.peek()[1] == 'where':
        tokens.next()
        condition = _parse_condition_disjunction(tokens)
    else:
        condition = None
    return condition


def _parse_condition_disjunction(tokens):
    conds = []
    while True:
        cond = _parse_condition_conjunction(tokens)
        if cond is not None:
            conds.append(cond)
        if tokens.peek()[1] in ('|', '||', 'or'):
            tokens.next()
            nextgid, nexttoken, nextlineno = tokens.peek()
        else:
            break

    if len(conds) == 0:
        return None
    elif len(conds) == 1:
        return conds[0]
    else:
        return ('or', conds)


def _parse_condition_conjunction(tokens):
    conds = []
    nextgid, nexttoken, nextlineno = tokens.peek()
    while True:
        if nextgid == 2 and nexttoken.lower() in ('!', 'not'):
            cond = _parse_condition_negation(tokens)
        elif nextgid == 3 and nexttoken == '(':
            cond = _parse_condition_group(tokens)
        elif nextgid == 3 and nexttoken == ')':
            break
        elif nextgid == 10:
            cond = _parse_condition_statement(tokens)
        else:
            raise TSQLSyntaxError("expected '!', 'not', '(', or a column name",
                                  lineno=nextlineno, text=nexttoken)
        conds.append(cond)
        if tokens.peek()[1].lower() in ('&', '&&', 'and'):
            tokens.next()
            nextgid, nexttoken, nextlineno = tokens.peek()
        else:
            break

    if len(conds) == 0:
        return None
    elif len(conds) == 1:
        return conds[0]
    else:
        return ('and', conds)


def _parse_condition_negation(tokens):
    gid, token, lineno = tokens.next()
    _expect(gid == 2 and token in ('!', 'not'), token, lineno, "'!' or 'not'")
    cond = _parse_condition_disjunction(tokens)
    return ('not', cond)


def _parse_condition_group(tokens):
    gid, token, lineno = tokens.next()
    _expect(gid == 3 and token == '(', token, lineno, "'('")
    cond = _parse_condition_disjunction(tokens)
    gid, token, lineno = tokens.next()
    _expect(gid == 3 and token == ')', token, lineno, "')'")
    return cond


def _parse_condition_statement(tokens):
    gid, column, lineno = tokens.next()
    _expect(gid == 10, column, lineno, 'a column name')
    gid, op, lineno = tokens.next()
    _expect(gid == 2, op, lineno, 'an operator')
    if op == '=':
        op = '=='  # normalize = to == (I think these are equivalent)
    gid, value, lineno = tokens.next()
    if op in ('~', '!~') and gid not in (4, 5):
        raise TSQLSyntaxError(
            "the '{}' operator is only valid with strings".format(op),
            lineno=lineno, text=op)
    elif op in ('<', '<=', '>', '>=') and gid not in (6, 7, 8, 9):
        raise TSQLSyntaxError(
            "the '{}' operator is only valid with integers and dates"
            .format(op), lineno=lineno, text=op)
    else:
        if gid in (6, 7, 8):
            value = _parse_datetime(value, gid)
        elif gid == 9:
            value = int(value)
        return (op, (column, value))


def _parse_datetime(s, gid):
    month_re = re.compile(r'(jan)|(feb)|(mar)|(apr)|(may)|(jun)|'
                          r'(jul)|(aug)|(sep)|(oct)|(nov)|(dec)',
                          flags=re.IGNORECASE)
    if gid == 6:
        s = re.sub(r'''
            (?P<y>[0-9]{4})
            -(?P<m>[0-9]{1,2}|\w{3})
            (?:-(?P<d>[0-9]{1,2}))?
            (?:\s*\(?
                (?P<H>[0-9]{2}):(?P<M>[0-9]{2})(?::(?P<S>[0-9]{2}))?
            \)?)?''', _date_fix, s, flags=re.VERBOSE)
        dt = datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
    elif gid == 7:
        s = re.sub(r'''
            (?:(?P<d>[0-9]{1,2})-)?
            (?P<m>[0-9]{1,2}|\w{3})
            -(?P<y>[0-9]{2}(?:[0-9]{2})?)
            (?:\s*\(?
                (?P<H>[0-9]{2}):(?P<M>[0-9]{2})(?::(?P<S>[0-9]{2}))?
            \)?)?''', _date_fix, s, flags=re.VERBOSE)
        dt = datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
    else:
        dt = datetime.now()
    return dt


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


def _expect(expected, token, lineno, msg):
    msg = 'expected ' + msg
    if not expected:
        raise TSQLSyntaxError(msg, lineno=lineno, text=token)
