# -*- coding: utf-8 -*-

"""
Classes and functions for working with [incr tsdb()] profiles.

The `itsdb` module provides classes and functions for working with
[incr tsdb()] profiles (or, more generally, testsuites; see
http://moin.delph-in.net/ItsdbTop). It handles the technical details
of encoding and decoding records in tables, including escaping and
unescaping reserved characters, pairing columns with their relational
descriptions, casting types (such as `:integer`, etc.), and
transparently handling gzipped tables, so that the user has a natural
way of working with the data. Capabilities include:

* Reading and writing testsuites:

    >>> from delphin import itsdb
    >>> ts = itsdb.TestSuite('jacy/tsdb/gold/mrs')
    >>> ts.write(path='mrs-copy')

* Selecting data by table name, record index, and column name or index:

    >>> ts['item'][0]['i-input']  # input sentence of the first item
    '雨 が 降っ た ．'
    >>> ts['item'][0]['i-id']     # :integer fields are cast to ints
    11

* Selecting data as a query:

    >>> next(ts.select('item:i-id@i-input'))
    [11, '雨 が 降っ た ．']

* In-memory modification of testsuite data:

    >>> # desegment each sentence
    >>> for record in ts['item']:
    ...     record['i-input'] = ''.join(record['i-input'].split())
    ...
    >>> ts['item'][0]['i-input']
    '雨が降った．'

* Joining tables

    >>> joined = itsdb.join(ts['parse'], ts['result'])
    >>> joined[0]['parse:i-id'], joined[0]['result:mrs']
    (11, '[ LTOP: h1 INDEX: e2 [ e TENSE: PAST ...')

* Processing data with ACE (results are stored in memory)

    >>> from delphin.interfaces import ace
    >>> with ace.AceParser('jacy.dat') as cpu:
    ...     ts.process(cpu)
    ...
    NOTE: parsed 126 / 135 sentences, avg 3167k, time 1.87536s
    >>> ts.write('new-profile')

This module covers all aspects of [incr tsdb()] data, from
:class:`Relations` files and :class:`Field` descriptions to
:class:`Record`, :class:`Table`, and full :class:`TestSuite` classes.
:class:`TestSuite` is the most user-facing interface, and it makes it
easy to load the tables of a testsuite into memory, inspect its
contents, modify or create data, and write the data to disk.

By default, the `itsdb` module expects testsuites to use the
standard [incr tsdb()] schema. Testsuites are always read and written
according to the associated or specified relations file, but other
things, such as default field values and the list of "core" tables,
are defined for the standard schema. It is, however, possible to
define non-standard schemata for particular applications, and most
functions will continue to work.

"""

from __future__ import print_function
# TODO: Remove when Python2.7 support is gone
try:
    unicode
except NameError:
    unicode = str

import os
import re
from gzip import GzipFile
import logging
import io
from io import TextIOWrapper, BufferedReader
from collections import (
    defaultdict, namedtuple, OrderedDict, Sequence, Mapping
)
from itertools import chain
from contextlib import contextmanager


from delphin.exceptions import ItsdbError
from delphin.util import (
    safe_int, stringtypes, deprecated, parse_datetime
)
from delphin.interfaces.base import FieldMapper

##############################################################################
# Module variables

_relations_filename = 'relations'
_field_delimiter = '@'
_default_datatype_values = {
    ':integer': '-1'
}
tsdb_coded_attributes = {
    'i-wf': 1,
    'i-difficulty': 1,
    'polarity': -1
}
_primary_keys = [
    ["i-id", "item"],
    ["p-id", "phenomenon"],
    ["ip-id", "item-phenomenon"],
    ["s-id", "set"],
    ["run-id", "run"],
    ["parse-id", "parse"],
    ["e-id", "edge"],
    ["f-id", "fold"]
]
tsdb_core_files = [
    "item",
    "analysis",
    "phenomenon",
    "parameter",
    "set",
    "item-phenomenon",
    "item-set"
]
_default_task_input_selectors = {
    'parse': 'item:i-input',
    'transfer': 'result:mrs',
    'generate': 'result:mrs',
}

#############################################################################
# Relations files

class Field(
        namedtuple('Field', 'name datatype key partial comment'.split())):
    '''
    A tuple describing a column in an [incr tsdb()] profile.

    Args:
        name (str): the column name
        datatype (str): `":string"`, `":integer"`, `":date"`,
            or `":float"`
        key (bool): `True` if the column is a key in the database
        partial (bool): `True` if the column is a partial key
        comment (str): a description of the column
    '''
    def __new__(cls, name, datatype, key=False, partial=False, comment=None):
        return super(Field, cls).__new__(
            cls, name, datatype, key, partial, comment
        )

    def __str__(self):
        parts = [self.name, self.datatype]
        if self.key:
            parts += [':key']
        if self.partial:
            parts += [':partial']
        s = '  ' + ' '.join(parts)
        if self.comment:
            s = '{}# {}'.format(s.ljust(40), self.comment)
        return s

    def default_value(self):
        """Get the default value of the field."""
        if self.name in tsdb_coded_attributes:
            return tsdb_coded_attributes[self.name]
        elif self.datatype == ':integer':
            return -1
        else:
            return ''


class Relation(tuple):
    """
    A [incr tsdb()] table schema.

    Args:
        name: the table name
        fields: a list of Field objects
    """
    def __new__(cls, name, fields):
        tr = super(Relation, cls).__new__(cls, fields)
        tr.name = name
        tr._index = dict(
            (f.name, i) for i, f in enumerate(fields)
        )
        tr._keys = tuple(f.name for f in fields if f.key)
        return tr

    def __contains__(self, name):
        return name in self._index

    def index(self, fieldname):
        """Return the Field index given by *fieldname*."""
        return self._index[fieldname]

    def keys(self):
        """Return the tuple of field names of key fields."""
        return self._keys


class _RelationJoin(Relation):
    def __new__(cls, rel1, rel2, on=None):
        if set(rel1.name.split('+')).intersection(rel2.name.split('+')):
            raise ItsdbError('Cannot join tables with the same name; '
                             'try renaming the table.')

        name = '{}+{}'.format(rel1.name, rel2.name)
        # the relation of the joined table, merging shared columns in *on*
        if isinstance(on, stringtypes):
            on = _split_cols(on)
        elif on is None:
            on = []

        fields = _prefixed_relation_fields(rel1, on, False)
        fields.extend(_prefixed_relation_fields(rel2, on, True))
        r = super(_RelationJoin, cls).__new__(cls, name, fields)

        # reset _keys to be a unique tuple of column-only forms
        keys = list(rel1.keys())
        seen = set(keys)
        for key in rel2.keys():
            if key not in seen:
                keys.append(key)
                seen.add(key)
        r._keys = tuple(keys)

        return r

    def __contains__(self, name):
        try:
            self.index(name)
        except KeyError:
            return False
        except ItsdbError:
            pass  # ambiguous field name
        return True

    def index(self, fieldname):
        if ':' not in fieldname:
            qfieldnames = []
            for table in self.name.split('+'):
                qfieldname = table + ':' + fieldname
                if qfieldname in self._index:
                    qfieldnames.append(qfieldname)
            if len(qfieldnames) > 1:
                raise ItsdbError(
                    "ambiguous field name; include the table name "
                    "(e.g., 'item:i-id' instead of 'i-id')")
            elif len(qfieldnames) == 1:
                fieldname = qfieldnames[0]
            else:
                pass  # lookup should return KeyError
        elif fieldname not in self._index:
            # join keys don't get prefixed
            uqfieldname = fieldname.rpartition(':')[2]
            if uqfieldname in self._keys:
                fieldname = uqfieldname
        return self._index[fieldname]


def _prefixed_relation_fields(relation, on, drop):
    fields = []
    already_joined = isinstance(relation, _RelationJoin)
    for f in relation:
        table, _, fieldname = f[0].rpartition(':')
        if already_joined :
            prefix = table + ':' if table else ''
        else:
            prefix = relation.name + ':'
        if fieldname in on and not drop:
            fields.append(Field(fieldname, *f[1:]))
        elif fieldname not in on:
            fields.append(Field(prefix + fieldname, *f[1:]))
    return fields


class Relations(object):
    """
    A [incr tsdb()] database schema.

    Note:
      Use :meth:`from_file` or :meth:`from_string` for instantiating
      a Relations object.

    Args:
        tables: a list of `(table, :class:`Relation`)` tuples
    """

    def __init__(self, tables):
        tables = [(t[0], Relation(*t)) for t in tables]
        self.tables = tuple(t[0] for t in tables)
        self._data = dict(tables)
        self._field_map = _make_field_map(t[1] for t in tables)

    @classmethod
    def from_file(cls, source):
        """Instantiate Relations from a relations file."""
        if hasattr(source, 'read'):
            relations = cls.from_string(source.read())
        else:
            with open(source) as f:
                relations = cls.from_string(f.read())
        return relations

    @classmethod
    def from_string(cls, s):
        """Instantiate Relations from a relations string."""
        tables = []
        seen = set()
        current_table = None
        lines = list(reversed(s.splitlines()))  # to pop() in right order
        while lines:
            line = lines.pop().strip()
            table_m = re.match(r'^(?P<table>\w.+):$', line)
            field_m = re.match(r'\s*(?P<name>\S+)'
                               r'(\s+(?P<attrs>[^#]+))?'
                               r'(\s*#\s*(?P<comment>.*)$)?',
                               line)
            if table_m is not None:
                table_name = table_m.group('table')
                if table_name in seen:
                    raise ItsdbError(
                        'Table {} already defined.'.format(table_name)
                    )
                current_table = (table_name, [])
                tables.append(current_table)
                seen.add(table_name)
            elif field_m is not None and current_table is not None:
                name = field_m.group('name')
                attrs = field_m.group('attrs').split()
                datatype = attrs.pop(0)
                key = ':key' in attrs
                partial = ':partial' in attrs
                comment = field_m.group('comment')
                current_table[1].append(
                    Field(name, datatype, key, partial, comment)
                )
            elif line != '':
                raise ItsdbError('Invalid line: ' + line)
        return cls(tables)

    def __contains__(self, key):
        return key in self._data

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        return iter(self.tables)

    def __len__(self):
        return len(self.tables)

    def __str__(self):
        return '\n\n'.join(
            '{tablename}:\n{fields}'.format(
                tablename=tablename,
                fields='\n'.join(str(f) for f in self[tablename])
            )
            for tablename in self
        )

    def items(self):
        """Return a list of (table, :class:`Relation`) for each table."""
        return [(table, self[table]) for table in self]

    def find(self, fieldname):
        """
        Return the list of tables that define the field *fieldname*.
        """
        tablename, _, column = fieldname.rpartition(':')
        if tablename and tablename in self._field_map[column]:
            return tablename
        else:
            return self._field_map[fieldname]

    def path(self, source, target):
        """
        Find the path of id fields connecting two tables.

        This is just a basic breadth-first-search. The relations file
        should be small enough to not be a problem.

        Returns:
            list: (table, fieldname) pairs describing the path from
                the source to target tables
        Raises:
            :class:`ItsdbError` when no path is found
        Example:
            >>> relations.path('item', 'result')
            [('parse', 'i-id'), ('result', 'parse-id')]
            >>> relations.path('parse', 'item')
            [('item', 'i-id')]
            >>> relations.path('item', 'item')
            []
        """
        visited = set(source.split('+'))  # split on + for joins
        targets = set(target.split('+')) - visited
        # ensure sources and targets exists
        for tablename in visited.union(targets):
            self[tablename]
        # base case; nothing to do
        if len(targets) == 0:
            return []
        paths = [[(tablename, None)] for tablename in visited]
        while True:
            newpaths = []
            for path in paths:
                laststep, pivot = path[-1]
                if laststep in targets:
                    return path[1:]
                else:
                    for key in self[laststep].keys():
                        for step in set(self.find(key)) - visited:
                            visited.add(step)
                            newpaths.append(path + [(step, key)])
            if newpaths:
                paths = newpaths
            else:
                break

        raise ItsdbError('no relation path found from {} to {}'
                         .format(source, target))



def _make_field_map(rels):
    g = {}
    for rel in rels:
        for field in rel:
            g.setdefault(field.name, []).append(rel.name)
    return g


##############################################################################
# Test items and test suites

class Record(list):
    """
    A row in a [incr tsdb()] table.

    Args:
        fields: the Relation schema for the table of this record
        iterable: an iterable containing the data for the record
    Attributes:
        fields (:class:`Relation`): table schema
    """

    def __init__(self, fields, iterable):
        # normalize data format
        if isinstance(iterable, Mapping):
            d = iterable
            iterable = [None] * len(fields)
            for key, value in d.items():
                try:
                    index = fields.index(key)
                except KeyError:
                    raise ItsdbError('Invalid field name(s): ' + key)
                iterable[index] = value
        else:
            iterable = list(iterable)

        if len(fields) != len(iterable):
            raise ItsdbError(
                'Incorrect number of column values: {} != {}'
                .format(len(iterable), len(fields))
            )

        for i, value in enumerate(iterable):
            field = fields[i]
            if value is None:
                if field.key:
                    raise ItsdbError('Missing key: {}'.format(field.name))
                iterable[i] = field.default_value()
            else:
                iterable[i] = value

        self.fields = fields
        super(Record, self).__init__(iterable)

    def __repr__(self):
        return "<{} '{}' {}>".format(
            self.__class__.__name__,
            self.fields.name,
            ' '.join('{}={}'.format(k, self[k]) for k in self.fields.keys())
        )

    def __str__(self):
        return make_row(self, self.fields)

    def __getitem__(self, index):
        if not isinstance(index, int):
            index = self.fields.index(index)
        return list.__getitem__(self, index)

    def __setitem__(self, index, value):
        if not isinstance(index, int):
            index = self.fields.index(index)
        # should the value be validated against the datatype?
        return list.__setitem__(self, index, value)

    def get(self, key, default=None, cast=False):
        """
        Return the field data given by field name *key*.

        Args:
            key: the field name of the data to return
            default: the value to return if *key* is not in the row
        """
        tablename, _, key = key.rpartition(':')
        if tablename and tablename not in self.fields.name.split('+'):
            raise ItsdbError('column requested from wrong table: {}'
                             .format(tablename))
        try:
            index = self.fields.index(key)
            value = list.__getitem__(self, index)
        except (KeyError, IndexError):
            value = default
        else:
            if cast:
                dt = self.fields[index].datatype
                if dt == ':integer':
                    value = int(value)
                elif dt == ':float':
                    value = float(value)
                elif dt == ':date':
                    value = parse_datetime(value)
                # others?
        return value


class Table(list):
    """
    A [incr tsdb()] table.

    Instances of this class contain a collection of rows with the data
    stored in the database. Generally a Table will be created by a
    TestSuite object for a database, but a Table can also be instantiated
    individually by the Table.from_file() class method, and the relations
    file in the same directory is used to get the schema.

    Args:
        name: the table name
        fields: the Relation schema for this table
        records: the collection of Record objects containing the table data
    Attributes:
        name (str): table name
        fields (:class:`Relation`): table schema
    """

    def __init__(self, name, fields, records=None):
        self.name = name
        self.fields = fields
        # columns = [f.name for f in fields]
        if records is None:
            records = []
        # ensure records are Record objects
        list.__init__(self, [Record(fields, rec) for rec in records])

    @classmethod
    def from_file(cls, path, name=None, fields=None, encoding='utf-8'):
        """
        Instantiate a Table from a database file.

        Args:
            path: the path to the table file
            name: the table name (inferred by the filename if not given)
            fields: the Relation schema for the table (loaded from the
                relations file in the same directory if not given)
            encoding: the character encoding of the files in the testsuite
        """
        path = _table_filename(path)  # do early in case file not found

        if name is None:
            name = os.path.basename(path).rsplit('.gz', 1)[0]

        if fields is None:
            rpath = os.path.join(os.path.dirname(path), _relations_filename)
            if not os.path.exists(rpath):
                raise ItsdbError(
                    'No fields are specified and a relations file could '
                    'not be found.'
                )
            rels = Relations.from_file(rpath)
            if name not in rels:
                raise ItsdbError(
                    'Table \'{}\' not found in the relations.'.format(name)
                )
            # successfully inferred the relations for the table
            fields = rels[name]

        records = []
        with _open_table(path, encoding) as tab:
            records.extend(map((lambda s: decode_row(s)), tab))

        return cls(name, fields, records)

    def select(self, cols, mode='list'):
        """
        Select columns from each row in the table.

        See select_rows() for a description of how to use the
        *mode* parameter.

        Args:
            cols: an iterable of Field (column) names
            mode: how to return the data
        """
        if isinstance(cols, stringtypes):
            cols = _split_cols(cols)
        if not cols:
            cols = [f.name for f in self.fields]
        return select_rows(cols, self, mode=mode)


class TestSuite(object):
    """
    A [incr tsdb()] testsuite database.

    Args:
        path: the path to the testsuite's directory
        relations: the relations file describing the schema of
            the database; if not given, the relations file under
            *path* will be used
        encoding: the character encoding of the files in the testsuite
    Attributes:
        encoding (:py:class:`str`): character encoding used when reading and
            writing tables
        relations (:class:`Relations`): database schema
    """
    def __init__(self, path=None, relations=None, encoding='utf-8'):
        self._path = path
        self.encoding = encoding

        if isinstance(relations, Relations):
            self.relations = relations
        elif relations is None and path is not None:
            relations = os.path.join(self._path, _relations_filename)
            self.relations = Relations.from_file(relations)
        elif relations is not None and os.path.isfile(relations):
            self.relations = Relations.from_file(relations)
        else:
            raise ItsdbError(
                'Either the relations parameter must be provided or '
                'path must point to a directory with a relations file.'
            )

        self._data = dict((t, None) for t in self.relations)

        if self._path is not None:
            self.reload()

    def __getitem__(self, tablename):
        # if the table is None it is invalidated; reload it
        if self._data[tablename] is None:
            if self._path is not None:
                self._reload_table(tablename)
            else:
                self._data[tablename] = Table(
                    tablename,
                    self.relations[tablename]
                )
        return self._data[tablename]

    def reload(self):
        """Discard temporary changes and reload the database from disk."""
        for tablename in self.relations:
            self._reload_table(tablename)

    def _reload_table(self, tablename):
        fields = self.relations[tablename]
        tablepath = os.path.join(self._path, tablename)
        if os.path.exists(tablepath) or os.path.exists(tablepath + '.gz'):
            table = Table.from_file(tablepath, name=tablename,
                                    fields=fields, encoding=self.encoding)
        else:
            table = Table(name=tablename, fields=fields)
        self._data[tablename] = table

    def select(self, arg, cols=None, mode='list'):
        """
        Select columns from each row in the table.

        The first parameter, *arg*, may either be a table name or a
        data specifier. If the former, the *cols* parameter selects the
        columns from the table. If the latter, *cols* is left
        unspecified and both the table and columns are taken from the
        data specifier; e.g., `select('item:i-id@i-input')` is
        equivalent to `select('item', ('i-id', 'i-input'))`.

        See select_rows() for a description of how to use the *mode*
        parameter.

        Args:
            arg: a table name, if *cols* is specified, otherwise a data
                specifier
            cols: an iterable of Field (column) names
            mode: how to return the data
        """
        if cols is None:
            table, cols = get_data_specifier(arg)
        else:
            table = arg
        if cols is None:
            cols = [f.name for f in self.relations[table]]
        return select_rows(cols, self[table], mode=mode)

    def write(self, tables=None, path=None, relations=None,
              append=False, gzip=None):
        """
        Write the testsuite to disk.

        Args:
            tables: a name or iterable of names of tables to write,
                or a Mapping of table names to table data; if `None`,
                all tables will be written
            path: the destination directory; if `None` use the path
                assigned to the TestSuite
            relations: a :class:`Relations` object or path to a
                relations file to be used when writing the tables
            append: if `True`, append to rather than overwrite tables
            gzip: compress non-empty tables with gzip
        Examples:
            >>> ts.write(path='new/path')
            >>> ts.write('item')
            >>> ts.write(['item', 'parse', 'result'])
            >>> ts.write({'item': item_rows})
        """
        if path is None:
            path = self._path
        if tables is None:
            tables = self._data
        elif isinstance(tables, stringtypes):
            tables = {tables: self[tables]}
        elif isinstance(tables, Mapping):
            pass
        elif isinstance(tables, Sequence):
            tables = dict((table, self[table]) for table in tables)
        if relations is None:
            relations = self.relations
        elif isinstance(relations, stringtypes):
            relations = Relations.from_file(relations)

        # prepare destination
        if not os.path.exists(path):
            os.makedirs(path)
        # raise error if path != self._path?
        with open(os.path.join(path, _relations_filename), 'w') as fh:
            print(str(relations), file=fh)

        for tablename, relation in relations.items():
            if tablename in tables:
                data = tables[tablename]
                # reload table from disk if it is invalidated
                if data is None:
                    data = self[tablename]
                elif not isinstance(data, Table):
                    data = Table(tablename, relation, data)
                _write_table(
                    path,
                    tablename,
                    data,
                    relation,
                    gzip=gzip,
                    encoding=self.encoding
                )

    def exists(self, table=None):
        """
        Return `True` if the testsuite or a table exists on disk.

        If *table* is `None`, this function returns `True` if the
        :attr:`TestSuite.path` is specified and points to an existing
        directory containing a valid relations file. If *table* is
        given, the function returns `True` if, in addition to the
        above conditions, the table exists as a file (even if
        empty). Otherwise it returns False.
        """
        if self._path is None or not os.path.isdir(self._path):
            return False
        if not os.path.isfile(os.path.join(self._path, _relations_filename)):
            return False
        if table is not None:
            try:
                _table_filename(os.path.join(self._path, table))
            except ItsdbError:
                return False
        return True

    def size(self, table=None):
        """
        Return the size, in bytes, of the testsuite or *table*.

        If *table* is `None`, return the size of the whole testsuite
        (i.e., the sum of the table sizes). Otherwise, return the
        size of *table*.

        Notes:
            * If the file is gzipped, it returns the compressed size.
            * Only tables on disk are included.
        """
        size = 0
        if table is None:
            for table in self.relations:
                size += self.size(table)
        else:
            try:
                fn = _table_filename(os.path.join(self._path, table))
                size += os.stat(fn).st_size
            except ItsdbError:
                pass
        return size

    def process(self, cpu, selector=None, source=None, fieldmapper=None):
        """
        Process each item in a [incr tsdb()] testsuite

        Args:
            cpu (:class:`~delphin.interfaces.base.Processor`):
                processor interface (e.g.,
                :class:`~delphin.interfaces.ace.AceParser`)
            selector (str): data specifier to select a single table and
                column as processor input (e.g., `"item:i-input"`)
            source (:class:`TestSuite`, :class:`Table`): testsuite or
                table from which inputs are taken; if `None`, use `self`
            fieldmapper (:class:`~delphin.interfaces.base.FieldMapper`):
                object for mapping response fields to [incr tsdb()]
                fields; if `None`, use a default mapper for the
                standard schema
        Examples:
            >>> ts.process(ace_parser)
            >>> ts.process(ace_generator, 'result:mrs', source=ts2)
        """
        if selector is None:
            selector = _default_task_input_selectors.get(cpu.task)
        if source is None:
            source = self
        if fieldmapper is None:
            fieldmapper = FieldMapper()

        source, cols = _prepare_source(selector, source)
        key_cols = cols[:-1]

        tables = {}
        for item in select_rows(cols, source, mode='list'):
            datum = item.pop()
            keys = dict(zip(key_cols, item))
            response = cpu.process_item(datum, keys=keys)
            logging.info(
                'Processed item {:>16}  {:>8} results'
                .format(encode_row(item), len(response['results']))
            )
            for tablename, data in fieldmapper.map(response):
                _add_record(tables, tablename, data, self.relations)

        for tablename, data in fieldmapper.cleanup():
            _add_record(tables, tablename, data, self.relations)

        for tablename, table in tables.items():
            self._data[tablename] = table


def _prepare_source(selector, source):
    tablename, fields = get_data_specifier(selector)
    if len(fields) != 1:
        raise ItsdbError(
            'Selector must specify exactly one data column: {}'
            .format(selector)
        )
    if isinstance(source, TestSuite):
        if not tablename:
            tablename = source.relations.find(fields[0])[0]
        source = source[tablename]
    cols = list(source.fields.keys()) + fields
    return source, cols

def _add_record(tables, tablename, data, relations):
    fields = relations[tablename]
    if tablename not in tables:
        tables[tablename] = Table(tablename, fields)
    # remove any keys that aren't relation fields
    for invalid_key in set(data).difference([f.name for f in fields]):
        del data[invalid_key]
    tables[tablename].append(Record(fields, data))



##############################################################################
# Non-class (i.e. static) functions


data_specifier_re = re.compile(r'(?P<table>[^:]+)?(:(?P<cols>.+))?$')
def get_data_specifier(string):
    """
    Return a tuple (table, col) for some [incr tsdb()] data specifier.
    For example::

        item              -> ('item', None)
        item:i-input      -> ('item', ['i-input'])
        item:i-input@i-wf -> ('item', ['i-input', 'i-wf'])
        :i-input          -> (None, ['i-input'])
        (otherwise)       -> (None, None)
    """
    match = data_specifier_re.match(string)
    if match is None:
        return (None, None)
    table = match.group('table')
    if table is not None:
        table = table.strip()
    cols = _split_cols(match.group('cols'))
    return (table, cols)


def _split_cols(colstring):
    if not colstring:
        return None
    colstring = colstring.lstrip(':')
    return [col.strip() for col in colstring.split('@')]

def decode_row(line, fields=None):
    """
    Decode a raw line from a profile into a list of column values.

    Decoding involves splitting the line by the field delimiter
    (`"@"` by default) and unescaping special characters. If *fields*
    is given, cast the values into the datatype given by their
    respective Field object.

    Args:
        line: a raw line from a [incr tsdb()] profile.
        fields: a list or Relation object of Fields for the row
    Returns:
        A list of column values.
    """
    cols = line.rstrip('\n').split(_field_delimiter)
    cols = list(map(unescape, cols))
    if fields is not None:
        if len(cols) != len(fields):
            raise ItsdbError(
                'Wrong number of fields: {} != {}'
                .format(len(cols), len(fields))
            )
        for i in range(len(cols)):
            col = cols[i]
            if col:
                field = fields[i]
                dt = field.datatype
                if dt == ':integer':
                    col = int(col)
                elif dt == ':float':
                    col = float(col)
                elif dt == ':date':
                    dt = parse_datetime(col)
                    col = dt if dt is not None else col
                # other casts? :position?
            cols[i] = col
    return cols


def encode_row(fields):
    """
    Encode a list of column values into a [incr tsdb()] profile line.

    Encoding involves escaping special characters for each value, then
    joining the values into a single string with the field delimiter
    (`"@"` by default). It does not fill in default values (see
    make_row()).

    Args:
        fields: a list of column values
    Returns:
        A [incr tsdb()]-encoded string
    """
    # NOTE: str(f) only works for Python3
    unicode_fields = [unicode(f) for f in fields]
    escaped_fields = map(escape, unicode_fields)
    return _field_delimiter.join(escaped_fields)


_character_escapes = {
    _field_delimiter: '\\s',
    '\n': '\\n',
    '\\': '\\\\'
}

def _escape(m):
    return _character_escapes[m.group(1)]


def escape(string):
    r"""
    Replace any special characters with their [incr tsdb()] escape
    sequences. Default sequences are::

        @         -> \s
        (newline) -> \\n
        \\        -> \\\\

    Also see :func:`unescape`

    Args:
        string: the string to escape
    Returns:
        The escaped string
    """
    return re.sub(r'(@|\n|\\)', _escape, string, flags=re.UNICODE)


_character_unescapes = {'\\s': _field_delimiter, '\\n': '\n', '\\\\': '\\'}

def _unescape(m):
    return _character_unescapes[m.group(1)]


def unescape(string):
    """
    Replace [incr tsdb()] escape sequences with the regular equivalents.
    Also see :func:`escape`.

    Args:
        string (str): the escaped string
    Returns:
        The string with escape sequences replaced
    """
    return re.sub(r'(\\s|\\n|\\\\)', _unescape, string, flags=re.UNICODE)


def _table_filename(tbl_filename):
    if tbl_filename.endswith('.gz'):
        gzfn = tbl_filename
        txfn = tbl_filename[:-3]
    else:
        txfn = tbl_filename
        gzfn = tbl_filename + '.gz'

    if os.path.exists(txfn):
        if (os.path.exists(gzfn) and
                os.stat(gzfn).st_mtime > os.stat(txfn).st_mtime):
            tbl_filename = gzfn
        else:
            tbl_filename = txfn
    elif os.path.exists(gzfn):
        tbl_filename = gzfn
    else:
        raise ItsdbError(
            'Table does not exist at {}(.gz)'
            .format(tbl_filename)
        )

    return tbl_filename


@contextmanager
def _open_table(tbl_filename, encoding):
    path = _table_filename(tbl_filename)
    if path.endswith('.gz'):
        # gzip.open() cannot use mode='rt' until Python2.7 support
        # is gone; until then use TextIOWrapper
        gzfile = GzipFile(path, mode='r')
        gzfile.read1 = gzfile.read  # Python2 hack
        with TextIOWrapper(gzfile, encoding=encoding) as f:
            yield f
    else:
        with io.open(tbl_filename, encoding=encoding) as f:
            yield f


def _write_table(profile_dir, table_name, rows, fields,
                 append=False, gzip=False, encoding='utf-8'):
    # don't gzip if empty
    rows = iter(rows)
    try:
        first_row = next(rows)
    except StopIteration:
        gzip = False
    else:
        rows = chain([first_row], rows)

    if gzip and append:
        logging.warning('Appending to a gzip file may result in '
                        'inefficient compression.')

    if not os.path.exists(profile_dir):
        raise ItsdbError('Profile directory does not exist: {}'
                         .format(profile_dir))

    tbl_filename = os.path.join(profile_dir, table_name)
    gzfn = tbl_filename + '.gz'
    mode = 'a' if append else 'w'
    if gzip:
        # clean up non-gzip files, if any
        if os.path.isfile(tbl_filename):
            os.remove(tbl_filename)
        # text mode only from py3.3; until then use TextIOWrapper
        #mode += 't'  # text mode for gzip
        f = TextIOWrapper(GzipFile(gzfn, mode=mode), encoding=encoding)
    else:
        # clean up gzip files, if any
        if os.path.isfile(gzfn):
            os.remove(gzfn)
        f = io.open(tbl_filename, mode=mode, encoding=encoding)

    for row in rows:
        f.write(make_row(row, fields) + '\n')

    f.close()


def make_row(row, fields):
    """
    Encode a mapping of column name to values into a [incr tsdb()]
    profile line. The *fields* parameter determines what columns are
    used, and default values are provided if a column is missing from
    the mapping.

    Args:
        row: a mapping of column names to values
        fields: an iterable of :class:`Field` objects
    Returns:
        A [incr tsdb()]-encoded string
    """
    row_fields = []
    for f in fields:
        val = row.get(f.name, None)
        if val is None:
            val = str(f.default_value())
        row_fields.append(val)
    return encode_row(row_fields)


def select_rows(cols, rows, mode='list', cast=True):
    """
    Yield data selected from rows.

    It is sometimes useful to select a subset of data from a profile.
    This function selects the data in *cols* from *rows* and yields it
    in a form specified by *mode*. Possible values of *mode* are:

    ==============  =================  ============================
    mode            description        example `['i-id', 'i-wf']`
    ==============  =================  ============================
    list (default)  a list of values   `[10, 1]`
    dict            col to value map   `{'i-id': 10,'i-wf': 1}`
    row             [incr tsdb()] row  `'10@1'`
    ==============  =================  ============================

    Args:
        cols: an iterable of column names to select data for
        rows: the rows to select column data from
        mode: the form yielded data should take
        cast: if `True`, cast column values to their datatype
            (requires *rows* to be :class:`Record` objects)

    Yields:
        Selected data in the form specified by *mode*.
    """
    mode = mode.lower()
    if mode == 'list':
        modecast = lambda cols, data: data
    elif mode == 'dict':
        modecast = lambda cols, data: dict(zip(cols, data))
    elif mode == 'row':
        modecast = lambda cols, data: encode_row(data)
    else:
        raise ItsdbError('Invalid mode for select operation: {}\n'
                         '  Valid options include: list, dict, row'
                         .format(mode))
    for row in rows:
        if cast:
            try:
                data = [row.get(c, cast=True) for c in cols]
            except TypeError:
                data = [row.get(c) for c in cols]
        else:
            data = [row.get(c) for c in cols]
        yield modecast(cols, data)


def match_rows(rows1, rows2, key, sort_keys=True):
    """
    Yield triples of `(value, left_rows, right_rows)` where
    `left_rows` and `right_rows` are lists of rows that share the
    same column value for *key*.
    """
    matched = OrderedDict()
    for i, rows in enumerate([rows1, rows2]):
        for row in rows:
            val = row[key]
            try:
                data = matched[val]
            except KeyError:
                matched[val] = ([], [])
                data = matched[val]
            data[i].append(row)
    vals = matched.keys()
    if sort_keys:
        vals = sorted(vals, key=safe_int)
    for val in vals:
        left, right = matched[val]
        yield (val, left, right)


def join(table1, table2, on=None, how='inner', name=None):
    """
    Join two tables and return the resulting Table object.

    Fields in the resulting table have their names prefixed with their
    corresponding table name. For example, when joining `item` and
    `parse` tables, the `i-input` field of the `item` table will be
    named `item:i-input` in the resulting Table. Pivot fields (those
    in *on*) are only stored once without the prefix.

    Both inner and left joins are possible by setting the *how*
    parameter to `inner` and `left`, respectively.

    Args:
        table1 (:class:`Table`): the left table to join
        table2 (:class:`Table`): the right table to join
        on (str): the shared key to use for joining; if `None`, find
            shared keys using the schemata of the tables
        how (str): the method used for joining (`"inner"` or `"left"`)
        name (str): the name assigned to the resulting table
    """
    if how not in ('inner', 'left'):
        ItsdbError('Only \'inner\' and \'left\' join methods are allowed.')
    # validate and normalize the pivot
    on = _join_pivot(on, table1, table2)
    # the relation of the joined table
    relation = _RelationJoin(table1.fields, table2.fields, on=on)
    # get key mappings to the right side (useful for inner and left joins)
    get_key = lambda rec: tuple(rec.get(k) for k in on)
    key_indices = set(table2.fields.index(k) for k in on)
    right = defaultdict(list)
    for rec in table2:
        right[get_key(rec)].append([c for i, c in enumerate(rec)
                                    if i not in key_indices])
    # build joined table
    rfill = [f.default_value() for f in table2.fields if f.name not in on]
    joined = []
    for lrec in table1:
        k = get_key(lrec)
        if how == 'left' or k in right:
            joined.extend(lrec + rrec for rrec in right.get(k, [rfill]))

    return Table(relation.name, relation, joined)


def _join_pivot(on, table1, table2):
    if isinstance(on, stringtypes):
        on = _split_cols(on)
    if not on:
        on = set(table1.fields.keys()).intersection(table2.fields.keys())
        if not on:
            raise ItsdbError(
                'No shared key to join on in the \'{}\' and \'{}\' tables.'
                .format(table1.name, table2.name)
            )
    return sorted(on)


##############################################################################
# Deprecated

@deprecated(final_version='1.0.0', alternative='Relations.from_file(path)')
def get_relations(path):
    """
    Parse the relations file and return a Relations object that
    describes the database structure.

    **Note**: for backward-compatibility only; use Relations.from_file()

    Args:
        path: The path of the relations file.
    Returns:
        A dictionary mapping a table name to a list of Field tuples.

    .. deprecated:: v0.7.0
    """
    return Relations.from_file(path)


@deprecated(final_version='1.0.0', alternative='Field.default_value()')
def default_value(fieldname, datatype):
    """
    Return the default value for a column.

    If the column name (e.g. *i-wf*) is defined to have an idiosyncratic
    value, that value is returned. Otherwise the default value for the
    column's datatype is returned.

    Args:
        fieldname: the column name (e.g. `i-wf`)
        datatype: the datatype of the column (e.g. `:integer`)
    Returns:
        The default value for the column.

    .. deprecated:: v0.7.0
    """
    if fieldname in tsdb_coded_attributes:
        return str(tsdb_coded_attributes[fieldname])
    else:
        return _default_datatype_values.get(datatype, '')


@deprecated(final_version='1.0.0')
def make_skeleton(path, relations, item_rows, gzip=False):
    """
    Instantiate a new profile skeleton (only the relations file and
    item file) from an existing relations file and a list of rows
    for the item table. For standard relations files, it is suggested
    to have, as a minimum, the `i-id` and `i-input` fields in the
    item rows.

    Args:
        path: the destination directory of the skeleton---must not
              already exist, as it will be created
        relations: the path to the relations file
        item_rows: the rows to use for the item file
        gzip: if `True`, the item file will be compressed
    Returns:
        An ItsdbProfile containing the skeleton data (but the profile
        data will already have been written to disk).
    Raises:
        ItsdbError if the destination directory could not be created.

    .. deprecated:: v0.7.0
    """
    try:
        os.makedirs(path)
    except OSError:
        raise ItsdbError('Path already exists: {}.'.format(path))

    import shutil
    shutil.copyfile(relations, os.path.join(path, _relations_filename))
    prof = ItsdbProfile(path, index=False)
    prof.write_table('item', item_rows, gzip=gzip)
    return prof


@deprecated(final_version='1.0.0')
def filter_rows(filters, rows):
    """
    Yield rows matching all applicable filters.

    Filter functions have binary arity (e.g. `filter(row, col)`) where
    the first parameter is the dictionary of row data, and the second
    parameter is the data at one particular column.

    Args:
        filters: a tuple of (cols, filter_func) where filter_func will
            be tested (filter_func(row, col)) for each col in cols where
            col exists in the row
        rows: an iterable of rows to filter
    Yields:
        Rows matching all applicable filters

    .. deprecated:: v0.7.0
    """
    for row in rows:
        if all(condition(row, row.get(col))
               for (cols, condition) in filters
               for col in cols
               if col is None or col in row):
            yield row


@deprecated(final_version='1.0.0')
def apply_rows(applicators, rows):
    """
    Yield rows after applying the applicator functions to them.

    Applicators are simple unary functions that return a value, and that
    value is stored in the yielded row. E.g.
    `row[col] = applicator(row[col])`. These are useful to, e.g., cast
    strings to numeric datatypes, to convert formats stored in a cell,
    extract features for machine learning, and so on.

    Args:
        applicators: a tuple of (cols, applicator) where the applicator
            will be applied to each col in cols
        rows: an iterable of rows for applicators to be called on
    Yields:
        Rows with specified column values replaced with the results of
        the applicators

    .. deprecated:: v0.7.0
    """
    for row in rows:
        for (cols, function) in applicators:
            for col in (cols or []):
                value = row.get(col, '')
                row[col] = function(row, value)
        yield row


class ItsdbProfile(object):
    """
    A [incr tsdb()] profile, analyzed and ready for reading or writing.

    Args:
        path: The path of the directory containing the profile
        filters: A list of tuples [(table, cols, condition)] such
            that only rows in table where condition(row, row[col])
            evaluates to a non-false value are returned; filters are
            tested in order for a table.
        applicators: A list of tuples [(table, cols, function)]
            which will be used when reading rows from a table---the
            function will be applied to the contents of the column
            cell in the table. For each table, each column-function
            pair will be applied in order. Applicators apply after
            the filters.
        index: If `True`, indices are created based on the keys of
            each table.
        cast: if `True`, automatically cast data into the type defined
            by its relation field (e.g., :integer)

    .. deprecated:: v0.7.0
    """

    # _tables is a list of table names to consider (for indexing, writing,
    # etc.). If `None`, all present in the relations file and on disk are
    # considered. Otherwise, only those present in the list are considered.
    _tables = None

    @deprecated("The 'ItsdbProfile' class is deprecated "
                "and will be removed from version {version}; "
                "use the following instead: {alternative}",
                final_version='1.0.0',
                alternative='TestSuite')
    def __init__(self, path, relations=None,
                 filters=None, applicators=None, index=True,
                 cast=False, encoding='utf-8'):
        self.root = path
        self.cast = cast
        self.encoding = encoding

        # somewhat backwards-compatible resolution of relations file
        if isinstance(relations, dict):
            self.relations = relations
        else:
            if relations is None:
                relations = os.path.join(self.root, _relations_filename)
            self.relations = Relations.from_file(relations)

        if self._tables is None:
            self._tables = list(self.relations)

        self.filters = defaultdict(list)
        self.applicators = defaultdict(list)
        self._index = dict()

        for (table, cols, condition) in (filters or []):
            self.add_filter(table, cols, condition)

        for (table, cols, function) in (applicators or []):
            self.add_applicator(table, cols, function)

        if index:
            self._build_index()

    def add_filter(self, table, cols, condition):
        """
        Add a filter. When reading *table*, rows in *table* will be
        filtered by filter_rows().

        Args:
            table: The table the filter applies to.
            cols: The columns in *table* to filter on.
            condition: The filter function.
        """
        if table is not None and table not in self.relations:
            raise ItsdbError('Cannot add filter; table "{}" is not defined '
                             'by the relations file.'
                             .format(table))
        # this is a hack, though perhaps well-motivated
        if cols is None:
            cols = [None]
        self.filters[table].append((cols, condition))

    def add_applicator(self, table, cols, function):
        """
        Add an applicator. When reading *table*, rows in *table* will be
        modified by apply_rows().

        Args:
            table: The table to apply the function to.
            cols: The columns in *table* to apply the function on.
            function: The applicator function.
        """

        if table not in self.relations:
            raise ItsdbError('Cannot add applicator; table "{}" is not '
                             'defined by the relations file.'
                             .format(table))
        if cols is None:
            raise ItsdbError('Cannot add applicator; columns not specified.')
        fields = set(f.name for f in self.relations[table])
        for col in cols:
            if col not in fields:
                raise ItsdbError('Cannot add applicator; column "{}" not '
                                 'defined by the relations file.'
                                 .format(col))
        self.applicators[table].append((cols, function))

    def _build_index(self):
        self._index = {key: None for key, _ in _primary_keys}
        tables = self._tables
        if tables is not None:
            tables = set(tables)
        for (keyname, table) in _primary_keys:
            if table in tables:
                ids = set()
                try:
                    for row in self.read_table(table):
                        key = row[keyname]
                        ids.add(key)
                except ItsdbError:
                    logging.info('Failed to index {}.'.format(table))
                self._index[keyname] = ids

    def table_relations(self, table):
        if table not in self.relations:
            raise ItsdbError(
                'Table {} is not defined in the profiles relations.'
                .format(table)
            )
        return self.relations[table]

    def read_raw_table(self, table):
        """
        Yield rows in the [incr tsdb()] *table*. A row is a dictionary
        mapping column names to values. Data from a profile is decoded
        by decode_row(). No filters or applicators are used.
        """
        fields = self.table_relations(table) if self.cast else None
        field_names = [f.name for f in self.table_relations(table)]
        field_len = len(field_names)
        table_path = os.path.join(self.root, table)
        with _open_table(table_path, self.encoding) as tbl:
            for line in tbl:
                cols = decode_row(line, fields=fields)
                if len(cols) != field_len:
                    # should this throw an exception instead?
                    logging.error('Number of stored fields ({}) '
                                  'differ from the expected number({}); '
                                  'fields may be misaligned!'
                                  .format(len(cols), field_len))
                row = OrderedDict(zip(field_names, cols))
                yield row

    def read_table(self, table, key_filter=True):
        """
        Yield rows in the [incr tsdb()] *table* that pass any defined
        filters, and with values changed by any applicators. If no
        filters or applicators are defined, the result is the same as
        from ItsdbProfile.read_raw_table().
        """
        filters = self.filters[None] + self.filters[table]
        if key_filter:
            for f in self.relations[table]:
                key = f.name
                if f.key and (self._index.get(key) is not None):
                    ids = self._index[key]
                    # Can't keep local variables (like ids) in the scope of
                    # the lambda expression, so make it a default argument.
                    # Source: http://stackoverflow.com/a/938493/1441112
                    function = lambda r, x, ids=ids: x in ids
                    filters.append(([key], function))
        applicators = self.applicators[table]
        rows = self.read_raw_table(table)
        return filter_rows(filters, apply_rows(applicators, rows))

    def select(self, table, cols, mode='list', key_filter=True):
        """
        Yield selected rows from *table*. This method just calls
        select_rows() on the rows read from *table*.
        """
        if cols is None:
            cols = [c.name for c in self.relations[table]]
        rows = self.read_table(table, key_filter=key_filter)
        for row in select_rows(cols, rows, mode=mode):
            yield row

    def join(self, table1, table2, key_filter=True):
        """
        Yield rows from a table built by joining *table1* and *table2*.
        The column names in the rows have the original table name
        prepended and separated by a colon. For example, joining tables
        'item' and 'parse' will result in column names like
        'item:i-input' and 'parse:parse-id'.
        """
        get_keys = lambda t: (f.name for f in self.relations[t] if f.key)
        keys = set(get_keys(table1)).intersection(get_keys(table2))
        if not keys:
            raise ItsdbError(
                'Cannot join tables "{}" and "{}"; no shared key exists.'
                .format(table1, table2)
            )
        key = keys.pop()
        # this join method stores the whole of table2 in memory, but it is
        # MUCH faster than a nested loop method. Most profiles will fit in
        # memory anyway, so it's a decent tradeoff
        table2_data = defaultdict(list)
        for row in self.read_table(table2, key_filter=key_filter):
            table2_data[row[key]].append(row)
        for row1 in self.read_table(table1, key_filter=key_filter):
            for row2 in table2_data.get(row1[key], []):
                joinedrow = OrderedDict(
                    [('{}:{}'.format(table1, k), v)
                     for k, v in row1.items()] +
                    [('{}:{}'.format(table2, k), v)
                     for k, v in row2.items()]
                )
                yield joinedrow

    def write_table(self, table, rows, append=False, gzip=False):
        """
        Encode and write out *table* to the profile directory.

        Args:
            table: The name of the table to write
            rows: The rows to write to the table
            append: If `True`, append the encoded rows to any existing
                data.
            gzip: If `True`, compress the resulting table with `gzip`.
                The table's filename will have `.gz` appended.
        """
        _write_table(self.root,
                     table,
                     rows,
                     self.table_relations(table),
                     append=append,
                     gzip=gzip,
                     encoding=self.encoding)

    def write_profile(self, profile_directory, relations_filename=None,
                      key_filter=True,
                      append=False, gzip=None):
        """
        Write all tables (as specified by the relations) to a profile.

        Args:
            profile_directory: The directory of the output profile
            relations_filename: If given, read and use the relations
                at this path instead of the current profile's
                relations
            key_filter: If True, filter the rows by keys in the index
            append: If `True`, append profile data to existing tables
                in the output profile directory
            gzip: If `True`, compress tables using `gzip`. Table
                filenames will have `.gz` appended. If `False`, only
                write out text files. If `None`, use whatever the
                original file was.
        """
        if relations_filename:
            src_rels = os.path.abspath(relations_filename)
            relations = get_relations(relations_filename)
        else:
            src_rels = os.path.abspath(os.path.join(self.root,
                                                    _relations_filename))
            relations = self.relations

        tgt_rels = os.path.abspath(os.path.join(profile_directory,
                                                _relations_filename))
        if not (os.path.isfile(tgt_rels) and src_rels == tgt_rels):
            with open(tgt_rels, 'w') as rel_fh:
                print(open(src_rels).read(), file=rel_fh)

        tables = self._tables
        if tables is not None:
            tables = set(tables)
        for table, fields in relations.items():
            if tables is not None and table not in tables:
                continue
            try:
                fn = _table_filename(os.path.join(self.root, table))
                _gzip = gzip if gzip is not None else fn.endswith('.gz')
                rows = list(self.read_table(table, key_filter=key_filter))
                _write_table(
                    profile_directory, table, rows, fields,
                    append=append, gzip=_gzip, encoding=self.encoding
                )
            except ItsdbError:
                logging.warning(
                    'Could not write "{}"; table doesn\'t exist.'.format(table)
                )
                continue

        self._cleanup(gzip=gzip)

    def exists(self, table=None):
        """
        Return True if the profile or a table exist.

        If *table* is `None`, this function returns True if the root
        directory exists and contains a valid relations file. If *table*
        is given, the function returns True if the table exists as a
        file (even if empty). Otherwise it returns False.
        """
        if not os.path.isdir(self.root):
            return False
        if not os.path.isfile(os.path.join(self.root, _relations_filename)):
            return False
        if table is not None:
            try:
                _table_filename(os.path.join(self.root, table))
            except ItsdbError:
                return False
        return True

    def size(self, table=None):
        """
        Return the size, in bytes, of the profile or *table*.

        If *table* is `None`, this function returns the size of the
        whole profile (i.e. the sum of the table sizes). Otherwise, it
        returns the size of *table*.

        Note: if the file is gzipped, it returns the compressed size.
        """
        size = 0
        if table is None:
            for table in self.relations:
                size += self.size(table)
        else:
            try:
                fn = _table_filename(os.path.join(self.root, table))
                size += os.stat(fn).st_size
            except ItsdbError:
                pass
        return size

    def _cleanup(self, gzip=None):
        for table in self.relations:
            txfn = os.path.join(self.root, table)
            gzfn = os.path.join(self.root, table + '.gz')
            if os.path.isfile(txfn) and os.path.isfile(gzfn):
                if gzip is True:
                    os.remove(txfn)
                elif gzip is False:
                    os.remove(gzfn)
                elif os.stat(txfn).st_mtime < os.stat(gzfn).st_mtime:
                    os.remove(txfn)
                else:
                    os.remove(gzfn)


class ItsdbSkeleton(ItsdbProfile):
    """
    A [incr tsdb()] skeleton, analyzed and ready for reading or writing.

    See :class:`ItsdbProfile` for initialization parameters.

    .. deprecated:: v0.7.0
    """

    _tables = tsdb_core_files

    @deprecated(final_version='1.0.0', alternative='TestSuite')
    def __init__(self, path, relations=None,
                 filters=None, applicators=None, index=True,
                 cast=False, encoding='utf-8'):
        super(ItsdbSkeleton, self).__init__(
            self,
            path,
            relations=relations,
            filters=filters,
            applicators=applicators,
            index=index,
            cast=cast,
            encoding=encoding
        )
