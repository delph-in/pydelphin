import os
import re
import gzip
import logging
from collections import defaultdict, namedtuple, OrderedDict
from delphin._exceptions import ItsdbError

##############################################################################
# Module variables

_relations_filename = 'relations'
_field_delimiter = '@'
_character_escapes = [
    (_field_delimiter, '\\s'),
    ('\n', '\\n'),
    ('\\', '\\\\')
]
_default_datatype_values = {
    ':integer': '-1'
}
_default_field_values = {
    'i-wf': '1'
}

##############################################################################
# Non-class (i.e. static) functions


Field = namedtuple('Field', ['name', 'datatype', 'key', 'other', 'comment'])


def get_relations(path):
    """
    Parse the relations file and return a dictionary describing the database
    structure.

    @param profile_directory: The directory where the relations file exists.
    @param relations_filename: The filename containing the database relations.
                               Defaults to 'relations'.
    """

    relations = defaultdict(list)
    table_re = re.compile(r'^(\w.+):$')
    field_re = re.compile(r'\s*(?P<name>\S+)'
                          r'(\s+(?P<props>[^#]+))?'
                          r'(\s*#\s*(?P<comment>.*)$)?')
    f = open(path)
    current_table = None
    for line in f:
        table_match = table_re.search(line)
        field_match = field_re.search(line)
        if table_match is not None:
            current_table = table_match.groups()[0]
        elif current_table is not None and field_match is not None:
            name = field_match.group('name')
            props = field_match.group('props').split()
            comment = field_match.group('comment')
            key = False
            if len(props) > 0:
                datatype = props.pop(0)
            if ':key' in props:
                key = True
                props.remove(':key')
            relations[current_table].append(
                Field(name, datatype, key, props, comment)
            )
    return relations


def decode_row(line):
    fields = line.split(_field_delimiter)
    return list(map(unescape, fields))


def encode_row(fields):
    return _field_delimiter.join(map(escape, map(str, fields)))


def escape(string):
    for char, esc in _character_escapes:
        string = string.replace(char, esc)
    return string


def unescape(string):
    for char, esc in _character_escapes:
        string = string.replace(esc, char)
    return string


def _write_table(profile_dir, table_name, rows, fields,
                 append=False, gzip=False):
    if gzip and append:
        logging.warning('Appending to a gzip file may result in '
                        'inefficient compression.')

    if not os.path.exists(profile_dir):
        raise ItsdbError('Profile directory does not exist: {}'
                         .format(profile_dir))

    tbl_filename = os.path.join(profile_dir, table_name)
    mode = 'a' if append else 'w'
    if gzip:
        mode += 't'  # text mode for gzip
        f = gzip.open(tbl_filename + '.gz', mode=mode)
    else:
        f = open(tbl_filename, mode=mode)

    for row in rows:
        f.write(make_row(row, fields) + '\n')

    f.close()


def make_row(row, fields):
    row_fields = [row.get(f.name, str(default_value(f.name, f.datatype)))
                  for f in fields]
    return encode_row(row_fields)


def default_value(fieldname, datatype):
    if fieldname in _default_field_values:
        return _default_field_values[fieldname]
    else:
        return _default_datatype_values.get(datatype, '')


def filter_rows(filters, rows):
    for row in rows:
        if all(condition(row, row.get(col))
               for (cols, condition) in filters
               for col in cols):
            yield row


def apply_rows(applicators, rows):
    for row in rows:
        for (cols, function) in applicators:
            for col in (cols or []):
                value = row.get(col, '')
                row[col] = function(row, value)
        yield row


##############################################################################
# Profile class

class TsdbProfile:
    """
    A [incr tsdb()] profile, analyzed and ready for reading or writing.

    Args:
      path: the path of the directory containing the profile
      filters: A list of tuples [(table, cols, condition)] such that only rows
        in table where condition(row) evaluates to a non-false value are
        returned; filters are tested in order for a table.
      applicators: A list of tuples [(table, cols, function)] which
        will be used when reading rows from a table---the function will
        be applied to the contents of the column cell in the table. For
        each table, each column-function pair will be applied in order.
        Applicators apply after the filters.
    """

    def __init__(self, path, filters=None, applicators=None):
        self.root = path
        self.relations = get_relations(os.path.join(self.root,
                                                    _relations_filename))

        self.filters = defaultdict(list)
        self.applicators = defaultdict(list)

        for (table, cols, condition) in (filters or []):
            self.add_filter(table, cols, condition)

        for (table, cols, function) in (applicators or []):
            self.add_applicator(table, cols, condition)

    def add_filter(self, table, cols, condition):
        if table not in self.relations:
            raise ItsdbError('Cannot add filter; table "{}" is not defined '
                             'by the relations file.'
                             .format(table))
        # this is a hack, though perhaps well-motivated
        if cols is None:
            cols = [None]
        self.filters[table].append((cols, condition))

    def add_applicator(self, table, cols, function):
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

    def table_fields(self, table_name):
        if table_name not in self.relations:
            raise ItsdbError(
                'Table {} is not defined in the profiles relations.'
                .format(table_name)
            )
        return self.relations[table_name]

    def _open_table(self, table_name):
        tbl_filename = os.path.join(self.root, table_name)
        if os.path.exists(tbl_filename):
            f = open(tbl_filename)
        elif os.path.exists(tbl_filename + '.gz'):
            f = gzip.open(tbl_filename + '.gz', mode='rt')
        else:
            raise ItsdbError(
                'Table {} does not exist at {}(.gz)'
                .format(table_name, tbl_filename)
            )
        return f

    def read_raw_table(self, table_name):
        """
        Iterate through the rows in the [incr tsdb()] table.
        """

        field_names = [f.name for f in self.table_fields(table_name)]
        field_len = len(field_names)
        with self._open_table(table_name) as table:
            for line in table:
                fields = decode_row(line)
                if len(fields) != field_len:
                    # should this throw an exception instead?
                    logging.error('Number of stored fields ({}) '
                                  'differ from the expected number({}); '
                                  'fields may be misaligned!'
                                  .format(len(fields), field_len))
                row = OrderedDict(zip(field_names, fields))
                yield row

    def read_table(self, table_name):
        """
        Iterate through the rows in the [incr tsdb()] table, yielding
        only rows that pass any filters, and changed by any applicators.
        """
        filters = self.filters[table_name]
        applicators = self.applicators[table_name]
        rows = self.read_raw_table(table_name)
        return filter_rows(filters, apply_rows(applicators, rows))

    def select(self, table, cols, mode='list'):
        """
        Return the data from the specified table and columns.

        Args:
          table: The data to read data from. Only one table is allowed.
          cols: A list of columns to read data from. If None, returns
                all columns in relations-file order.
          mode: How to return the data. Options:

            ==============  ==================  ========================
                 mode          description      example ['i-id', 'i-wf']
            ==============  ==================  ========================
            list (default)  a list of values    [10, 1]
            dict            col to value map    {'i-id':'10','i-wf':'1'}
            row             [incr tsdb()] row   '10@1'
            ==============  ==================  ========================

        Returns:
          A generator of data for each row in table. The data structure
          is specified by the `mode` parameter.
        """
        mode = mode.lower()
        if mode == 'list':
            cast = lambda cols, data: data
        elif mode == 'dict':
            cast = lambda cols, data: dict(zip(cols, data))
        elif mode == 'row':
            cast = lambda cols, data: encode_row(data)
        else:
            raise ItsdbError('Invalid mode for select operation: {}\n'
                             '  Valid options include: list, dict, row'
                             .format(mode))
        if cols is None:
            cols = [c.name for c in self.relations[table]]
        for row in self.read_table(table):
            data = [row.get(c) for c in cols]
            yield cast(cols, data)

    def write_table(self, table_name, rows, append=False, gzip=False):
        _write_table(self.root,
                     table_name,
                     rows,
                     self.fields(table_name),
                     append=append,
                     gzip=gzip)

    def write_profile(self, profile_directory, relations_filename=None,
                      append=False, gzip=False):
        """
        Using self.relations as a schema, write the profile data out to
        the specified profile directory.

        @param profile_directory: The directory where the profile will
            be written.
        @param relations_file: If specified, provides an alternative
            relations file for the profile to be written.
        """
        import shutil
        if relations_filename:
            relations = get_relations(relations_filename)
        else:
            relations = self.relations
        shutil.copyfile(relations_filename,
                        os.path.join(profile_directory, _relations_filename))
        for table_name, fields in relations.items():
            # don't create new empty files if they didn't already exist
            # (likely was a skeleton rather than a profile)
            if not os.path.exists(os.path.join(self.root, table_name)):
                continue
            rows = self.read_table(table_name)
            _write_table(profile_directory, table_name, rows, fields,
                         append=append, gzip=gzip)