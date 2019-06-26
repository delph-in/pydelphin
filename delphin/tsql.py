
"""
TSQL -- Test Suite Query Language

.. note::

  This module deals with queries of TSDB databases. For basic,
  low-level access to the databases, see :mod:`delphin.tsdb`. For
  high-level operations and structures on top of the databases, see
  :mod:`delphin.itsdb`.

This module implements a subset of TSQL, namely the 'select' (or
'retrieve') queries for extracting data from test suites. The general
form of a select query is::

    [select] <projection> [from <relations>] [where <condition>]*

For example, the following selects item identifiers that took more
than half a second to parse::

    select i-id from item where total > 500

The `select` string is necessary when querying with the generic
:func:`query` function, but is implied and thus disallowed when using
the :func:`select` function.

The `<projection>` is a list of space-separated field names (e.g.,
`i-id i-input mrs`), or the special string `*` which selects all
columns from the joined relations.

The optional `from` clause provides a list of relation names (e.g.,
`item parse result`) that are joined on shared keys. The `from` clause
is required when `*` is used for the projection, but it can also be
used to select columns from non-standard relations (e.g., `i-id from
output`). Alternatively, `delphin.itsdb`-style data specifiers (see
:func:`delphin.itsdb.get_data_specifier`) may be used to specify the
relation on the column name (e.g., `item.i-id`).

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
  intervening `parse` relation
* `select i-input from result` returns a matching `i-input` for every
  row in `result`, rather than only the unique rows

PyDelphin also adds some features to standard TSQL:

* qualified column names (e.g., `item.i-id`)
* multiple `where` clauses (as described above)
"""

from typing import (
    List, Tuple, Mapping, Optional, Union, Any,
    Iterator, Iterable, Callable)
import operator
import re

from delphin.exceptions import PyDelphinException, PyDelphinSyntaxError
from delphin import util
from delphin import tsdb

# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401


# CUSTOM EXCEPTIONS ###########################################################

class TSQLError(PyDelphinException):
    """Raised on invalid TSQL operations."""


class TSQLSyntaxError(PyDelphinSyntaxError):
    """Raised when encountering an invalid TSQL query."""


# LOCAL TYPES #################################################################

Comparison = Tuple[str, Tuple[str, tsdb.Value]]
# the following should be recursive:
#     Boolean = Tuple[str, Tuple[Boolean, ...]]
# but use Any until the type checker supports recursive types.
# see: https://github.com/python/mypy/issues/731
Boolean = Tuple[str, Tuple[Any, ...]]
Condition = Union[Comparison, Boolean]
# This matches the signature for itsdb.Row; tsdb does not actually
# have a Record class, only a type description.
_RecordType = Callable[[tsdb.Fields, tsdb.Record, Optional[tsdb.FieldIndex]],
                       tsdb.Record]
_Names = Tuple[str, ...]


def _default_record_class(
        fields: tsdb.Fields,
        data: tsdb.Record,
        field_index: tsdb.FieldIndex) -> tsdb.Record:
    return tuple(data)


class Selection(tsdb.Relation):
    def __init__(self,
                 record_class: _RecordType = None) -> None:
        """
        The results of a 'select' query.
        """
        self.fields = []  # type: tsdb.Fields
        self._field_index = {}  # type: tsdb.FieldIndex
        self.data = []  # type: tsdb.Relation
        self.projection = None
        if record_class is None:
            record_class = _default_record_class
        self.record_class = record_class
        self.joined = set()

    def __iter__(self) -> Iterator[tsdb.Record]:
        if self.projection is None:
            return self.select()
        else:
            return self.select(*self.projection)

    def select(self, *names: str) -> Iterator[tsdb.Record]:
        if not names:
            indices = list(range(len(self.fields)))
        else:
            indices = [self._field_index[name] for name in names]
        fields = [self.fields[idx] for idx in indices]
        index = tsdb.make_field_index(fields)
        cls = self.record_class
        for row in self.data:
            data = tuple(row[idx] for idx in indices)
            yield cls(fields, data, field_index=index)


# QUERY INSPECTION ############################################################

def inspect_query(querystring: str) -> dict:
    """
    Parse *querystring* and return the interpreted query dictionary.

    Example:
        >>> from delphin import tsql
        >>> from pprint import pprint
        >>> pprint(tsql.inspect_query(
        ...     'select i-input from item where i-id < 100'))
        {'type': 'select',
         'projection': ['i-input'],
         'relations': ['item'],
         'condition': ('<', ('i-id', 100))}
    """
    return _parse_query(querystring)


# QUERY PROCESSING ############################################################

def query(querystring: str,
          db: tsdb.Database,
          **kwargs):
    """
    Perform query *querystring* on the testsuite *ts*.

    Note: currently only 'select' queries are supported.

    Args:
        querystring (str): TSQL query string
        ts (:class:`delphin.itsdb.TestSuite`): testsuite to query over
        kwargs: keyword arguments passed to the more specific query
            function (e.g., :func:`select`)
    Example:
        >>> list(tsql.query('select i-id where i-length < 4', ts))
        [[142], [1061]]
    """
    queryobj = _parse_query(querystring)

    if queryobj['type'] in ('select', 'retrieve'):
        return _select(
            queryobj['projection'],
            queryobj['relations'],
            queryobj['condition'],
            db,
            record_class=kwargs.get('record_class', None))
    else:
        # not really a syntax error; replace with TSQLError or something
        # when the proper exception class exists
        raise TSQLSyntaxError(queryobj['type'] + ' queries are not supported',
                              text=querystring)


def select(querystring: str,
           db: tsdb.Database,
           record_class: _RecordType = None) -> Selection:
    """
    Perform the TSQL selection query *querystring* on testsuite *ts*.

    Note: The `select`/`retrieve` part of the query is not included.

    Args:
        querystring: TSQL select query
        db: TSDB database to query over
    Example:
        >>> list(tsql.select('i-id where i-length < 4', ts))
        [[142], [1061]]
    """
    queryobj = _parse_select(querystring)
    return _select(
        queryobj['projection'],
        queryobj['relations'],
        queryobj['condition'],
        db,
        record_class=record_class)


def _select(projection: List[str],
            relations: List[str],
            condition: Optional[Condition],
            db: tsdb.Database,
            record_class: _RecordType) -> Selection:

    plan = _make_execution_plan(projection, relations, condition, db)
    selection = Selection(record_class=record_class)

    for name, colnames in plan['joins']:
        relation = db[name]
        fields = list(map(relation.get_field, colnames))
        _join(selection, relation, fields, 'inner')

    selection.data = list(filter(plan['condition'], selection.data))
    selection.projection = plan['projection']
    return selection


def _make_execution_plan(
        projection: List[str],
        relations: List[str],
        condition: Optional[Condition],
        db: tsdb.Database) -> dict:
    """Make a plan for all relations to join and columns to keep."""
    schema_map = _make_schema_map(db, relations)
    resolve_qname = _make_qname_resolver(schema_map)

    if projection == ['*']:
        projection = _project_all(relations, db)
    else:
        projection = [resolve_qname(name) for name in projection]

    if condition:
        cond_func, cond_fields = _process_condition(condition,
                                                    resolve_qname)
    else:
        cond_func, cond_fields = None, ()

    joins = _plan_joins(projection, cond_fields, relations, db)

    return {'projection': projection,
            'joins': joins,
            'condition': cond_func}


def _project_all(relations: List[str], db: tsdb.Database) -> List[str]:
    projection = []
    keys_added = set()
    for name in relations:
        for field in db.schema[name]:
            qname = '{}.{}'.format(name, field.name)
            # only include same keys once
            if not field.is_key:
                projection.append(qname)
            elif field.name not in keys_added:
                projection.append(qname)
                keys_added.add(field.name)
    return projection


def _make_schema_map(
        db: tsdb.Database,
        relations: List[str]) -> Mapping[str, List[str]]:
    """Return an inverse mapping from field names to relations."""
    schema_map = {}
    for relname, fields in db.schema.items():
        for field in fields:
            schema_map.setdefault(field.name, []).append(relname)
    # prefer those appearing in specified relations
    for colname in schema_map:
        schema_map[colname] = sorted(schema_map[colname],
                                     key=relations.__contains__,
                                     reverse=True)
    return schema_map


def _make_qname_resolver(schema_map):
    """
    Return a function that turns column names into qualified names.

    For example, `i-input` becomes `item.i-input`.
    """

    def resolve(colname: str) -> str:
        rel, _, col = colname.rpartition('.')
        if rel:
            qname = colname
        elif col in schema_map:
            qname = '{}.{}'.format(schema_map[col][0], col)
        else:
            raise TSQLError('undefined column: {}'.format(colname))
        return qname

    return resolve


def _plan_joins(projection, condition_fields, relations, db):
    """
    Calculate the relations and columns needed for the query.
    """
    joinmap = {}
    added = set()
    relset = set(relations)
    for qname in projection + list(condition_fields):
        if qname not in added:
            rel, _, col = qname.rpartition('.')
            relset.add(rel)
            joinmap.setdefault(rel, []).append(col)
            added.add(qname)
    # add necessary relations to span all requested relations
    keymap = _make_keymap(db)
    relset.update(_pivot_relations(relset, keymap, db))
    # always add keys
    for relation in relset:
        for field in db.schema[relation]:
            if field.is_key:
                qname = '{}.{}'.format(relation, field.name)
                if qname not in added:
                    joinmap.setdefault(relation, []).append(field.name)
    # finally ensure joins occur in a valid order
    joined_keys = set()
    joins = []
    while joinmap:
        changed = False
        for rel in list(joinmap):
            if not joins or joined_keys.intersection(joinmap[rel]):
                joins.append((rel, joinmap.pop(rel)))
                joined_keys.update(keymap[rel])
                changed = True
                break
        if not changed:
            raise TSQLError('infinite loop detected!')

    return joins


def _make_keymap(db):
    keymap = {}
    for rel, fields in db.schema.items():
        keys = [field.name for field in db.schema[rel] if field.is_key]
        keymap[rel] = keys
    return keymap


def _pivot_relations(relset, keymap, db):
    """
    Search to find a relation that can join two disjoint relations.

    Note: If disjoint relation sets cannot be conjoined with a single
        other relation, a TSQLError is raised.
    """
    edges = []
    nodes = set()

    def add_edges(keys):
        for i in range(len(keys) - 1):
            for j in range(i + 1, len(keys)):
                edges.append((keys[i], keys[j]))

    for rel in relset:
        keys = keymap[rel]
        nodes.update(keys)
        add_edges(keys)

    pivots = set()
    components = util._connected_components(nodes, edges)
    while len(components) > 1:
        improved = False
        for rel, keys in keymap.items():
            if rel not in relset.union(pivots) and len(keys) > 1:
                if sum(1 if c.intersection(keys) else 0
                       for c in components) > 1:
                    nodes.update(keys)
                    add_edges(keys)
                    pivots.add(rel)
                    improved = True
                    break
        if not improved:
            raise TSQLError('could not find relation to join: {}'
                            .format(', '.join(sorted(relset))))
        components = util._connected_components(nodes, edges)

    return pivots


_operator_functions = {'==': operator.eq,
                       '!=': operator.ne,
                       '<': operator.lt,
                       '<=': operator.le,
                       '>': operator.gt,
                       '>=': operator.ge}


def _process_condition(
        condition: Condition,
        resolve_qname: Callable[[str], str]) -> Tuple[Condition, _Names]:
    # conditions are something like:
    #  ('==', ('i-id', 11))
    op, body = condition
    if op in ('and', 'or'):
        fieldset = set()
        conditions = []
        for cond in body:
            _func, _fields = _process_condition(cond, resolve_qname)
            fieldset.update(_fields)
            conditions.append(_func)
        fields = tuple(sorted(fieldset))
        _func = all if op == 'and' else any

        def func(row):
            return _func(cond(row) for cond in conditions)

    elif op == 'not':
        nfunc, fields = _process_condition(body, resolve_qname)

        def func(row):
            return not nfunc(row)

    elif op == '~':
        qname = resolve_qname(body[0])
        fields = (qname,)

        def func(row):
            return re.search(body[1], row[qname])

    elif op == '!~':
        qname = resolve_qname(body[0])
        fields = (qname,)

        def func(row):
            return not re.search(body[1], row[qname])

    else:
        qname = resolve_qname(body[0])
        fields = (qname,)
        compare = _operator_functions[op]

        def func(row):
            return compare(row.get(qname, cast=True), body[1])

    return func, fields


# RELATION JOINS ##############################################################

def _join(selection: Selection,
          relation: tsdb.Relation,
          fields: tsdb.Fields = None,
          how: str = 'inner') -> None:
    """
    Join *fields* from *relation* into *selection*.

    If *fields* is `None`, all fields from *relation* are used. Fields
    in *relation* where :attr:`Field.is_key
    <delphin.tsdb.Field.is_key>` returns `True` are always included.

    If *how* is `"inner"`, then only matched rows persist after
    the join; if *how* is `"left"`, all existing rows are kept and
    those without a match are padded with `None` values.
    """
    if how not in ('inner', 'left'):
        raise TSQLError("only 'inner' and 'left' join methods are allowed")
    if relation.name in selection.joined:
        raise TSQLError('cannot join the same relation twice')

    if not selection.joined:
        _merge_fields(selection, relation.name, fields)
        selection.data = list(relation.select(*[f.name for f in fields]))
    else:
        on = []  # type: List[str, ...]
        if selection is not None:
            on = [f.name for f in fields
                  if f.is_key and f.name in selection._field_index]
        fields = [f for f in fields if f.name not in on]
        cols = [f.name for f in fields]

        if not on:
            raise TSQLError('no shared keys for joining')

        right = {}  # type: Mapping[Tuple[tsdb.Value, ...], tsdb.Record]
        for keys, row in zip(relation.select(*on), relation.select(*cols)):
            right.setdefault(tuple(keys), []).append(tuple(row))

        rfill = tuple([None] * len(fields))
        data = []  # type: List[tsdb.Record]
        for keys, lrow in zip(selection.select(*on), selection):
            keys = tuple(keys)
            if how == 'left' or keys in right:
                data.extend(lrow + rrow
                            for rrow in right.get(keys, [rfill]))

        selection.data = data
        _merge_fields(selection, relation.name, fields)


# def _prepare_fields(
#         fields: tsdb.Fields,
#         selection: Selection,
#         relation: tsdb.Relation) -> Tuple[_Names, tsdb.Fields]:
#     on = []  # type: List[str, ...]
#     if selection is not None:
#         on = [f.name for f in fields
#               if f.is_key and f.name in selection._field_index]

#     # we want to ensure key fields are always included
#     if fields is None:
#         fields = relation.fields
#     else:
#         included = {field.name for field in fields}
#         for field in relation.fields:
#             if field.is_key and field.name not in included:
#                 fields = [field] + fields
#                 included.add(field.name)

#     # but filter out keys used in the join pivot
#     fields = [f for f in fields if f.name not in on]

#     return on, fields


def _merge_fields(selection: Selection,
                  relationname: str,
                  fields: tsdb.Fields) -> None:
    offset = len(selection.fields)
    for i, field in enumerate(fields, offset):
        selection.fields.append(field)
        if field.name not in selection._field_index:
            selection._field_index[field.name] = i
        selection._field_index[relationname + '.' + field.name] = i
    selection.joined.add(relationname)


# QUERY PARSING ###############################################################

_year = r'[0-9]{4}'
_yr = r'(?:[0-9]{2})?[0-9]{2}'
_month = r'(?:[0-9][0-9]?|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)'
_day = r'[0-9]{1,2}'
_time = (r'\s*\({t}:{t}(?::{t})?\)'
         r'|\s+{t}:{t}(?::{t})').format(t=r'[0-9]{2}')
_yyyy_mm_dd = r'{year}-{month}(?:-{day})?(?:{time})?'.format(
    year=_year, month=_month, day=_day, time=_time)
_dd_mm_yy = r'(?:{day}-)?{month}-{year}(?:{time})?'.format(
    year=_yr, month=_month, day=_day, time=_time)
_id = r'[a-zA-Z][-_a-zA-Z0-9]*'
_qid = r'{id}\.{id}'.format(id=_id)  # qualified id: "table.column"

_TSQLLexer = util.Lexer(
    tokens=[
        (r'info|set|retrieve|select|insert', 'QUERY:a query type'),
        (r'from', 'FROM:from'),
        (r'where', 'WHERE:where'),
        (r'report', 'REPORT:report'),
        (r'\*', 'STAR:*'),
        (r'\.', 'DOT:.'),
        (r'==|=|!=|~|!~|<=|<|>=|>', 'OP:a comparison operator'),
        (r'&&|&|and', "AND:'&&', '&', or 'and'"),
        (r'\|\||\||or', "OR:'||', '|', or 'or'"),
        (r'!|not', "NOT:'!' or 'not'"),
        (r'\(', 'LPAREN:('),
        (r'\)', 'RPAREN:)'),
        (r'"([^"\\]*(?:\\.[^"\\]*)*)"', 'DQSTRING:a double-quoted string'),
        (r"'([^'\\]*(?:\\.[^'\\]*)*)'", 'SQSTRING:a single-quoted string'),
        (_yyyy_mm_dd, 'YYYYMMDD:a YYYY-MM-DD date'),
        (_dd_mm_yy, 'DDMMYY: a DD-MM-YY date'),
        (r':today|now', "KWDATE:'now' or ':today'"),
        (r'[+-]?\d+', 'INT:an integer'),
        (_qid, 'QID:a qualified identifier'),
        (_id, 'ID:a simple identifier'),
        (r'[^\s]', 'UNEXPECTED')
    ],
    error_class=TSQLSyntaxError)


_QUERY      = _TSQLLexer.tokentypes.QUERY
_FROM       = _TSQLLexer.tokentypes.FROM
_WHERE      = _TSQLLexer.tokentypes.WHERE
_REPORT     = _TSQLLexer.tokentypes.REPORT
_STAR       = _TSQLLexer.tokentypes.STAR
_DOT        = _TSQLLexer.tokentypes.DOT
_OP         = _TSQLLexer.tokentypes.OP
_AND        = _TSQLLexer.tokentypes.AND
_OR         = _TSQLLexer.tokentypes.OR
_NOT        = _TSQLLexer.tokentypes.NOT
_LPAREN     = _TSQLLexer.tokentypes.LPAREN
_RPAREN     = _TSQLLexer.tokentypes.RPAREN
_DQSTRING   = _TSQLLexer.tokentypes.DQSTRING
_SQSTRING   = _TSQLLexer.tokentypes.SQSTRING
_YYYYMMDD   = _TSQLLexer.tokentypes.YYYYMMDD
_DDMMYY     = _TSQLLexer.tokentypes.DDMMYY
_KWDATE     = _TSQLLexer.tokentypes.KWDATE
_INT        = _TSQLLexer.tokentypes.INT
_QID        = _TSQLLexer.tokentypes.QID
_ID         = _TSQLLexer.tokentypes.ID
_UNEXPECTED = _TSQLLexer.tokentypes.UNEXPECTED


def _parse_query(querystring: str) -> dict:
    querytype, _, querybody = querystring.lstrip().partition(' ')
    querytype = querytype.lower()
    if querytype in ('select', 'retrieve'):
        result = _parse_select(querybody)
    else:
        raise TSQLSyntaxError("'{}' queries are not supported"
                              .format(querytype), lineno=1)

    return result


def _parse_select(querystring: str) -> dict:
    querystring += '.'  # just a sentinel to indicate the end of the query
    lexer = _TSQLLexer.lex(querystring.splitlines())
    projection = _parse_select_projection(lexer)
    relations = _parse_select_from(lexer)
    condition = _parse_select_where(lexer)
    lexer.expect_type(_DOT)

    if projection == ['*'] and not relations:
        raise TSQLSyntaxError(
            "'select *' requires a 'from' clause",
            text=querystring)

    return {'type': 'select',
            'projection': projection,
            'relations': relations,
            'condition': condition}


def _parse_select_projection(lexer: util.Lexer) -> List[str]:
    typ, col_id = lexer.choice_type(_STAR, _QID, _ID)
    projection = []
    if typ in (_QID, _ID):
        while col_id:
            projection.append(col_id)
            col_id = lexer.accept_type(_QID) or lexer.accept_type(_ID)
    else:
        projection.append(col_id)
    return projection


def _parse_select_from(lexer: util.Lexer) -> List[str]:
    relations = []
    if lexer.accept_type(_FROM):
        relation = lexer.expect_type(_ID)
        while relation:
            relations.append(relation)
            relation = lexer.accept_type(_ID)
    return relations


def _parse_select_where(lexer: util.Lexer) -> Optional[Condition]:
    conditions = []  # type: List[Condition]
    while lexer.accept_type(_WHERE):
        conditions.append(_parse_condition_disjunction(lexer))
    condition = None  # type: Optional[Condition]
    if len(conditions) == 1:
        condition = conditions[0]
    elif len(conditions) > 1:
        condition = ('and', tuple(conditions))
    return condition


def _parse_condition_disjunction(lexer: util.Lexer) -> Condition:
    conds = []
    while True:
        conds.append(_parse_condition_conjunction(lexer))

        if not lexer.accept_type(_OR):
            break

    if len(conds) == 0:
        raise TSQLSyntaxError('invalid query')
    elif len(conds) == 1:
        return conds[0]
    else:
        return ('or', tuple(conds))


def _parse_condition_conjunction(lexer: util.Lexer) -> Condition:
    conds = []  # type: List[Condition]
    while True:
        typ, token = lexer.choice_type(_NOT, _LPAREN, _QID, _ID)
        if typ == _NOT:
            conds.append(('not', _parse_condition_disjunction(lexer)))
        elif typ == _LPAREN:
            conds.append(_parse_condition_disjunction(lexer))
            lexer.expect_type(_RPAREN)
        elif typ in (_QID, _ID):
            conds.append(_parse_condition_statement(token, lexer))

        if not lexer.accept_type(_AND):
            break

    if len(conds) == 0:
        raise TSQLSyntaxError('invalid query')
    elif len(conds) == 1:
        return conds[0]
    else:
        return ('and', tuple(conds))


def _parse_condition_statement(column: str, lexer: util.Lexer) -> Comparison:
    op = lexer.expect_type(_OP)
    if op == '=':
        op = '=='  # normalize = to == (I think these are equivalent)

    if op in ('~', '!~'):
        typ, value = lexer.choice_type(_DQSTRING, _SQSTRING)
    elif op in ('<', '<=', '>', '>='):
        typ, value = lexer.choice_type(_INT, _YYYYMMDD, _DDMMYY, _KWDATE)
    else:  # must be == or !=
        typ, value = lexer.choice_type(_INT, _DQSTRING, _SQSTRING,
                                       _YYYYMMDD, _DDMMYY, _KWDATE)

    if typ == _INT:
        value = int(value)
    elif typ in (_YYYYMMDD, _DDMMYY, _KWDATE):
        value = tsdb.cast(':date', value)

    return (op, (column, value))
