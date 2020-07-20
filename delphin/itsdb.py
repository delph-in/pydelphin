# -*- coding: utf-8 -*-

"""
[incr tsdb()] Test Suites
"""

from typing import (
    Union, Iterable, Sequence, Tuple, List, Dict, Any,
    Iterator, Optional, IO, overload, Callable, cast as typing_cast
)
from pathlib import Path
import tempfile
from datetime import datetime
import logging
import collections
import itertools

from delphin import util
from delphin import tsdb
from delphin import interface
# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401


logger = logging.getLogger(__name__)


##############################################################################
# Module variables

_default_task_selectors = {
    'parse': ('item', 'i-input'),
    'transfer': ('result', 'mrs'),
    'generate': ('result', 'mrs'),
}


#############################################################################
# Exceptions

class ITSDBError(tsdb.TSDBError):
    """Raised when there is an error processing a [incr tsdb()] profile."""


##############################################################################
# Processor Interface


Transaction = List[Tuple[str, tsdb.ColumnMap]]


class FieldMapper(object):
    """
    A class for mapping between response objects and test suites.

    If *source* is given, it is the test suite providing the inputs
    used to create the responses, and it is used to provide some
    contextual information that may not be present in the response.

    This class provides two methods for mapping responses to fields:

    * :meth:`map` -- takes a response and returns a list of (table,
      data) tuples for the data in the response, as well as
      aggregating any necessary information

    * :meth:`cleanup` -- returns any (table, data) tuples resulting
      from aggregated data over all runs, then clears this data

    And one method for mapping test suites to responses:

    * :meth:`collect` -- yield :class:`~delphin.interface.Response`
      objects by collecting the relevant data from the test suite

    In addition, the :attr:`affected_tables` attribute should list
    the names of tables that become invalidated by using this
    FieldMapper to process a profile. Generally this is the list of
    tables that :meth:`map` and :meth:`cleanup` create rows for,
    but it may also include those that rely on the previous set
    (e.g., treebanking preferences, etc.).

    Alternative [incr tsdb()] schemas can be handled by overriding
    these three methods and the __init__() method. Note that
    overriding :meth:`collect` is only necessary for mapping back from
    test suites to responses.

    Attributes:
        affected_tables: list of tables that are affected by the
            processing
    """
    def __init__(self, source: tsdb.Database = None):
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
        self._runs: Dict[int, Dict[str, Any]] = {}
        self._last_run_id = -1

        self.affected_tables = '''
            run parse result rule output edge tree decision preference
            update fold score
        '''.split()

        self._i_id_map: Dict[int, int] = {}
        if source:
            pairs = typing_cast(List[Tuple[int, int]],
                                source.select_from(
                                    'parse',
                                    ('parse-id', 'i-id'),
                                    cast=True))
            self._i_id_map.update(pairs)

    def map(self, response: interface.Response) -> Transaction:
        """
        Process *response* and return a list of (table, rowdata) tuples.
        """
        transaction: Transaction = []

        patch = self._map_parse(response)
        parse_id = patch['parse-id']
        assert isinstance(parse_id, int)
        transaction.append(('parse', patch))

        result: interface.Result
        for result in response.results():
            patch = self._map_result(result, parse_id)
            transaction.append(('result', patch))

        for edge in response.get('chart', []):
            patch = self._map_edge(edge, parse_id)
            transaction.append(('edge', patch))

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

    def _map_parse(self, response: interface.Response) -> tsdb.ColumnMap:
        patch: tsdb.ColumnMap = {}
        # custom remapping, cleanup, and filling in holes
        keys = response.get('keys', {})
        if 'i-id' in keys:
            patch['i-id'] = keys['i-id']
        elif 'parse-id' in keys and keys['parse-id'] in self._i_id_map:
            patch['i-id'] = self._i_id_map[keys['parse-id']]
        else:
            patch['i-id'] = -1
        i_id = patch['i-id']
        assert isinstance(i_id, int)  # for type-checker's benefit, mainly
        self._parse_id = max(self._parse_id + 1, i_id)
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

    def _map_result(self,
                    result: interface.Result,
                    parse_id: int) -> tsdb.ColumnMap:
        patch: tsdb.ColumnMap = {'parse-id': parse_id}
        if 'flags' in result:
            patch['flags'] = util.SExpr.format(result['flags'])
        for key in self._result_keys:
            if key in result:
                patch[key] = result[key]
        return patch

    def _map_edge(self,
                  edge: tsdb.ColumnMap,
                  parse_id: int) -> tsdb.ColumnMap:
        edge['parse-id'] = parse_id
        daughters = edge.get('e-daughters')
        if daughters:
            edge['e-daughters'] = util.SExpr.format(daughters)
        else:
            edge['e-daughters'] = None
        alternates = edge.get('e-alternates')
        if alternates:
            edge['e-alternates'] = util.SExpr.format(alternates)
        else:
            edge['e-alternates'] = None
        return edge

    def cleanup(self) -> Transaction:
        """
        Return aggregated (table, rowdata) tuples and clear the state.
        """
        inserts = []

        if self._last_run_id != -1:
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

    def collect(self, ts: 'TestSuite') -> Iterator[interface.Response]:
        """
        Map from test suites to response objects.

        The data in the test suite must be ordered.

        .. note::

           This method stores the 'item', 'parse', and 'result' tables
           in memory during operation, so it is not recommended when a
           test suite is very large as it may exhaust the system's
           available memory.
        """

        # type checking this function is a mess; it needs a better fix

        def get_i_id(row: 'Row') -> int:
            i_id = row['i-id']
            assert isinstance(i_id, int)
            return i_id

        def get_parse_id(row: 'Row') -> int:
            parse_id = row['parse-id']
            assert isinstance(parse_id, int)
            return parse_id

        parse_map: Dict[int, List[Dict[str, tsdb.Value]]] = {}
        rows  = typing_cast(Sequence['Row'], ts['parse'])
        for key, grp in itertools.groupby(rows, key=get_i_id):
            parse_map[key] = [dict(zip(row.keys(), row)) for row in grp]

        result_map: Dict[int, List[Dict[str, tsdb.Value]]] = {}
        rows  = typing_cast(Sequence['Row'], ts['result'])
        for key, grp in itertools.groupby(rows, key=get_parse_id):
            result_map[key] = [dict(zip(row.keys(), row)) for row in grp]

        for item in ts['item']:
            d: Dict[str, tsdb.Value] = dict(zip(item.keys(), item))
            i_id = d['i-id']
            assert isinstance(i_id, int)
            for parse in parse_map.get(i_id, []):
                response = interface.Response(d)
                response.update(parse)
                parse_id = parse['parse-id']
                assert isinstance(parse_id, int)
                response['results'] = result_map.get(parse_id, [])
                yield response


##############################################################################
# Test items and test suites

class Row(tsdb.Record):
    """
    A row in a [incr tsdb()] table.

    The third argument, *field_index*, is optional. Its purpose is to
    reduce memory usage because the same field index can be shared by
    all rows for a table, but using an incompatible index can yield
    unexpected results for value retrieval by field names
    (`row[field_name]`).

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
                 field_index: tsdb.FieldIndex = None):
        if len(data) != len(fields):
            raise ITSDBError(
                'number of columns ({}) != number of fields ({})'
                .format(len(data), len(fields)))
        if field_index is None:
            field_index = tsdb.make_field_index(fields)
        self.fields = fields
        self.data = tuple(tsdb.format(f.datatype, val)
                          for f, val in zip(fields, data))
        self._field_index = field_index

    def __repr__(self) -> str:
        return '<{} object ({}) at {}>'.format(
            type(self).__name__,
            ', '.join(map(repr, self)),
            id(self))

    def __str__(self) -> str:
        return tsdb.join(self, self.fields)

    def __eq__(self, other) -> bool:
        if not hasattr(other, '__iter__'):
            return NotImplemented
        return tuple(self) == tuple(other)

    def __len__(self) -> int:
        return len(self.fields)

    def __iter__(self) -> Iterator[tsdb.Value]:
        datatypes = tuple(field.datatype for field in self.fields)
        for datatype, raw_value in zip(datatypes, self.data):
            yield tsdb.cast(datatype, raw_value)

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
        if isinstance(key, slice):
            fields = self.fields[key]
            raw_values = self.data[key]
            return tuple(tsdb.cast(field.datatype, raw)
                         for field, raw in zip(fields, raw_values))
        else:
            if isinstance(key, str):
                index = self._field_index[key]
            else:
                index = key
            field = self.fields[index]
            raw_value = self.data[index]
            return tsdb.cast(field.datatype, raw_value)

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
        self.dir = Path(dir).expanduser()
        self.name = name
        self.fields: Sequence[tsdb.Field] = fields
        self._field_index = tsdb.make_field_index(fields)
        self.encoding = encoding
        try:
            tsdb.get_path(self.dir, name)
        except tsdb.TSDBError:
            # file didn't exist as plain-text or gzipped, so create it
            path = self.dir.joinpath(name)
            path.write_text('')
        self._rows: List[Optional[Row]] = []
        # storing the open file for __iter__ let's Table.close() work
        self._file: Optional[IO[str]] = None

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
        with tsdb.open(self.dir,
                       self.name,
                       encoding=self.encoding) as lines:
            for i, line in enumerate(lines):
                self._rows.append(None)
        self._persistent_count = i + 1
        self._volatile_index = i + 1

    def __iter__(self) -> Iterator[Row]:
        if self._file is not None:
            self._file.close()
        fh: IO[str] = tsdb.open(self.dir, self.name,
                                encoding=self.encoding)
        self._file = fh

        for _, row in self._enum_rows(fh):
            yield row

    @overload
    def __getitem__(self, index: int) -> Row:
        ...

    @overload  # noqa: F811
    def __getitem__(self, index: slice) -> Rows:
        ...

    def __getitem__(self, index):  # noqa: F811
        if isinstance(index, slice):
            return self._iterslice(index)
        else:
            return self._getitem(index)

    def _iterslice(self, slice: slice) -> List[Row]:
        """Yield rows from a slice index."""
        with tsdb.open(self.dir, self.name, encoding=self.encoding) as fh:
            rows = [row for _, row in self._enum_rows(fh, slice)]
            if slice.step is not None and slice.step < 0:
                rows = list(reversed(rows))
            return rows

    def _getitem(self, index: int) -> Row:
        """Get a single non-slice index."""
        row = self._rows[index]
        if row is None:
            # need to handle negative indices manually
            if index < 0:
                index = len(self._rows) + index
            with tsdb.open(self.dir,
                           self.name,
                           encoding=self.encoding) as lines:
                for i, line in enumerate(lines):
                    if i == index:
                        row = Row(self.fields,
                                  tsdb.split(line),
                                  field_index=self._field_index)
                        break
        if row is None:
            raise ITSDBError('could not retrieve row {}'.format(index))
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
            if index < 0:
                index = len(self._rows) + index
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

    def close(self) -> None:
        """Close the table file being iterated over, if open."""
        if self._file is not None:
            self._file.close()
        self._file = None

    def column_index(self, name: str) -> int:
        """Return the tuple index of the column with name *name*."""
        return self._field_index[name]

    def get_field(self, name: str) -> tsdb.Field:
        """Return the :class:`tsdb.Field` object with column name *name*."""
        return self.fields[self.column_index(name)]

    def clear(self) -> None:
        """Clear the table of all rows."""
        self._rows.clear()
        self._volatile_index = 0

    def append(self, row: tsdb.Record) -> None:
        """
        Add *row* to the end of the table.

        Args:
            row: a :class:`Row` or other iterable containing
                column values
        """
        self.extend([row])

    def extend(self, rows: Iterable[tsdb.Record]) -> None:
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
               data: tsdb.ColumnMap) -> None:
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

    def select(self, *names: str, cast: bool = True) -> Iterator[tsdb.Record]:
        """
        Select fields given by *names* from each row in the table.

        If no field names are given, all fields are returned.

        If *cast* is `False`, simple tuples of raw data are returned
        instead of :class:`Row` objects.

        Yields:
            Row
        Examples:
            >>> next(table.select())
            Row(10, 'unknown', 'formal', 'none', 1, 'S', 'It rained.', ...)
            >>> next(table.select('i-id'))
            Row(10)
            >>> next(table.select('i-id', 'i-input'))
            Row(10, 'It rained.')
            >>> next(table.select('i-id', 'i-input', cast=False))
            ('10', 'It rained.')
        """
        indices = tuple(map(self._field_index.__getitem__, names))
        fields = tuple(map(self.fields.__getitem__, indices))
        field_index = tsdb.make_field_index(fields)
        with tsdb.open(self.dir, self.name, encoding=self.encoding) as fh:
            for _, row in self._enum_rows(fh):
                data = tuple(row.data[i] for i in indices)
                if cast:
                    yield Row(fields, data, field_index=field_index)
                else:
                    yield data

    def _enum_rows(self,
                   fh: IO[str],
                   _slice: slice = None) -> Iterator[Tuple[int, Row]]:
        """Enumerate on-disk and in-memory rows."""
        if _slice is None:
            _slice = slice(None)
        indices = range(*_slice.indices(len(self._rows)))
        fields = self.fields
        field_index = self._field_index

        file_exhausted = False
        for i, row in enumerate(self._rows):
            # always read next line until EOF to keep in sync
            if not file_exhausted:
                line: Optional[str] = None
                try:
                    line = next(fh)
                except StopIteration:
                    file_exhausted = True
            # now skip if it's not a requested index
            if i not in indices:
                continue
            # proceed only if we have a row in memory or on disk
            if row is None:
                if line is not None:
                    row = Row(fields,
                              tsdb.split(line),
                              field_index=field_index)
                else:
                    continue
            yield (i, row)


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

        super().__init__(path, autocast=False, encoding=encoding)
        self._data: Dict[str, Table] = {}

    @property
    def in_transaction(self) -> bool:
        """Return `True` is there are uncommitted changes."""
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

    def select_from(self,
                    name: str,
                    columns: Iterable[str] = None,
                    cast: bool = True):
        """
        Select fields given by *names* from each row in table *name*.

        If no field names are given, all fields are returned.

        If *cast* is `False`, simple tuples of raw data are returned
        instead of :class:`Row` objects.

        Yields:
            Row
        Examples:
            >>> next(ts.select_from('item'))
            Row(10, 'unknown', 'formal', 'none', 1, 'S', 'It rained.', ...)
            >>> next(ts.select_from('item', ('i-id')))
            Row(10)
            >>> next(ts.select_from('item', ('i-id', 'i-input')))
            Row(10, 'It rained.')
            >>> next(ts.select_from('item', ('i-id', 'i-input'), cast=False))
            ('10', 'It rained.')
        """
        if not columns:
            columns = []
        return self[name].select(*columns, cast=cast)

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
                data: tsdb.Records = []
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

    def processed_items(
            self,
            fieldmapper: FieldMapper = None) -> Iterator[interface.Response]:
        """
        Iterate over the data as :class:`Response` objects.
        """
        if fieldmapper is None:
            fieldmapper = FieldMapper()
        yield from fieldmapper.collect(self)

    def process(
            self,
            cpu: interface.Processor,
            selector: Tuple[str, str] = None,
            source: tsdb.Database = None,
            fieldmapper: FieldMapper = None,
            gzip: bool = False,
            buffer_size: int = 1000,
            callback: Callable[[interface.Response], Any] = None,
    ) -> None:
        """
        Process each item in a [incr tsdb()] test suite.

        The output rows will be flushed to disk when the number of new
        rows in a table is *buffer_size*.

        The *callback* parameter can be used, for example, to update a
        progress indicator.

        Args:
            cpu (:class:`~delphin.interface.Processor`): processor
                interface (e.g., :class:`~delphin.ace.ACEParser`)
            selector: a pair of (table_name, column_name) that specify
                the table and column used for processor input (e.g.,
                `('item', 'i-input')`)
            source (:class:`~delphin.tsdb.Database`): test suite from
                which inputs are taken; if `None`, use the current
                test suite
            fieldmapper (:class:`FieldMapper`): object for
                mapping response fields to [incr tsdb()] fields; if
                `None`, use a default mapper for the standard schema
            gzip: if `True`, compress non-empty tables with gzip
            buffer_size (int): number of output rows to hold in memory
                before flushing to disk; ignored if the test suite is all
                in-memory; if `None`, do not flush to disk
            callback: a function that is called with the response for
                each item processed; the return value is ignored
        Examples:
            >>> ts.process(ace_parser)
            >>> ts.process(ace_generator, 'result:mrs', source=ts2)
        """
        if selector is None:
            assert isinstance(cpu.task, str)
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
            fieldmapper = FieldMapper(source=source)
        index = tsdb.make_field_index(source.schema[input_table])

        affected = set(fieldmapper.affected_tables).intersection(self.schema)
        for name in affected:
            self[name].clear()

        key_names = [f.name for f in source.schema[input_table] if f.is_key]

        for row in source[input_table]:
            datum = row[index[input_column]]
            keys = [row[index[name]] for name in key_names]
            keys_dict = dict(zip(key_names, keys))
            response = cpu.process_item(datum, keys=keys_dict)

            logger.info(
                'Processed item {:>16}  {:>8} results'
                .format(tsdb.join(keys), len(response['results']))
            )
            if callback:
                callback(response)

            for tablename, data in fieldmapper.map(response):
                _add_row(self, tablename, data, buffer_size)

        for tablename, data in fieldmapper.cleanup():
            _add_row(self, tablename, data, buffer_size)

        tsdb.write_database(self, self.path, gzip=gzip)


def _add_row(ts: TestSuite,
             name: str,
             data: Dict,
             buffer_size: int) -> None:
    """
    Prepare and append a Row into its Table; flush to disk if necessary.
    """
    fields = ts.schema[name]
    # remove any keys that aren't relation fields
    for invalid_key in set(data).difference([f.name for f in fields]):
        del data[invalid_key]

    ts[name].append(tsdb.make_record(data, fields))

    num_changes = 0
    for _name in ts:
        table = ts[_name]
        num_changes += len(table) - table._persistent_count
    if num_changes > buffer_size:
        ts.commit()


##############################################################################
# Non-class (i.e. static) functions

Match = Tuple[tsdb.Value, Rows, Rows]
_Matched = Tuple[List[Row], List[Row]]


def match_rows(rows1: Rows,
               rows2: Rows,
               key: Union[str, int],
               sort_keys: bool = True) -> Iterator[Match]:
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
        key (str, int): the column name or index on which to match
        sort_keys (bool): if `True`, yield matching rows sorted by the
            matched key instead of the original order
    Yields:
        tuple: a triple containing the matched value for *key*, the
            list of any matching rows from *rows1*, and the list of
            any matching rows from *rows2*
    """
    matched: Dict[tsdb.Value, _Matched] = collections.OrderedDict()
    for i, rows in enumerate([rows1, rows2]):
        for row in rows:
            val: tsdb.Value = row[key]
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
