
"""
TSQL -- Test Suite Query Language

This module implements a subset of TSQL, namely the 'select' (or
'retrieve') queries for extracting data from test suites. The general
form of a select query is::

    [select] <projection> [from <tables>] [where <condition>]*

For example, the following selects item identifiers that took more
than half a second to parse::

    select i-id from item where total > 500

The `select` string is necessary when querying with the generic
:func:`query` function, but is implied and thus disallowed when using
the :func:`select` function.

The `<projection>` is a list of space-separated field names (e.g.,
`i-id i-input mrs`), or the special string `*` which selects all
columns from the joined tables.

The optional `from` clause provides a list of table names (e.g.,
`item parse result`) that are joined on shared keys. The `from`
clause is required when `*` is used for the projection, but it can
also be used to select columns from non-standard tables (e.g., `i-id
from output`). Alternatively, `delphin.itsdb`-style data specifiers
(see :func:`delphin.itsdb.get_data_specifier`) may be used to specify
the table on the column name (e.g., `item:i-id`).

The `where` clause provide conditions for filtering the list of
results. Conditions are binary operations that take a column or data
specifier on the left side and an integer (e.g., `10`), a date (e.g.,
`2018-10-07`), or a string (e.g., `"sleep"`) on the right side of the
operator. The allowed conditions are:

    ================  ======================================
    Condition         Form
    ================  ======================================
    Regex match       ``<field> ~ "regex"``
    Regex fail        ``<field> !~ "regex"``
    Equality          ``<field> = (integer|date|"string")``
    Inequality        ``<field> != (integer|date|"string")``
    Less-than         ``<field> < (integer|date)``
    Less-or-equal     ``<field> <= (integer|date)``
    Greater-than      ``<field> > (integer|date)``
    Greater-or-equal  ``<field> >= (integer|date)``
    ================  ======================================

Boolean operators can be used to join multiple conditions or for
negation:

    ===========  =====================================
    Operation    Form
    ===========  =====================================
    Disjunction  ``X | Y``, ``X || Y``, or ``X or Y``
    Conjunction  ``X & Y``, ``X && Y``, or ``X and Y``
    Negation     ``!X`` or ``not X``
    ===========  =====================================

Normally, disjunction scopes over conjunction, but parentheses may be
used to group clauses, so the following are equivalent::

    ... where i-id = 10 or i-id = 20 and i-input ~ "[Dd]og"
    ... where i-id = 10 or (i-id = 20 and i-input ~ "[Dd]og")

Multiple `where` clauses may also be used as a conjunction that scopes
over disjunction, so the following are equivalent::

    ... where (i-id = 10 or i-id = 20) and i-input ~ "[Dd]og"
    ... where i-id = 10 or i-id = 20 where i-input ~ "[Dd]og"

This facilitates query construction, where a user may want to apply
additional global constraints by appending new conditions to the query
string.

PyDelphin has several differences to standard TSQL:

* `select *` requires a `from` clause
* `select * from item result` does not also include columns from the
  intervening `parse` table
* `select i-input from result` returns a matching `i-input` for every
  row in `result`, rather than only the unique rows

PyDelphin also adds some features to standard TSQL:

* optional table specifications on columns (e.g., `item:i-id`)
* multiple `where` clauses (as described above)
"""

import operator
import copy
import re

from delphin.exceptions import TSQLSyntaxError
from delphin.util import LookaheadIterator, parse_datetime
from delphin import itsdb


### QUERY INSPECTION ##########################################################

def inspect_query(query):
    """
    Parse *query* and return the interpreted query object.

    Example:
        >>> from delphin import tsql
        >>> from pprint import pprint
        >>> pprint(tsql.inspect_query(
        ...     'select i-input from item where i-id < 100'))
        {'querytype': 'select',
         'projection': ['i-input'],
         'tables': ['item'],
         'where': ('<', ('i-id', 100))}
    """
    return _parse_query(query)

### QUERY PROCESSING ##########################################################

def query(query, ts, **kwargs):
    """
    Perform *query* on the testsuite *ts*.

    Note: currently only 'select' queries are supported.

    Args:
        query (str): TSQL query string
        ts (:class:`delphin.itsdb.TestSuite`): testsuite to query over
        kwargs: keyword arguments passed to the more specific query
            function (e.g., :func:`select`)
    Example:
        >>> list(tsql.query('select i-id where i-length < 4', ts))
        [[142], [1061]]
    """
    queryobj = _parse_query(query)

    if queryobj['querytype'] in ('select', 'retrieve'):
        return _select(
            queryobj['projection'],
            queryobj['tables'],
            queryobj['where'],
            ts,
            mode=kwargs.get('mode', 'list'),
            cast=kwargs.get('cast', True))
    else:
        # not really a syntax error; replace with TSQLError or something
        # when the proper exception class exists
        raise TSQLSyntaxError(queryobj['querytype'] +
                              ' queries are not supported')


def select(query, ts, mode='list', cast=True):
    """
    Perform the TSQL selection query *query* on testsuite *ts*.

    Note: The `select`/`retrieve` part of the query is not included.

    Args:
        query (str): TSQL select query
        ts (:class:`delphin.itsdb.TestSuite`): testsuite to query over
        mode (str): how to return the results (see
            :func:`delphin.itsdb.select_rows` for more information
            about the *mode* parameter; default: `list`)
        cast (bool): if `True`, values will be cast to their datatype
            according to the testsuite's relations (default: `True`)
    Example:
        >>> list(tsql.select('i-id where i-length < 4', ts))
        [[142], [1061]]
    """
    queryobj = _parse_select(query)
    return _select(
        queryobj['projection'],
        queryobj['tables'],
        queryobj['where'],
        ts,
        mode,
        cast)


def _select(projection, tables, condition, ts, mode, cast):
    table = _select_from(tables, None, ts)
    table = _select_projection(projection, table, ts)
    table = _select_where(condition, table, ts)

    # finally select the relevant columns from the joined table
    if projection == '*':
        if len(tables) == 1:
            projection = [f.name for f in ts.relations[tables[0]]]
        else:
            projection = []
            for t in tables:
                projection.extend(t + ':' + f.name
                                  for f in ts.relations[t])
    return itsdb.select_rows(projection, table, mode=mode, cast=cast)


def _select_from(tables, table, ts):
    joined = set([] if table is None else table.name.split('+'))
    for tab in tables:
        if tab not in joined:
            joined.add(tab)
            table = _transitive_join(table, ts[tab], ts, 'inner')
    return table


def _select_projection(projection, table, ts):
    if projection != '*':
        for p in projection:
            table = _join_if_missing(table, p, ts, 'inner')
    return table


def _select_where(condition, table, ts):
    keys = table.fields.keys()
    ids = set()
    if condition is not None:
        func, fields = _process_condition(condition)
        # join tables in the condition for filtering
        tmptable = table
        for field in fields:
            tmptable = _join_if_missing(tmptable, field, ts, 'left')
        # filter the rows and store the keys only
        for record in filter(func, tmptable):
            idtuple = tuple(record[key] for key in keys)
            ids.add(idtuple)
        # check if a matching idtuple was retained
        def meta_condition(rec):
            return tuple(rec[key] for key in keys) in ids
        table[:] = filter(meta_condition, table)
    return table


_operator_functions = {'==': operator.eq,
                       '!=': operator.ne,
                       '<': operator.lt,
                       '<=': operator.le,
                       '>': operator.gt,
                       '>=': operator.ge}


def _process_condition(condition):
    # conditions are something like:
    #  ('==', ('i-id', 11))
    op, body = condition
    if op in ('and', 'or'):
        fields = []
        conditions = []
        for cond in body:
            _func, _fields = _process_condition(cond)
            fields.extend(_fields)
            conditions.append(_func)
        _func = all if op == 'and' else any
        def func(row):
            return _func(cond(row) for cond in conditions)
    elif op == 'not':
        nfunc, fields = _process_condition(body)
        func = lambda row, nfunc=nfunc: not nfunc(row)
    elif op == '~':
        fields = [body[0]]
        func = lambda row, body=body: re.search(body[1], row[body[0]])
    elif op == '!~':
        fields = [body[0]]
        func = lambda row, body=body: not re.search(body[1], row[body[0]])
    else:
        fields = [body[0]]
        compare = _operator_functions[op]
        def func(row):
            return compare(row.get(body[0], cast=True), body[1])
    return func, fields


def _join_if_missing(table, col, ts, how):
    tab, _, column = col.rpartition(':')
    if not tab:
        # Just get the first table defining the column. This
        # makes the assumption that relations are ordered and
        # that the first one is 'primary'
        tab = ts.relations.find(column)[0]
    if table is None or column not in table.fields:
        table = _transitive_join(table, ts[tab], ts, how)
    return table


def _transitive_join(tab1, tab2, ts, how):
    if tab1 is None:
        table = copy.copy(tab2)
    else:
        table = tab1
        # the tables may not be directly joinable but could be
        # joinable transitively via a 'path' of table joins
        path = ts.relations.path(tab1.name, tab2.name)
        for intervening, pivot in path:
            table = itsdb.join(table, ts[intervening], on=pivot, how=how)
    return table


### QUERY PARSING #############################################################

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


def _parse_query(query):
    querytype, _, querybody = query.lstrip().partition(' ')
    querytype = querytype.lower()
    if querytype in ('select', 'retrieve'):
        result = _parse_select(querybody)
    else:
        raise TSQLSyntaxError("'{}' queries are not supported"
                              .format(querytype), lineno=1)

    return result


def _parse_select(query):
    tokens = LookaheadIterator(_lex(query))
    _, token, lineno = tokens.peek()  # maybe used in error below

    projection = _parse_select_projection(tokens)
    tables = _parse_select_from(tokens)
    condition = _parse_select_where(tokens)

    if projection == '*' and not tables:
        raise TSQLSyntaxError(
            "'select *' requires a 'from' clause",
            lineno=lineno, text=token)

    # verify we're at the end of the query (the '.' may have been
    # added in _lex())
    gid, token, lineno = tokens.next()
    _expect(gid == 1 and token == '.', token, lineno, "'.'")

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
    tables = []
    if tokens.peek()[1] == 'from':
        tokens.next()
        while tokens.peek()[0] == 10:
            _, table, _ = tokens.next()
            tables.append(table)
    return tables


def _parse_select_where(tokens):
    conditions = []
    while tokens.peek()[1] == 'where':
        tokens.next()
        conditions.append(_parse_condition_disjunction(tokens))
    if len(conditions) == 1:
        condition = conditions[0]
    elif len(conditions) > 1:
        condition = ('and', conditions)
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
        return ('or', tuple(conds))


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
        return ('and', tuple(conds))


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
    return tuple(cond)


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
            value = parse_datetime(value)
        elif gid == 9:
            value = int(value)
        return (op, (column, value))


def _expect(expected, token, lineno, msg):
    msg = 'expected ' + msg
    if not expected:
        raise TSQLSyntaxError(msg, lineno=lineno, text=token)
