# -*- coding: utf-8 -*-

"""
Classes and functions for working with [incr tsdb()] test suites.

.. note::

  This module implements high-level structures and operations on top
  of TSDB test suites. For the basic, low-level functionality, see
  :mod:`delphin.tsdb`. For complex queries of the databases, see
  :mod:`delphin.tsql`.

[incr tsdb()] is a tool built on top of TSDB databases for the purpose
of profiling and comparing grammar versions using test suites. This
module is named after that tool as it also builds higher-level
operations on top of TSDB test suites but it has a much narrower
scope. The aim of this module is to assist users with creating,
processing, or manipulating test suites.
"""

from typing import (
    Iterable, Sequence, Mapping, Tuple, List, Dict,
    Iterator, Generator, Optional, Callable, overload
)
from pathlib import Path
import tempfile
from datetime import datetime
import logging
import collections

from delphin.exceptions import PyDelphinException
from delphin import util
from delphin import tsdb
from delphin.interface import Processor, Response, Result
# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401


##############################################################################
# Module variables

_default_task_selectors = {
    'parse': ('item', 'i-input'),
    'transfer': ('result', 'mrs'),
    'generate': ('result', 'mrs'),
}


#############################################################################
# Exceptions

class ITSDBError(PyDelphinException):
    """Raised when there is an error processing a [incr tsdb()] profile."""


##############################################################################
# Processor Interface


Transaction = List[Tuple[str, tsdb.ColumnMap]]


class FieldMapper(object):
    """
    A class for mapping responses to [incr tsdb()] fields.

    This class provides two methods for mapping responses to fields:

    * :meth:`map` -- takes a response and returns a list of (table,
      data) tuples for the data in the response, as well as
      aggregating any necessary information

    * :meth:`cleanup` -- returns any (table, data) tuples resulting
      from aggregated data over all runs, then clears this data

    In addition, the :attr:`affected_tables` attribute should list
    the names of tables that become invalidated by using this
    FieldMapper to process a profile. Generally this is the list of
    tables that :meth:`map` and :meth:`cleanup` create rows for,
    but it may also include those that rely on the previous set
    (e.g., treebanking preferences, etc.).

    Alternative [incr tsdb()] schema can be handled by overriding
    these two methods and the __init__() method.

    Attributes:
        affected_tables: list of tables that are affected by the
            processing
    """
    def __init__(self):
        # the parse keys exclude some that are handled specially
        self._parse_keys = '''
            ninputs ntokens readings first total tcpu tgc treal words
            l-stasks p-ctasks p-ftasks p-etasks p-stasks
            aedges pedges raedges rpedges tedges eedges ledges sedges redges
            unifications copies conses symbols others gcs i-load a-load
            date error comment
        '''.split()
        self._result_keys = '''
            result-id time r-ctasks r-ftasks r-etasks r-stasks size
            r-aedges r-pedges derivation surface tree mrs
        '''.split()
        self._run_keys = '''
            run-comment platform protocol tsdb application environment
            grammar avms sorts templates lexicon lrules rules
            user host os start end items status
        '''.split()
        self._parse_id = -1
        self._runs = {}
        self._last_run_id = -1

        self.affected_tables = '''
            run parse result rule output edge tree decision preference
            update fold score
        '''.split()

    def map(self, response: Response) -> Transaction:
        """
        Process *response* and return a list of (table, rowdata) tuples.
        """
        transaction = []  # type: Transaction

        patch = self._map_parse(response)
        parse_id = patch['parse-id']
        transaction.append(('parse', patch))

        for result in response.results():  # type: Result
            patch = self._map_result(result, parse_id)
            transaction.append(('result', patch))

        if 'run' in response:
            run_id = response['run'].get('run-id', -1)
            # check if last run was not closed properly
            if run_id not in self._runs and self._last_run_id in self._runs:
                last_run = self._runs[self._last_run_id]
                if 'end' not in last_run:
                    last_run['end'] = datetime.now()
            self._runs[run_id] = response['run']
            self._last_run_id = run_id

        return transaction

    def _map_parse(self, response: Response) -> tsdb.ColumnMap:
        patch = {}  # type: tsdb.ColumnMap
        # custom remapping, cleanup, and filling in holes
        patch['i-id'] = response.get('keys', {}).get('i-id', -1)
        self._parse_id = max(self._parse_id + 1, patch['i-id'])
        patch['parse-id'] = self._parse_id
        patch['run-id'] = response.get('run', {}).get('run-id', -1)
        if 'tokens' in response:
            patch['p-input'] = response['tokens'].get('initial')
            patch['p-tokens'] = response['tokens'].get('internal')
            if 'ninputs' not in response:
                toks = response.tokens('initial')
                if toks is not None:
                    response['ninputs'] = len(toks.tokens)
            if 'ntokens' not in response:
                toks = response.tokens('internal')
                if toks is not None:
                    response['ntokens'] = len(toks.tokens)
        if 'readings' not in response and 'results' in response:
            response['readings'] = len(response['results'])
        # basic mapping
        for key in self._parse_keys:
            if key in response:
                patch[key] = response[key]
        return patch

    def _map_result(self, result: Result, parse_id: int) -> tsdb.ColumnMap:
        patch = {'parse-id': parse_id}  # type: tsdb.ColumnMap
        if 'flags' in result:
            patch['flags'] = util.SExpr.format(result['flags'])
        for key in self._result_keys:
            if key in result:
                patch[key] = result[key]
        return patch

    def cleanup(self) -> Transaction:
        """
        Return aggregated (table, rowdata) tuples and clear the state.
        """
        inserts = []

        last_run = self._runs[self._last_run_id]
        if 'end' not in last_run:
            last_run['end'] = datetime.now()

        for run_id in sorted(self._runs):
            run = self._runs[run_id]
            d = {'run-id': run.get('run-id', -1)}
            for key in self._run_keys:
                if key in run:
                    d[key] = run[key]
            inserts.append(('run', d))

        # reset for next task
        self._parse_id = -1
        self._runs = {}
        self._last_run_id = -1

        return inserts


##############################################################################
# Test items and test suites

class Row(tsdb.Record):
    """
    A row in a [incr tsdb()] table.

    Args:
        fields: column descriptions; an iterable of
            :class:`tsdb.Field` objects
        data: raw column values
        field_index: mapping of field name to its index in *fields*;
            if not given, it will be computed from *fields*
    Attributes:
        fields: The fields of the row.
        data: The raw column values.
    """

    __slots__ = 'fields', 'data', '_field_index'

    def __init__(self,
                 fields: tsdb.Fields,
                 data: Sequence[tsdb.Value],
                 field_index: Mapping[str, int] = None):
        if len(data) != len(fields):
            raise ITSDBError(
                'number of columns ({}) != number of fields ({})'
                .format(len(data), len(fields)))
        if field_index is None:
            field_index = {field.name: i for i, field in enumerate(fields)}
        self.fields = fields
        self.data = tuple(tsdb.format(f.datatype, val)
                          for f, val in zip(fields, data))
        self._field_index = field_index

    def __repr__(self) -> str:
        return 'Row({})'.format(', '.join(map(repr, self)))

    def __str__(self) -> str:
        return tsdb.encode(self, self.fields)

    def __eq__(self, other) -> bool:
        if not hasattr(other, '__iter__'):
            return NotImplemented
        return tuple(self) == tuple(other)

    def __len__(self) -> int:
        return len(self.fields)

    def __iter__(self) -> Iterator[tsdb.Value]:
        cast = tsdb.cast
        datatypes = tuple(field.datatype for field in self.fields)
        for datatype, raw_value in zip(datatypes, self.data):
            yield cast(datatype, raw_value)

    @overload
    def __getitem__(self, key: int) -> tsdb.Value:
        ...

    @overload  # noqa: F811
    def __getitem__(self, key: slice) -> Tuple[tsdb.Value]:
        ...

    @overload  # noqa: F811
    def __getitem__(self, key: str) -> tsdb.Value:
        ...

    def __getitem__(self, key):  # noqa: F811
        cast = tsdb.cast
        if isinstance(key, slice):
            fields = self.fields[key]
            raw_values = self.data[key]
            return tuple(cast(field.datatype, raw)
                         for field, raw in zip(fields, raw_values))
        else:
            if isinstance(key, str):
                index = self._field_index[key]
            else:
                index = key
            field = self.fields[index]
            raw_value = self.data[index]
            return cast(field.datatype, raw_value)

    def keys(self) -> List[str]:
        """
        Return the list of field names for the row.

        Note this returns the names of all fields, not just those with
        the `:key` flag.
        """
        return [f.name for f in self.fields]


Rows = Sequence[Row]


class Table(tsdb.Relation):
    """
    A [incr tsdb()] table.

    Instances of this class contain a collection of rows with the data
    stored in the database. Generally a Table will be created by a
    instantiated individually by the :meth:`Table.from_file` class
    :class:`TestSuite` object for a database, but a Table can also be
    method, and the relations file in the same directory is used to
    get the schema. Tables can also be constructed entirely in-memory
    and separate from a test suite via the standard `Table()`
    constructor.

    Tables have two modes: **attached** and **detached**. Attached
    tables are backed by a file on disk (whether as part of a test
    suite or not) and only store modified rows in memory---all
    unmodified rows are retrieved from disk. Therefore, iterating
    over a table is more efficient than random-access. Attached files
    use significantly less memory than detached tables but also
    require more processing time. Detached tables are entirely stored
    in memory and are not backed by a file. They are useful for the
    programmatic construction of test suites (including for unit
    tests) and other operations where high-speed random-access is
    required.  See the :meth:`attach` and :meth:`detach` methods for
    more information. The :meth:`is_attached` method is useful for
    determining the mode of a table.

    Args:
        dir: path to the database directory
        name: name of the table
        fields: the table schema; an iterable of :class:`tsdb.Field`
            objects
        encoding: character encoding of the table file
    Attributes:
        dir: The path to the database directory.
        name: The name of the table.
        fields: The table's schema.
        encoding: The character encoding of table files.
    """

    def __init__(self,
                 dir: util.PathLike,
                 name: str,
                 fields: tsdb.Fields,
                 encoding: str = 'utf-8') -> None:
        super().__init__(dir, name, fields, encoding=encoding)
        try:
            tsdb.get_path(self.dir, name)
        except tsdb.TSDBError:
            # file didn't exist as plain-text or gzipped, so create it
            path = self.dir.joinpath(name)
            path.write_text('')
        self._rows = []  # type: List[Optional[Row]]

        # These two numbers are needed to track if changes to the
        # table are only additions or if they remove/alter existing
        # rows. The first is the number of rows in the file and the
        # second is the index of the first unwritten row
        self._persistent_count = 0
        self._volatile_index = 0

        self._sync_with_file()

    @property
    def _in_transaction(self) -> bool:
        num_recs = len(self._rows)
        return (num_recs > self._persistent_count
                or self._volatile_index < self._persistent_count)

    def _sync_with_file(self) -> None:
        """Clear in-memory structures so table is synced with the file."""
        self._rows = []
        i = -1
        for i, line in self._enum_lines():
            self._rows.append(None)
        self._persistent_count = i + 1
        self._volatile_index = i + 1

    def __iter__(self) -> Generator[Row, None, None]:
        yield from self._iterslice(slice(None))

    @overload
    def __getitem__(self, index: int) -> Row:
        ...

    @overload  # noqa: F811
    def __getitem__(self, index: slice) -> Rows:
        ...

    def __getitem__(self, index):  # noqa: F811
        if isinstance(index, slice):
            return list(self._iterslice(index))
        else:
            return self._getitem(index)

    def _iterslice(self, slice: slice) -> Generator[Row, None, None]:
        """Yield rows from a slice index."""
        indices = range(*slice.indices(len(self._rows)))
        rows = self._enum_rows(indices)
        if slice.step is not None and slice.step < 0:
            rows = reversed(list(rows))
        for i, row in rows:
            yield row

    def _getitem(self, index: int) -> Row:
        """Get a single non-slice index."""
        row = self._rows[index]
        if row is None:
            # need to handle negative indices manually
            if index < 0:
                index = len(self._rows) + index
            row = next((Row(self.fields,
                            tsdb.decode(line, self.fields),
                            field_index=self._field_index)
                        for i, line in self._enum_lines()
                        if i == index))
        return row

    @overload
    def __setitem__(self, index: int, value: Row) -> None:
        ...

    @overload  # noqa: F811
    def __setitem__(self, index: slice, value: Iterable[Row]) -> None:
        ...

    def __setitem__(self, index, value):  # noqa: F811
        # first normalize the arguments for slices and regular indices
        if isinstance(index, slice):
            values = list(value)
        else:
            self._rows[index]  # check for IndexError
            values = [value]
            index = slice(index, index + 1)
        # now prepare the rows for being in a table
        for i, row in enumerate(values):
            values[i] = Row(self.fields,
                            row,
                            field_index=self._field_index)
        self._rows[index] = values
        self._volatile_index = min(
            self._volatile_index,
            min(index.indices(len(self._rows))[:2])
        )

    def __len__(self) -> int:
        return len(self._rows)

    def clear(self) -> None:
        self._rows.clear()
        self._volatile_index = 0

    def append(self, row: Row) -> None:
        """
        Add *row* to the end of the table.

        Args:
            row: a :class:`Row` or other iterable containing
                column values
        """
        self.extend([row])

    def extend(self, rows: Rows) -> None:
        """
        Add each row in *rows* to the end of the table.

        Args:
            row: an iterable of :class:`Row` or other iterables
                containing column values
        """
        for row in rows:
            if not isinstance(row, Row):
                row = Row(self.fields,
                          row,
                          field_index=self._field_index)
            self._rows.append(row)

    def update(self, index: int,
               data: Mapping[str, tsdb.Value]) -> None:
        """
        Update the row at *index* with *data*.

        Args:
            index: the 0-based index of the row in the table
            data: a mapping of column names to values for replacement

        Examples:
            >>> table.update(0, {'i-input': '...'})
        """
        if not isinstance(index, int):
            raise TypeError(type(index).__name__)
        values = list(self[index])
        for key, value in data.items():
            field_index = self._field_index[key]
            values[field_index] = value
        self[index] = Row(self.fields,
                          values,
                          field_index=self._field_index)

    def select(self, *names: str) -> Generator[Row, None, None]:
        """
        Select fields given by *names* from each row in the table.

        If no field names are given, all fields are returned.

        Yields:
            Row
        Examples:
            >>> next(table.select())
            Row(10, 'unknown', 'formal', 'none', 1, 'S', 'It rained.', ...)
            >>> next(table.select('i-id'))
            Row(10)
            >>> next(table.select('i-id', 'i-input'))
            Row(10, 'It rained.')
        """
        indices = map(self._field_index.__getitem__, names)
        fields = list(map(self.fields.__getitem__, indices))
        field_index = {field.name: i for i, field in enumerate(fields)}
        for row in super().select(*names):
            yield Row(fields, row, field_index=field_index)

    def _enum_lines(self):
        """Enumerate raw lines from the table file."""
        with tsdb.open(self.dir,
                       self.name,
                       encoding=self.encoding) as lines:
            yield from enumerate(lines)

    def _enum_rows(self, indices):
        """Enumerate on-disk and in-memory rows."""
        fields = self.fields
        field_index = self._field_index
        rows = self._rows
        i = 0
        # first rows covered by the file
        for i, line in self._enum_lines():
            if i in indices:
                row = rows[i]
                if row is None:
                    row = Row(fields,
                              tsdb.decode(line, fields),
                              field_index=field_index)
                yield (i, row)
        # then any uncommitted rows
        for j in range(i, len(rows)):
            if j in indices and rows[j] is not None:
                yield (j, rows[j])


class TestSuite(tsdb.Database):
    """
    A [incr tsdb()] test suite database.

    Args:
        path: the path to the test suite's directory
        schema (dict, str): the database schema; either a mapping of
            table names to lists of :class:`Fields <Field>` or a path
            to a relations file; if not given, the relations file
            under *path* will be used
        encoding: the character encoding of the files in the test suite
    Attributes:
        schema (dict): database schema as a mapping of table names to
            lists of :class:`Field` objects
        encoding (str): character encoding used when reading and
            writing tables
    """

    def __init__(self,
                 path: util.PathLike = None,
                 schema: tsdb.SchemaLike = None,
                 encoding: str = 'utf-8') -> None:
        # Virtual test suites use a temporary directory
        if path is None:
            self._tempdir = tempfile.TemporaryDirectory()
            path = Path(self._tempdir.name)
        else:
            path = Path(path).expanduser()
            path.mkdir(exist_ok=True)  # can fail if path is a file

        # Ensure test suite directory has a relations file
        if not path.joinpath(tsdb.SCHEMA_FILENAME).is_file():
            if schema is None:
                raise ITSDBError(
                    '*schema* argument is required for new test suites')
            elif isinstance(schema, (str, Path)):
                schema = tsdb.read_schema(schema)
            tsdb.write_schema(path, schema)

        super().__init__(path, encoding=encoding)
        self._data = {}  # type: Dict[str, Table]

    @property
    def in_transaction(self) -> bool:
        data = self._data
        return any(data[name]._in_transaction
                   for name in self.schema
                   if name in data)

    def __getitem__(self, name: str) -> Table:
        """Return a Table given its name in the schema."""
        if name not in self.schema:
            raise ITSDBError('table not defined in schema: {}'.format(name))
        # if the table is None it is invalidated; reload it
        if name not in self._data:
            self._data[name] = Table(
                self.path, name, self.schema[name], self.encoding)
        return self._data[name]

    def reload(self) -> None:
        """Discard temporary changes and reload the database from disk."""
        for name in self.schema:
            if name in self._data:
                self._data[name]._sync_with_file()

    def commit(self) -> None:
        """
        Commit the current changes to disk.

        This method writes the current state of the test suite to
        disk. The effect is similar to using
        :func:`tsdb.write_database`, except that it also updates the
        test suite's internal bookkeeping so that it is aware that the
        current transaction is complete. It also may be more efficient
        if the only changes are adding new rows to existing tables.
        """
        for name in self.schema:
            if name not in self._data:
                continue
            table = self._data[name]
            fields = self.schema[name]
            if table._in_transaction:
                if table._volatile_index >= table._persistent_count:
                    append = True
                    data = table[table._persistent_count:]
                else:
                    append = False
                    data = table
                tsdb.write(
                    self.path,
                    name,
                    data,
                    fields,
                    append=append,
                    encoding=self.encoding
                )
            table._sync_with_file()

    def process(self,
                cpu: Processor,
                selector: Tuple[str, str] = None,
                source: tsdb.Database = None,
                fieldmapper: FieldMapper = None,
                gzip: bool = None,
                buffer_size: int = 1000) -> None:
        """
        Process each item in a [incr tsdb()] test suite.

        The output rows will be flushed to disk when the number of new
        rows in a table is *buffer_size*.

        Args:
            cpu (:class:`~delphin.interface.Processor`): processor
                interface (e.g., :class:`~delphin.ace.ACEParser`)
            selector: a pair of (table_name, column_name) that specify
                the table and column used for processor input (e.g.,
                `('item', 'i-input')`)
            source (:class:`TestSuite`, :class:`Table`): test suite or
                table from which inputs are taken; if `None`, use the
                current test suite
            fieldmapper (:class:`FieldMapper`): object for
                mapping response fields to [incr tsdb()] fields; if
                `None`, use a default mapper for the standard schema
            gzip: if `True`, compress non-empty tables with gzip
            buffer_size (int): number of output rows to hold in memory
                before flushing to disk; ignored if the test suite is all
                in-memory; if `None`, do not flush to disk
        Examples:
            >>> ts.process(ace_parser)
            >>> ts.process(ace_generator, 'result:mrs', source=ts2)
        """
        if selector is None:
            input_table, input_column = _default_task_selectors[cpu.task]
        else:
            input_table, input_column = selector
        if (input_table not in self.schema
            or all(f.name != input_column
                   for f in self.schema[input_table])):
            raise ITSDBError('invalid table or column: {!s}, {!s}'
                             .format(input_table, input_column))
        if source is None:
            source = self
        if fieldmapper is None:
            fieldmapper = FieldMapper()

        affected = set(fieldmapper.affected_tables).intersection(self.schema)
        for name in affected:
            self[name].clear()

        key_names = [f.name for f in source.schema[input_table] if f.is_key]

        for row in source[input_table]:
            datum = row[input_column]
            keys = [row[name] for name in key_names]
            keys_dict = dict(zip(key_names, keys))
            response = cpu.process_item(datum, keys=keys_dict)
            logging.info(
                'Processed item {:>16}  {:>8} results'
                .format(tsdb.encode(keys), len(response['results']))
            )
            for tablename, data in fieldmapper.map(response):
                _add_row(self[tablename], data, buffer_size)

        for tablename, data in fieldmapper.cleanup():
            _add_row(self[tablename], data, buffer_size)

        tsdb.write_database(self, self.path, gzip=gzip)


def _add_row(table: Table,
             data: Dict,
             buffer_size: int) -> None:
    """
    Prepare and append a Row into its Table; flush to disk if necessary.
    """
    fields = table.fields
    # remove any keys that aren't relation fields
    for invalid_key in set(data).difference([f.name for f in fields]):
        del data[invalid_key]

    table.append(tsdb.make_record(data, fields))

    if len(table) - table._persistent_count > buffer_size:
        table.commit()


##############################################################################
# Non-class (i.e. static) functions

Match = Tuple[tsdb.Value, Rows, Rows]
_Matched = Tuple[List[Row], List[Row]]


def match_rows(rows1: Rows,
               rows2: Rows,
               key: str,
               sort_keys: bool = True) -> Generator[Match, None, None]:
    """
    Yield triples of `(value, left_rows, right_rows)` where
    `left_rows` and `right_rows` are lists of rows that share the same
    column value for *key*. This means that both *rows1* and *rows2*
    must have a column with the same name *key*.

    .. warning::

       Both *rows1* and *rows2* will exist in memory for this
       operation, so it is not recommended for very large tables on
       low-memory systems.

    Args:
        rows1: a :class:`Table` or list of :class:`Row` objects
        rows2: a :class:`Table` or list of :class:`Row` objects
        key (str): the column name on which to match
        sort_keys (bool): if `True`, yield matching rows sorted by the
            matched key instead of the original order
    Yields:
        tuple: a triple containing the matched value for *key*, the
            list of any matching rows from *rows1*, and the list of
            any matching rows from *rows2*
    """
    matched = collections.OrderedDict()  # type: Dict[tsdb.Value, _Matched]
    for i, rows in enumerate([rows1, rows2]):
        for row in rows:
            val = row[key]  # type: tsdb.Value
            try:
                data = matched[val]
            except KeyError:
                matched[val] = ([], [])
                data = matched[val]
            data[i].append(row)
    vals = list(matched.keys())
    if sort_keys:
        vals = sorted(vals, key=util.safe_int)
    for val in vals:
        left, right = matched[val]
        yield (val, left, right)
