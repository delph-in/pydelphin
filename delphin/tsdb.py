# -*- coding: utf-8 -*-

"""
TSDB: Test Suite Databases

.. note::

  This module implements the basic, low-level functionality for
  working with TSDB databases. For higher-level views and uses of
  these databases, see :mod:`delphin.itsdb`. For complex queries of
  the databases, see :mod:`delphin.tsql`.

TSDB databases are plain-text file-based relational databases
minimally consisting of a directory with a file, called `relations`,
containing the database's schema (see `Schemas`_). Every table in the
database has its own file, which may be `gzipped
<https://en.wikipedia.org/wiki/Gzip>`_ to save space. The tables have
a simple format with columns delimited by ``@`` and rows delimited by
newlines. This makes them easy to inspect at the command line with
standard Unix tools such as ``cut`` and ``awk`` (but gzipped tables need
to be decompressed or piped from a tool such as ``zcat``).

This module handles the technical details of reading and writing TSDB
databases, including:

- parsing database schemas

- transparently opening either the plain-text or gzipped tables on
  disk, as appropriate

- escaping and unescaping reserved characters in table data

- pairing columns with their schema descriptions

- casting types (such as ``:integer``, ``:date``, etc.)

Additionally, this module provides very basic abstractions of
databases and tables as the :class:`Database` and :class:`Table`
classes, respectively. These serve as base classes for the more
featureful :class:`delphin.itsdb.TestSuite` class, but may be useful
for simple needs.
"""

from typing import (
    Union, Iterable, Sequence, Mapping, Tuple, List, Set,
    Optional, Generator, IO
)
import re
from pathlib import Path
from gzip import open as gzopen
import tempfile
import shutil
from contextlib import contextmanager
from datetime import datetime

from delphin.exceptions import PyDelphinException
from delphin import util
# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401


#############################################################################
# Constants

SCHEMA_FILENAME = 'relations'
FIELD_DELIMITER = '@'
TSDB_CORE_FILES = [
    "item",
    "analysis",
    "phenomenon",
    "parameter",
    "set",
    "item-phenomenon",
    "item-set"
]
TSDB_CODED_ATTRIBUTES = {
    'i-wf': '1',
    'i-difficulty': '1',
    'polarity': '-1'
}
# bidirectional de-localized month map for date parsing/formatting
_MONTHS = {
    1: 'jan', 'jan': 1,
    2: 'feb', 'feb': 2,
    3: 'mar', 'mar': 3,
    4: 'apr', 'apr': 4,
    5: 'may', 'may': 5,
    6: 'jun', 'jun': 6,
    7: 'jul', 'jul': 7,
    8: 'aug', 'aug': 8,
    9: 'sep', 'sep': 9,
    10: 'oct', 'oct': 10,
    11: 'nov', 'nov': 11,
    12: 'dec', 'dec': 12,
}


#############################################################################
# Local types

Value = Union[str, int, float, datetime, None]
Row = Tuple[Value, ...]
ColumnMap = Mapping[str, Value]  # e.g., a partial Row

#############################################################################
# Exceptions


class TSDBError(PyDelphinException):
    """Raised when encountering invalid TSDB databases."""


class TSDBSchemaError(PyDelphinException):
    """Raised when there is an error processing a TSDB schema."""


#############################################################################
# Database Schema

class Field(object):
    '''
    A tuple describing a column in a TSDB database table.

    Args:
        name (str): the column name
        datatype (str): `":string"`, `":integer"`, `":date"`,
            or `":float"`
        flags (list): List of additional flags
        comment (str): a description of the column
    Attributes:
        is_key (bool): `True` if the column is a key in the database.
        default (str): The default value to use when writing a table
            if the value is `None`.
    '''

    __slots__ = 'name', 'datatype', 'flags', 'comment', 'is_key', 'default'

    def __init__(self,
                 name: str,
                 datatype: str,
                 flags: Iterable[str] = None,
                 comment: str = None) -> None:
        self.name = name
        self.datatype = datatype
        self.flags = tuple(flags or [])
        self.comment = comment

        self.is_key = False
        for flag in self.flags:
            if flag in (':key', ':primary') or flag.startswith(':foreign'):
                self.is_key = True

        self.default = TSDB_CODED_ATTRIBUTES.get(
            name,
            '-1' if datatype == ':integer' else ''
        )  # type: str

    def __str__(self):
        parts = [self.name, self.datatype]
        parts.extend(self.flags)
        s = '  ' + ' '.join(parts)
        if self.comment:
            s = '{}# {}'.format(s.ljust(40), self.comment)
        return s

    def __eq__(self, other):
        if not isinstance(other, Field):
            return NotImplemented
        return (self.name == other.name
                and self.datatype == other.datatype
                and self.flags == other.flags)


Fields = Sequence[Field]
Schema = Mapping[str, Fields]
SchemaLike = Union[Schema, util.PathLike]


def read_schema(path: util.PathLike) -> Schema:
    """
    Instantiate schema dict from a schema file given by *path*.

    If *path* is a directory, use the relations file under *path*. If
    *path* is a file, use it directly as the schema's path. Otherwise
    raise a :exc:`TSDBSchemaError`.
    """
    path = Path(path).expanduser()
    if path.is_dir():
        path = path.joinpath(SCHEMA_FILENAME)
    if not path.is_file():
        raise TSDBSchemaError(
            'no valid schema file at {!s}'.format(path))

    return _parse_schema(path.read_text())


def _parse_schema(s: str) -> Schema:
    """Instantiate schema dict from a string."""
    tables = []  # type: List[Tuple[str, Fields]]
    seen = set()  # type: Set[str]
    current_table = ''
    current_fields = []  # type: List[Field]
    lines = list(reversed(s.splitlines()))  # to pop() in right order
    while lines:
        line = lines.pop().strip()
        table_m = re.match(r'^(?P<table>\w.+):$', line)
        field_m = re.match(r'\s*(?P<name>\S+)'
                           r'(\s+(?P<flags>[^#]+))?'
                           r'(\s*#\s*(?P<comment>.*)$)?',
                           line)
        if table_m is not None:
            table_name = table_m.group('table')
            if table_name in seen:
                raise TSDBSchemaError(
                    'table {} redefined'.format(table_name)
                )
            current_table = table_name
            current_fields = []
            tables.append((current_table, current_fields))
            seen.add(table_name)
        elif field_m is not None and current_table:
            name = field_m.group('name')
            flags = field_m.group('flags').split()
            datatype = flags.pop(0)
            comment = field_m.group('comment')
            current_fields.append(
                Field(name, datatype, flags, comment)
            )
        elif line != '':
            raise TSDBSchemaError('invalid line in schema file: ' + line)
    return dict(tables)


def write_schema(path: util.PathLike,
                 schema: Schema) -> None:
    """
    Serialize *schema* and write it to the relations file at *path*.

    If *path* is a directory, write to a `relations` file under
    *path*, otherwise write to the file *path*.
    """
    path = Path(path).expanduser()
    if path.is_dir():
        path = path.joinpath(SCHEMA_FILENAME)
    path.write_text(_format_schema(schema) + '\n')


def _format_schema(schema: Schema) -> str:
    """Serialize a schema dict to its string form."""
    return '\n\n'.join(
        '{name}:\n{fields}'.format(
            name=name,
            fields='\n'.join(str(f) for f in schema[name])
        )
        for name in schema
    )


#############################################################################
# Basic Database Classes

class Table(object):
    """
    A basic abstraction of a TSDB database table.

    This class provides a basic read-only view into a TSDB table. It
    supports iteration over the rows and basic column selection.
    Column values are not cast into their datatypes.

    Args:
        dir: path to the database directory
        name: name of the table
        fields: the table schema; an iterable of :class:`Field` objects
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
                 fields: Fields,
                 encoding: str = 'utf-8') -> None:
        self.dir = Path(dir).expanduser()
        self.name = name
        self.fields = fields
        self.encoding = encoding
        self._field_index = {field.name: i for i, field in enumerate(fields)}

    def __iter__(self) -> Generator[Row, None, None]:
        with open_table(self.dir, self.name, encoding=self.encoding) as f:
            for line in f:
                yield decode_row(line)

    def column_index(self, name: str) -> int:
        """Return the tuple index of the column with name *name*."""
        return self._field_index[name]

    def select(self, *names: str) -> Generator[Row, None, None]:
        """
        Select fields given by *names* from each row in the table.

        If no field names are given, all fields are returned.

        Yields:
            tuple: rows containing the specified columns
        Examples:
            >>> next(table.select())
            ('10', 'unknown', 'formal', 'none', '1', 'S', 'It rained.', ...)
            >>> next(table.select('i-id'))
            ('10',)
            >>> next(table.select('i-id', 'i-input'))
            ('10', 'It rained.')
        """
        if not names:
            yield from iter(self)
        else:
            indices = []
            for name in names:
                try:
                    indices.append(self.column_index(name))
                except KeyError as exc:
                    msg = 'no such field: {}'.format(name)
                    raise TSDBError(msg) from exc
            for record in self:
                yield tuple(record[idx] for idx in indices)


class Database(object):
    """
    A basic abstraction of a TSDB database.

    This class manages the basic access into a TSDB database by
    loading its schema and allowing for named access to table data.

    Args:
        path: path to the database directory
        encoding: character encoding of the table files
    Example:
        >>> db = tsdb.Database('my-profile')
        >>> item = db['item']
    Attributes:
        schema: The database's schema.
        encoding: The character encoding of table files.
    """
    def __init__(self,
                 path: util.PathLike,
                 encoding: str = 'utf-8') -> None:
        path = Path(path).expanduser()
        if not is_database_directory(path):
            raise TSDBError('not a valid TSDB database: {!s}'.format(path))
        self._path = path
        self.schema = read_schema(path)
        self.encoding = encoding

    @property
    def path(self) -> util.PathLike:
        """The database directory's path."""
        return self._path

    def __getitem__(self, name: str) -> Table:
        if name not in self.schema:
            raise TSDBError('table not defined in schema: {}'.format(name))
        return Table(self.path, name, self.schema[name], self.encoding)


#############################################################################
# Table Encoding

def escape(string: str) -> str:
    r"""
    Replace any special characters with their TSDB escape
    sequences. The characters and their escape sequences are::

        @          ->  \s
        (newline)  ->  \n
        \          ->  \\

    Also see :func:`unescape`

    Args:
        string: the string to escape
    Returns:
        The escaped string
    """
    # str.replace()... is about 3-4x faster than re.sub() here
    return (string
            .replace('\\', '\\\\')  # must be done first
            .replace('\n', '\\n')
            .replace(FIELD_DELIMITER, '\\s'))


def unescape(string: str) -> str:
    """
    Replace TSDB escape sequences with the regular equivalents.

    Also see :func:`escape`.

    Args:
        string (str): the escaped string
    Returns:
        The string with escape sequences replaced
    """
    # str.replace()... is about 3-4x faster than re.sub() here
    return (string
            .replace('\\\\', '\\')  # must be done first
            .replace('\\n', '\n')
            .replace('\\s', FIELD_DELIMITER))


def decode_row(line: str,
               fields: Fields = None) -> Row:
    """
    Decode a raw line from a table into a list of column values.

    Decoding involves splitting the line by the field delimiter and
    unescaping special characters. The column value for empty fields
    is `None`.

    If *fields* is given, cast each column value into its datatype,
    otherwise the value is returned as a string.

    Args:
        line: a raw line from a TSDB table file.
        fields: an iterable of :class:`Field` objects
    Returns:
        A list of column values.
    """
    raw_values = [unescape(col) if col else None
                  for col in line.rstrip('\n').split(FIELD_DELIMITER)]
    if fields:
        if len(raw_values) != len(fields):
            _mismatched_counts(raw_values, fields)
        row = tuple(cast(f.datatype, col)
                    for col, f in zip(raw_values, fields))
    else:
        row = tuple(raw_values)
    return row


def encode_row(values: Row,
               fields: Fields = None) -> str:
    """
    Encode a list of column values into a string for a table file.

    Encoding involves escaping special characters for each value, then
    joining the values into a single string with the field
    delimiter. If *fields* is given, `None` values will be replaced
    with the default value for their datatype.

    For creating a row from a mapping of column names to values, see
    :func:`make_row`.

    Args:
        values: a list of column values
        fields: an iterable of :class:`Field` objects
    Returns:
        A TSDB-encoded string
    """
    if fields:
        if len(values) != len(fields):
            _mismatched_counts(values, fields)
        raw_values = [format(f.datatype, val, default=f.default)
                      for f, val in zip(fields, values)]
    else:
        raw_values = ['' if v is None else str(v) for v in values]
    escaped_values = map(escape, raw_values)
    return FIELD_DELIMITER.join(escaped_values)


def _mismatched_counts(columns, fields):
    raise TSDBError('number of columns ({}) != number of fields ({})'
                    .format(len(columns), len(fields)))


def make_row(colmap: ColumnMap, fields: Fields) -> Row:
    """
    Encode a mapping of column names to values into a TSDB table row.

    This function is useful when *colmap* is either a subset or
    superset of the columns defined for a row (as determined by
    *fields*). That is, it selects the relevant column values and
    fills in the missing ones with `None` (not the default value; this
    is done in :func:`encode_row`). *fields* is also responsible for
    determining the column order.

    Args:
        row: a mapping of column names to values
        fields: an iterable of :class:`Field` objects
    Returns:
        A list of column values
    """
    return tuple(colmap.get(f.name, None) for f in fields)


def cast(datatype: str, raw_value: Optional[str]) -> Value:
    """
    Cast TSDB field *raw_value* into *datatype*.

    If *raw_value* is `None`, `None` will be returned, regardless of
    the *datatype*.

    Supported datatypes:

    =============  ===================
    TSDB datatype  Python type
    =============  ===================
    `:integer`     `int`
    `:string`      `str`
    `:float`       `float`
    `:date`        `datetime.datetime`
    =============  ===================

    Casting the `:integer`, `:string`, and `:float` types is trivial,
    but for `:date` TSDB uses a non-standard date format.  This format
    generally follows the `DD-MM-YY` pattern, optionally followed by a
    time (with no timezone or UTF-offset allowed). The day of the
    month may be left unspecified, in which case `01` is used. Years
    may be 2 or 4 digits: in the case of 2-digit years, `19` is
    prepended if the 2-digit year is greater than or equal to 93 (the
    year of the first TSNLP publications and the earliest test
    suites), otherwise `20` is prepended (meaning that users are
    advised to start using 4-digit years by, at least, the year 2093).
    In addition, the more universal YYYY-MM-DD format is allowed, but
    it must have 4-digit years (to disambiguate with the other
    pattern).

    Examples:
        >>> tsdb.cast(':integer', '15')
        15
        >>> tsdb.cast(':float', '2.05e-3')
        0.00205
        >>> tsdb.cast(':string', 'Abrams slept.')
        'Abrams slept.'
        >>> tsdb.cast(':date', '10-6-2002')
        datetime.datetime(2002, 6, 10, 0, 0)
        >>> tsdb.cast(':date', '8-sep-1999')
        datetime.datetime(1999, 9, 8, 0, 0)
        >>> tsdb.cast(':date', 'apr-95')
        datetime.datetime(1995, 4, 1, 0, 0)
        >>> tsdb.cast(':date', '01-dec-02 (15:31:01)')
        datetime.datetime(2002, 12, 1, 15, 31, 1)
        >>> tsdb.cast(':date', '2008-10-12 10:51')
        datetime.datetime(2008, 10, 12, 10, 51)
    """
    if raw_value is None:
        return None
    elif datatype == ':integer':
        return int(raw_value)
    elif datatype == ':float':
        return float(raw_value)
    elif datatype == ':date':
        return _parse_datetime(raw_value)
    elif datatype == ':string':
        return raw_value
    else:
        raise TSDBError('invalid datatype: {}'.format(datatype))


def _parse_datetime(s: str) -> datetime:
    if re.match(r':?(today|now)', s):
        return datetime.now()

    # YYYY-MM-DD HH:MM:SS
    m = re.match(
        r'''
        (?P<y>[0-9]{4})
        -(?P<m>[0-9]{1,2}|\w{3})
        (?:-(?P<d>[0-9]{1,2}))?
        (?:\s*\(?
        (?P<H>[0-9]{2}):(?P<M>[0-9]{2})(?::(?P<S>[0-9]{2}))?
        \)?)?''', s, flags=re.VERBOSE)
    if m is None:
        # DD-MM-YYYY HH:MM:SS
        m = re.match(
            r'''
            (?:(?P<d>[0-9]{1,2})-)?
            (?P<m>[0-9]{1,2}|\w{3})
            -(?P<y>[0-9]{2}(?:[0-9]{2})?)
            (?:\s*\(?
                (?P<H>[0-9]{2}):(?P<M>[0-9]{2})(?::(?P<S>[0-9]{2}))?
            \)?)?''', s, flags=re.VERBOSE)
    if m is not None:
        s = _date_fix(m)

    return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')


def _date_fix(mo):
    y = mo.group('y')
    if len(y) == 2:
        pre = '19' if int(y) >= 93 else '20'
        y = pre + y  # beware the year-2093 bug! Use 4-digit dates.
    m = mo.group('m')
    if len(m) == 3:  # assuming 3-letter abbreviations
        m = _MONTHS[m.lower()]
    d = mo.group('d') or '01'
    H = mo.group('H') or '00'
    M = mo.group('M') or '00'
    S = mo.group('S') or '00'
    return '{}-{}-{} {}:{}:{}'.format(y, m, d, H, M, S)


def format(datatype: str,
           value: Optional[Value],
           default: Optional[str] = None) -> str:
    """
    Format a column *value* based on its *field*.

    If *value* is `None` then *default* is returned if it is given
    (i.e., not `None`). If *default* is `None`, `'-1'` is returned if
    *datatype* is `':integer'`, otherwise an empty string (`''`) is
    returned.

    If *datatype* is `':date'` and *value* is a
    :class:`datetime.datetime` object then a TSDB-compatible date
    format (DD-MM-YYYY) is returned.

    In all other cases, *value* is cast directly to a string and
    returned.

    Examples:
        >>> tsdb.format(':integer', 42)
        '42'
        >>> tsdb.format(':integer', None)
        '-1'
        >>> tsdb.format(':integer', None, default='1')
        '1'
        >>> tsdb.format(':date', datetime.datetime(1999,9,8))
        '8-sep-1999'
    """
    if value is None:
        if default is None:
            default = '-1' if datatype == ':integer' else ''
        else:
            default = str(default)  # ensure it is a string
        raw_value = default
    elif datatype == ':date' and isinstance(value, datetime):
        month = _MONTHS[value.month]
        pattern = '{}-{}-%Y'.format(str(value.day), month)
        if (value.hour, value.minute, value.second) != (0, 0, 0):
            pattern += ' %H:%M:%S'
        raw_value = value.strftime(pattern)
    else:
        raw_value = str(value)
    return raw_value

#############################################################################
# Files


def is_database_directory(path: util.PathLike) -> bool:
    """
    Return `True` if *path* is a valid TSDB database directory.

    A path is a valid database directory if it is a directory
    containing a schema file. This is a simple test; the schema file
    itself is not checked for validity.
    """
    path = Path(path).expanduser()
    return path.is_dir() and path.joinpath(SCHEMA_FILENAME).is_file()


def table_path(dir: util.PathLike,
               name: str) -> Path:
    """
    Determine if the table path should end in .gz or not and return it.

    A .gz path is preferred only if it exists and is newer than any
    regular text file path.

    Args:
        dir: TSDB database directory
        name: name of a table in the database
    Raises:
        TSDBError: when neither the .gz nor the text file exist.
    """
    tx_path, gz_path, use_gz = _table_paths(dir, name)
    tbl_path = gz_path if use_gz else tx_path
    if not tbl_path.is_file():
        raise TSDBError(
            'Table does not exist at {!s}(.gz)'
            .format(tbl_path)
        )
    return tbl_path


def _table_paths(dir: util.PathLike, name: str) -> Tuple[Path, Path, bool]:
    tbl_path = Path(dir, name).expanduser()
    tx_path = tbl_path.with_suffix('')
    gz_path = tbl_path.with_suffix('.gz')
    use_gz = False
    if (gz_path.is_file()
        and (not tx_path.exists()
             or gz_path.stat().st_mtime > tx_path.stat().st_mtime)):
        use_gz = True
    return tx_path, gz_path, use_gz


# Note: the return type should have TextIO instead of IO[str], but
# there's a bug in the type checker. Replace when mypy no longer
# complains about TextIO.
@contextmanager
def open_table(dir: util.PathLike,
               name: str,
               encoding: str = 'utf-8') -> Generator[IO[str], None, None]:
    """
    Transparently open the compressed or text table file.

    Can be used as a context manager in a 'with' statement, but it
    cannot be directly iterated over like a normal open file.

    Args:
        dir: path to the database directory
        name: the name of the table to open
        encoding: character encoding of the table file
    Example:
        >>> sentences = []
        >>> with tsdb.'item', open_table('my-profile') as item:
        ...     for line in item:
        ...         sentences.append(tsdb.decode_row(line)[6])
    """
    path = table_path(dir, name)
    # open and gzip.open don't accept pathlib.Path objects until Python 3.6
    if path.suffix.lower() == '.gz':
        with gzopen(str(path), mode='rt', encoding=encoding) as f:
            yield f
    else:
        with path.open(encoding=encoding) as f:
            yield f


def write_table(dir: util.PathLike,
                name: str,
                rows: Iterable[Row],
                fields: Fields,
                append: bool = False,
                gzip: Optional[bool] = None,
                encoding: str = 'utf-8') -> None:
    """
    Write *rows* to table *name* in the test suite at *dir*.

    Args:
        dir: path to the database directory
        name: the name of the table to write
        rows: an iterable of rows to write
        fields: an iterable of :class:`Field` objects
        append: if `True`, append to rather than overwriting the file
        gzip: if `True` and the table is not empty, compress the table
            with `gzip`; if `False`, do not compress; if `None`,
            compress if existing table is compressed
        encoding: character encoding of the table file
    Example:
        >>> tsdb.write_table('my-profile',
        ...                  'item',
        ...                  item_rows,
        ...                  schema['item'])
    """
    if encoding is None:
        encoding = 'utf-8'

    if not dir.is_dir():
        raise TSDBError('invalid test suite directory: {}'.format(dir))

    tx_path, gz_path, use_gz = _table_paths(dir, name)
    if gzip is None:
        gzip = use_gz
    dest, other = (gz_path, tx_path) if gzip else (tx_path, gz_path)
    mode = 'ab' if append else 'wb'
    append_nonempty = append and dest.is_file() and dest.stat().st_size > 0

    with tempfile.NamedTemporaryFile(
            mode='w+b', suffix='.tmp',
            prefix=name, dir=str(dir)) as f_tmp:

        for row in rows:
            f_tmp.write((encode_row(row, fields) + '\n').encode(encoding))

        # only gzip non-empty files
        gzip = gzip and (f_tmp.tell() != 0 or append_nonempty)

        # now copy the temp file to the destination
        f_tmp.seek(0)
        if gzip:
            with gzopen(str(dest), mode) as f_out:
                shutil.copyfileobj(f_tmp, f_out)
        else:
            with dest.open(mode=mode) as f_out:
                shutil.copyfileobj(f_tmp, f_out)

    # clean up other (gz or non-gz) file if it exists
    if other.is_file():
        other.unlink()


def write_database(db: Database,
                   path: util.PathLike,
                   tables: Optional[Iterable[str]] = None,
                   schema: SchemaLike = None,
                   gzip: Optional[bool] = None,
                   encoding: str = 'utf-8') -> None:
    """
    Write TSDB database *db* to *path*.

    If *path* is an existing file (not a directory), a
    :class:`TSDBError` is raised. If *path* is an existing directory,
    the directory will be cleared. Every table name in *tables* must
    exist in the destination schema. If *schema* is given (even if it
    is the same as for *db*), every row will be remade (using
    :func:`make_row`) using the schema, and columns may be
    dropped or `None` values inserted as necessary, but no more
    sophisticated changed will be made.

    .. warning::

       If *path* points to an existing directory, all files in that
       directory will be deleted prior to writing the database!
       Directories under *path* will not be deleted.

    Args:
        db: Database containing data to write
        path: the path to the destination database directory
        tables: list of tables to write; if `None` use all tables in
            the destination schema
        schema: the destination database schema; if `None` use the
            schema of *db*
        gzip: if `True`, compress all non-empty tables; if `False`, do
            not compress; if `None` compress if destination table
            exists, is non-empty, and is compressed
        encoding: character encoding for the table files
    """
    path = Path(path).expanduser()
    if path.is_file():
        raise TSDBError('not a directory: {!s}'.format(path))
    remake_rows = schema is not None
    if schema is None:
        schema = db.schema
    elif isinstance(schema, (str, Path)):
        schema = read_schema(schema)
    if tables is None:
        tables = list(schema)

    # Prepare destination directory
    path.mkdir(exist_ok=True)
    write_schema(path, schema)

    for name in tables:
        fields = schema[name]
        if name in db.schema:
            table = db[name]
        else:
            table = Table(path, name, fields, encoding=encoding)
        if remake_rows:
            rows = _remake_rows(table, fields)
        else:
            rows = iter(table)
        write_table(path,
                    name,
                    rows,
                    fields,
                    append=False,
                    gzip=gzip,
                    encoding=encoding)

    # only delete other files at the end in case db.path == path
    keepers = set(tables).union([SCHEMA_FILENAME])
    for existing in path.iterdir():
        if existing.is_file() and existing.with_suffix('').name not in keepers:
            existing.unlink()


def _remake_rows(table, fields):
    field_names = [field.name for field in table.fields]
    for row in table:
        colmap = dict(zip(field_names, row))
        yield make_row(colmap, fields)
