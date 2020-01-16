
"""
TSQL -- Test Suite Query Language
"""

from typing import (
    List, Tuple, Dict, Set, Optional, Union, Any, Type,
    Iterator, Callable, cast as typing_cast)
import operator
import re
from datetime import datetime

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

_Names = List[str]
_Comparison = Tuple[str, Tuple[str, tsdb.Value]]
# the following should be recursive:
#     _Boolean = Tuple[str, Union[_Boolean, List[_Boolean, ...]]]
# but use Any until the type checker supports recursive types.
# see: https://github.com/python/mypy/issues/731
_Boolean = Tuple[str, Any]
_Condition = Union[_Comparison, _Boolean]
_FilterFunction = Callable[[tsdb.Record], bool]

_QNameResolver = Callable[[str], Tuple[str, tsdb.Field]]


class _Record(tsdb.Record):
    """Dummy Record type to mimic the call signature of itsdb.Row."""
    def __new__(cls,
                fields: tsdb.Fields,
                data: tsdb.Record,
                field_index: tsdb.FieldIndex = None):
        return tuple(data)


class Selection(tsdb.Records):
    def __init__(self,
                 record_class: Optional[Type[_Record]] = None) -> None:
        """
        The results of a 'select' query.
        """
        self.fields: List[tsdb.Field] = []
        self._field_index: tsdb.FieldIndex = {}
        self.data: tsdb.Records = []
        self.projection = None
        if record_class is None:
            record_class = _Record
        self.record_class = record_class
        self.joined: Set[str] = set()

    def __iter__(self) -> Iterator[tsdb.Record]:
        if self.projection is None:
            return self.select()
        else:
            return self.select(*self.projection)

    def select(self,
               *names: str,
               cast: bool = False) -> Iterator[tsdb.Record]:
        if not names:
            indices = list(range(len(self.fields)))
        else:
            indices = [self._field_index[name] for name in names]
        fields = [self.fields[idx] for idx in indices]
        index = tsdb.make_field_index(fields)
        cls = self.record_class
        for record in self.data:
            record = getattr(record, 'data', record)  # in case it's a Row
            data = tuple(record[idx] for idx in indices)
            if cast and all(value is None or isinstance(value, str)
                            for value in data):
                data = typing_cast(Tuple[Optional[str], ...], data)
                data = tuple(tsdb.cast(field.datatype, value)
                             for field, value in zip(fields, data))
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
           record_class: Optional[Type[_Record]] = None) -> Selection:
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


def _select(projection: _Names,
            relations: List[str],
            condition: Optional[_Condition],
            db: tsdb.Database,
            record_class: Optional[Type[_Record]]) -> Selection:

    proj, joins, condition = _make_execution_plan(
        projection, relations, condition, db)
    selection = Selection(record_class=record_class)

    for name, columns in joins:
        _join(selection, db, name, columns, 'inner')

    if condition:
        cond = _process_condition_function(condition, selection)
        selection.data = list(filter(cond, selection.data))

    selection.projection = proj
    return selection


def _make_execution_plan(
        projection: _Names,
        relations: List[str],
        condition: Optional[_Condition],
        db: tsdb.Database) -> Tuple:
    """Make a plan for all relations to join and columns to keep."""
    resolve_qname = _make_qname_resolver(db, relations)

    if projection == ['*']:
        projection = _project_all(relations, db)
    else:
        projection = [resolve_qname(name)[0] for name in projection]

    cond_resolved: Optional[_Condition] = None
    cond_fields: _Names = []
    if condition:
        cond_resolved, cond_fields = _process_condition_fields(
            condition, resolve_qname)

    joins = _plan_joins(projection, cond_fields, relations, db)

    return projection, joins, cond_resolved


def _project_all(relations: List[str], db: tsdb.Database) -> List[str]:
    projection = []
    keys_added: Set[str] = set()
    for name in relations:
        for field in db.schema[name]:
            qname = f'{name}.{field.name}'
            # only include same keys once
            if not field.is_key:
                projection.append(qname)
            elif field.name not in keys_added:
                projection.append(qname)
                keys_added.add(field.name)
    return projection


def _make_qname_resolver(
        db: tsdb.Database,
        relations: List[str]) -> _QNameResolver:
    """
    Return a function that turns column names into qualified names.

    For example, `i-input` becomes `item.i-input`.
    """

    index = {rel: tsdb.make_field_index(db.schema[rel]) for rel in db.schema}
    schema_map: Dict[str, List[str]] = {}
    for relname, fields in db.schema.items():
        for field in fields:
            schema_map.setdefault(field.name, []).append(relname)
    # prefer those appearing in specified relations
    for colname in schema_map:
        schema_map[colname] = sorted(schema_map[colname],
                                     key=relations.__contains__,
                                     reverse=True)

    def resolve(colname: str) -> Tuple[str, tsdb.Field]:
        rel, _, col = colname.rpartition('.')
        if rel:
            qname = colname
        elif col in schema_map:
            rel = schema_map[col][0]
            qname = f'{rel}.{col}'
        else:
            raise TSQLError(f'undefined column: {colname}')
        return qname, db.schema[rel][index[rel][col]]

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
                qname = f'{relation}.{field.name}'
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


def _process_condition_fields(
        condition: _Condition,
        resolve_qname: _QNameResolver) -> Tuple[_Condition, _Names]:
    # conditions are something like:
    #  ('==', ('i-id', 11))
    op, body = condition
    if op in ('and', 'or'):
        body = typing_cast(List[_Condition], body)
        fieldset = set()
        conditions = []
        for cond in body:
            _cond, _fields = _process_condition_fields(
                cond, resolve_qname)
            fieldset.update(_fields)
            conditions.append(_cond)
        return (op, conditions), sorted(fieldset)

    elif op == 'not':
        ncond, fields = _process_condition_fields(
            body, resolve_qname)
        return ('not', ncond), fields

    else:
        qname, field = resolve_qname(body[0])

        # check if the condition's type matches the column
        typ = _expected_type(field.datatype)
        if not isinstance(body[1], typ):
            raise TSQLError(
                'type mismatch in condition on {}: {} {} {}'
                .format(qname, typ.__name__, op, type(body[1]).__name__))

        return (op, (qname, body[1])), [qname]


def _expected_type(datatype):
    if datatype == ':string':
        return str
    elif datatype in ':integer':
        return int
    elif datatype in ':float':
        return (int, float)
    elif datatype in ':date':
        return datetime


def _process_condition_function(
        condition: _Condition,
        selection: Selection) -> _FilterFunction:
    field_index = selection._field_index
    fields = selection.fields
    # conditions are something like:
    #  ('==', ('i-id', 11))
    op, body = condition
    if op in ('and', 'or'):
        body = typing_cast(List[_Condition], body)
        conditions = []
        for cond in body:
            _func = _process_condition_function(cond, selection)
            conditions.append(_func)
        _func = all if op == 'and' else any

        def func(row):
            return _func(cond(row) for cond in conditions)

    elif op == 'not':
        nfunc = _process_condition_function(body, selection)

        def func(row):
            return not nfunc(row)

    elif op == '~':

        def func(row):
            index = field_index[body[0]]
            field = fields[index]
            value = tsdb.cast(field.datatype, row[index])
            return value is not None and re.search(body[1], value)

    elif op == '!~':

        def func(row):
            index = field_index[body[0]]
            field = fields[index]
            value = tsdb.cast(field.datatype, row[index])
            return value is None or not re.search(body[1], value)

    else:
        compare = _operator_functions[op]

        def func(row):
            index = field_index[body[0]]
            field = fields[index]
            value = tsdb.cast(field.datatype, row[index])
            return value is not None and compare(value, body[1])

    return func


# RELATION JOINS ##############################################################

def _join(selection: Selection,
          db: tsdb.Database,
          name: str,
          columns: _Names,
          how: str = 'inner') -> None:
    """
    Join *fields* from *relation* into *selection*.

    If *how* is `"inner"`, then only matched rows persist after
    the join; if *how* is `"left"`, all existing rows are kept and
    those without a match are padded with `None` values.
    """
    if how not in ('inner', 'left'):
        raise TSQLError("only 'inner' and 'left' join methods are allowed")
    if name in selection.joined:
        raise TSQLError('cannot join the same relation twice')

    all_fields = db.schema[name]
    field_index = tsdb.make_field_index(all_fields)
    indices = [field_index[col] for col in columns]
    fields = [all_fields[idx] for idx in indices]

    data: List[tsdb.Record] = []
    if not selection.joined:
        _merge_fields(selection, name, [], fields)
        data.extend(db._select_raw(name, columns))
    else:
        on: List[str] = []
        if selection is not None:
            on = [f.name for f in fields
                  if f.is_key and f.name in selection._field_index]
        fields = [f for f in fields if f.name not in on]
        cols = [f.name for f in fields]

        if not on:
            raise TSQLError('no shared keys for joining')

        right: Dict[Tuple[tsdb.Value, ...], List[tsdb.Record]] = {}
        for keys, row in zip(db.select_from(name, on, cast=True),
                             db._select_raw(name, cols)):
            right.setdefault(tuple(keys), []).append(tuple(row))

        rfill = tuple([None] * len(fields))
        for keys, lrow in zip(selection.select(*on, cast=True), selection):
            keys = tuple(keys)
            if how == 'left' or keys in right:
                for rrow in right.get(keys, [rfill]):
                    data.append(tuple(lrow) + tuple(rrow))

        _merge_fields(selection, name, on, fields)

    selection.data = data


def _merge_fields(selection: Selection,
                  relationname: str,
                  on: _Names,
                  fields: tsdb.Fields) -> None:
    offset = len(selection.fields)
    for i, field in enumerate(fields, offset):
        selection.fields.append(field)
        if field.name not in selection._field_index:
            selection._field_index[field.name] = i
        selection._field_index[relationname + '.' + field.name] = i
    # also add qualified names for 'on' fields in case the joins
    # happen in a strange order
    for name in on:
        i = selection._field_index[name]
        selection._field_index[relationname + '.' + name] = i
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
        raise TSQLSyntaxError(f"'{querytype}' queries are not supported",
                              lineno=1)

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


def _parse_select_projection(lexer: util.LookaheadLexer) -> List[str]:
    typ, col_id = lexer.choice_type(_STAR, _QID, _ID)
    projection = []
    if typ in (_QID, _ID):
        while col_id:
            projection.append(col_id)
            col_id = lexer.accept_type(_QID) or lexer.accept_type(_ID)
    else:
        projection.append(col_id)
    return projection


def _parse_select_from(lexer: util.LookaheadLexer) -> List[str]:
    relations = []
    if lexer.accept_type(_FROM):
        relation = lexer.expect_type(_ID)
        while relation:
            relations.append(relation)
            relation = lexer.accept_type(_ID)
    return relations


def _parse_select_where(
        lexer: util.LookaheadLexer) -> Optional[_Condition]:
    conditions: List[_Condition] = []
    while lexer.accept_type(_WHERE):
        conditions.append(_parse_condition_disjunction(lexer))
    condition: Optional[_Condition] = None
    if len(conditions) == 1:
        condition = conditions[0]
    elif len(conditions) > 1:
        condition = ('and', list(conditions))
    return condition


def _parse_condition_disjunction(
        lexer: util.LookaheadLexer) -> _Condition:
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
        return ('or', list(conds))


def _parse_condition_conjunction(
        lexer: util.LookaheadLexer) -> _Condition:
    conds: List[_Condition] = []
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
        return ('and', list(conds))


def _parse_condition_statement(
        column: str,
        lexer: util.LookaheadLexer) -> _Comparison:
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
