
"""
PyDelphin API counterparts to the ``delphin`` commands.
"""

from typing import Union, Iterator, IO, Dict, Any
import sys
from pathlib import Path
import tempfile
import logging
import warnings

from progress.bar import Bar as ProgressBar

from delphin import exceptions
from delphin import tsdb, itsdb, tsql
from delphin.lnk import Lnk
from delphin.semi import SemI, load as load_semi
from delphin import util
from delphin.exceptions import PyDelphinException
# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401


logger = logging.getLogger(__name__)


# EXCEPTIONS ##################################################################

class CommandError(exceptions.PyDelphinException):
    """Raised on an invalid command call."""


###############################################################################
# CONVERT #####################################################################

def convert(path: Union[util.PathLike, IO[str]],
            source_fmt: str,
            target_fmt: str,
            select: str = 'result.mrs',
            properties: bool = True,
            lnk: bool = True,
            color: bool = False,
            indent: int = None,
            show_status: bool = False,
            predicate_modifiers: bool = False,
            semi: Union[SemI, util.PathLike] = None) -> str:
    """
    Convert between various DELPH-IN Semantics representations.

    If *source_fmt* ends with `"-lines"`, then *path* must be an
    input file containing one representation per line to be read with
    the :func:`decode` function of the source codec. If *target_fmt*
    ends with `"-lines"`, then any :attr:`HEADER`, :attr:`JOINER`,
    or :attr:`FOOTER` defined by the target codec are ignored. The
    *source_fmt* and *target_fmt* arguments are then downcased and
    hyphens are removed to normalize the codec name.

    Note:

        For syntax highlighting, `delphin.highlight`_ must be
        installed, and it is only available for select target formats.

        .. _delphin.highlight: https://github.com/delph-in/delphin.highlight

    Args:
        path (str, ~pathlib.Path, open file): filename, testsuite
            directory, open file, or stream of input representations
        source_fmt (str): convert from this format
        target_fmt (str): convert to this format
        select (str): TSQL query for selecting data (ignored if *path*
            is not a testsuite directory; default: `"result:mrs"`)
        properties (bool): include morphosemantic properties if `True`
            (default: `True`)
        lnk (bool): include lnk surface alignments and surface strings
            if `True` (default: `True`)
        color (bool): apply syntax highlighting if `True` and
            *target_fmt* is `"simplemrs"` (default: `False`)
        indent (int): specifies an explicit number of spaces
            for indentation
        show_status (bool): show disconnected EDS nodes (ignored if
            *target_fmt* is not `"eds"`; default: `False`)
        predicate_modifiers (bool): apply EDS predicate modification
            for certain kinds of patterns (ignored if *target_fmt* is
            not an EDS format; default: `False`)
        semi: a :class:`delphin.semi.SemI` object or path to a SEM-I
            (ignored if *target_fmt* is not ``indexedmrs``)
    Returns:
        str: the converted representation
    """
    if path is None:
        path = sys.stdin

    # normalize codec names
    source_fmt, source_lines = _parse_format_name(source_fmt)
    target_fmt, target_lines = _parse_format_name(target_fmt)
    # process other arguments
    highlight = _get_highlighter(color, target_fmt)
    source_codec = _get_codec(source_fmt)
    target_codec = _get_codec(target_fmt)
    converter = _get_converter(source_codec, target_codec, predicate_modifiers)

    if len(tsql.inspect_query('select ' + select)['projection']) != 1:
        raise CommandError(
            'Exactly 1 column must be given in selection query: '
            '(e.g., result.mrs)')

    if semi is not None and not isinstance(semi, SemI):
        # lets ignore the SEM-I warnings until questions regarding
        # valid SEM-Is are resolved
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            semi = load_semi(semi)

    # read
    kwargs: Dict[str, Any] = {}
    if source_fmt == 'indexedmrs' and semi is not None:
        kwargs['semi'] = semi
    if source_lines:
        xs = _read_lines(path, source_codec, kwargs)
    else:
        xs = _read(path, source_codec, select, kwargs)

    # convert if source representation != target representation
    xs = _iter_convert(converter, xs)

    # write
    kwargs = {}
    if indent:
        kwargs['indent'] = indent
    if target_fmt == 'eds':
        kwargs['show_status'] = show_status
    if target_fmt == 'indexedmrs' and semi is not None:
        kwargs['semi'] = semi
    kwargs['properties'] = properties
    kwargs['lnk'] = lnk
    # Manually dealing with headers, joiners, and footers is to
    # accommodate streaming output. Otherwise it is the same as
    # calling the following:
    #     target_codec.dumps(xs, **kwargs)
    if target_lines:
        header = footer = ''
        joiner = '\n'
    else:
        header = getattr(target_codec, 'HEADER', '')
        joiner = getattr(target_codec, 'JOINER', ' ')
        footer = getattr(target_codec, 'FOOTER', '')
        if indent is not None:
            if header:
                header += '\n'
            joiner = joiner.strip() + '\n'
            if footer:
                footer = '\n' + footer

    parts = []
    for x in xs:
        try:
            s = target_codec.encode(x, **kwargs)
        except (PyDelphinException, KeyError, IndexError):
            logger.exception('could not convert representation')
        else:
            parts.append(s)

    output = highlight(header + joiner.join(parts) + footer)

    return output


def _parse_format_name(name):
    name = name.lower()
    lines = False
    if name.endswith('-lines'):
        lines = True
        name = name[:-6]
    name = name.replace('-', '')
    return name, lines


def _get_highlighter(color, target_fmt):
    if color and target_fmt in ('simplemrs', 'simple-mrs'):
        highlight = util.make_highlighter('simplemrs')
    else:
        highlight = str
    return highlight


def _get_codec(name):
    try:
        codec = util.import_codec(name)
    except KeyError as exc:
        raise CommandError(f'invalid codec: {name}') from exc
    return codec


def _get_converter(source_codec, target_codec, predicate_modifiers):
    src_rep = source_codec.CODEC_INFO['representation'].lower()
    tgt_rep = target_codec.CODEC_INFO['representation'].lower()

    # The following could be done dynamically by inspecting if the
    # target representation has a from_{src_rep} function, but that
    # seems like overkill, and it's not clear what to do about
    # EDS's predicate_modifiers argument in that case.

    if (src_rep, tgt_rep) == ('mrs', 'dmrs'):
        from delphin.dmrs import from_mrs

        def converter(m):
            return from_mrs(m, representative_priority=None)

    elif (src_rep, tgt_rep) == ('dmrs', 'mrs'):
        from delphin.mrs import from_dmrs as converter

    elif (src_rep, tgt_rep) == ('mrs', 'eds'):
        from delphin.eds import from_mrs

        def converter(m):
            return from_mrs(m, predicate_modifiers=predicate_modifiers)

    elif src_rep == tgt_rep:
        converter = None

    else:
        raise CommandError(
            f'{src_rep.upper()} -> {tgt_rep.upper()}'
            ' conversion is not supported')

    return converter


def _read(path, source_codec, select, kwargs):
    if hasattr(path, 'read'):
        xs = list(source_codec.load(path, **kwargs))
    else:
        path = Path(path).expanduser()
        if path.is_dir():
            db = tsdb.Database(path)
            # ts = itsdb.TestSuite(path)
            xs = [
                next(iter(source_codec.loads(r[0], **kwargs)), None)
                for r in tsql.select(select, db)
            ]
        else:
            xs = list(source_codec.load(path, **kwargs))
    yield from xs


def _read_lines(path, source_codec, kwargs):
    if hasattr(path, 'read'):
        yield from _read_file(path, source_codec, kwargs)
    else:
        path = Path(path).expanduser()
        with path.open() as fh:
            yield from _read_file(fh, source_codec, kwargs)


def _read_file(fh, source_codec, kwargs):
    for line in fh:
        yield source_codec.decode(line, **kwargs)


def _iter_convert(converter, xs):
    if not converter:
        logger.info('no conversion necessary')
        for i, x in enumerate(xs, 1):
            logger.debug('item %d: %r', i, x)
            yield x
    else:
        logger.info('converting...')
        for i, x in enumerate(xs, 1):
            logger.debug('item %d: %r', i, x)
            try:
                yield converter(x)
            except PyDelphinException:
                logger.error('could not convert item %d', i)


###############################################################################
# SELECT ######################################################################

def select(query: str, path: util.PathLike, record_class=None):
    """
    Select data from [incr tsdb()] test suites.

    Args:
        query (str): TSQL select query (e.g., `'i-id i-input mrs'` or
            `'* from item where readings > 0'`)
        path (str, ~pathlib.Path): path to a TSDB test suite
        record_class: alternative class for records in the selection
    Yields:
        selected data from the test suite
    """
    db = tsdb.Database(path, autocast=True)
    return tsql.select(query, db, record_class=record_class)


###############################################################################
# MKPROF ######################################################################

def mkprof(destination, source=None, schema=None, where=None, delimiter=None,
           refresh=False, skeleton=False, full=False, gzip=False, quiet=False):
    """
    Create [incr tsdb()] profiles or skeletons.

    Data for the testsuite may come from an existing testsuite or from
    a list of sentences. There are four main usage patterns:

    - ``source="testsuite/"`` -- read data from `testsuite/`
    - ``source=None, refresh=True`` -- read data from *destination*
    - ``source=None, refresh=False`` -- read sentences from stdin
    - ``source="sents.txt"`` -- read sentences from `sents.txt`

    The latter two require the *schema* parameter.

    Args:
        destination (str, ~pathlib.Path): path of the new testsuite
        source (str, ~pathlib.Path): path to a source testsuite or a
            file containing sentences; if not given and *refresh* is
            `False`, sentences are read from stdin
        schema (str, ~pathlib.Path): path to a relations file to use
            for the created testsuite; if `None` and *source* is a
            test suite, the schema of *source* is used
        where (str): TSQL condition to filter records by; ignored if
            *source* is not a testsuite
        delimiter (str): if given, split lines from *source* or stdin
            on the character *delimiter*; if *delimiter* is `"@"`,
            split using :func:`delphin.tsdb.split`; a header line
            with field names is required; ignored when the data source
            is not text lines
        refresh (bool): if `True`, rewrite the data at *destination*;
            implies *full* is `True`; ignored if *source* is not
            `None`, best combined with *schema* or *gzip* (default:
            `False`)
        skeleton (bool): if `True`, only write tsdb-core files
            (default: `False`)
        full (bool): if `True`, copy all data from the source
            testsuite; ignored if the data source is not a testsuite
            or if *skeleton* is `True` (default: `False`)
        gzip (bool): if `True`, non-empty tables will be compressed
            with gzip
        quiet (bool): if `True`, don't print summary information
    """
    destination = Path(destination).expanduser()
    if source is not None:
        source = Path(source).expanduser()
    if schema is not None:
        schema = tsdb.read_schema(schema)
    old_relation_files = []

    # work in-place on destination test suite
    if source is None and refresh:
        db = tsdb.Database(destination)
        old_relation_files = list(db.schema)
        tsdb.write_database(db, db.path, schema=schema, gzip=gzip)

    # input is sentences on stdin or a file of sentences
    elif source is None and not refresh:
        _mkprof_from_lines(
            destination, sys.stdin, schema, delimiter, gzip)
    elif source.is_file():
        with source.open() as fh:
            _mkprof_from_lines(
                destination, fh, schema, delimiter, gzip)

    # input is source testsuite
    elif source.is_dir():
        db = tsdb.Database(source)
        old_relation_files = list(db.schema)
        _mkprof_from_database(
            destination, db, schema, where, full, gzip)

    else:
        raise CommandError(f'invalid source for mkprof: {source!s}')

    _mkprof_cleanup(destination, skeleton, old_relation_files)

    if not quiet:
        _mkprof_summarize(destination, tsdb.read_schema(destination))


def _mkprof_from_lines(destination, stream, schema, delimiter, gzip):
    if not schema:
        raise CommandError(
            'a schema is required to make a testsuite from text')

    lineiter = iter(stream)
    colnames, split = _make_split(delimiter, lineiter)

    # setup destination testsuite
    tsdb.initialize_database(destination, schema, files=True)

    tsdb.write(destination,
               'item',
               _lines_to_records(lineiter, colnames, split, schema['item']),
               fields=schema['item'],
               gzip=gzip)


def _lines_to_records(lineiter, colnames, split, fields):

    with_i_id = with_i_length = False
    for field in fields:
        if field.name == 'i-id':
            with_i_id = True
        elif field.name == 'i-length':
            with_i_length = True

    i_ids = set()
    for i, line in enumerate(lineiter, 1):
        colvals = split(line.rstrip('\n'))
        if len(colvals) != len(colnames):
            raise CommandError(
                'line values do not match expected fields:\n'
                f'  fields: {", ".join(colnames)}\n'
                f'  values: {", ".join(colvals)}')
        colmap = dict(zip(colnames, colvals))

        if with_i_id:
            if 'i-id' not in colmap:
                colmap['i-id'] = i
            if colmap['i-id'] in i_ids:
                raise CommandError(f'duplicate i-id: {colmap["i-id"]}')
            i_ids.add(colmap['i-id'])

        if with_i_length and 'i-length' not in colmap and 'i-input' in colmap:
            colmap['i-length'] = len(colmap['i-input'].split())

        yield tsdb.make_record(colmap, fields)


def _make_split(delimiter, lineiter):

    if not delimiter:

        def split(line):
            return (0, line[1:]) if line.startswith('*') else (1, line)

        colnames = ('i-wf', 'i-input')

    else:
        if delimiter == '@':
            split = tsdb.split
        else:

            def split(line):
                return line.split(delimiter)

        colnames = split(next(lineiter).rstrip('\n'))

    return colnames, split


def _mkprof_from_database(destination, db, schema, where, full, gzip):
    if schema is None:
        schema = db.schema

    destination.mkdir(exist_ok=True)
    tsdb.write_schema(destination, schema)

    to_copy = set(schema if full else tsdb.TSDB_CORE_FILES)
    where = '' if not where else 'where ' + where

    for table in schema:
        if table not in to_copy or _no_such_relation(db, table):
            records = []
        elif where:
            # filter the data, but use all if the query fails
            # (e.g., if the filter and table cannot be joined)
            try:
                records = _tsql_distinct(
                    tsql.select(f'* from {table} {where}', db))
            except tsql.TSQLError:
                records = list(db[table])
        else:
            records = list(db[table])
        tsdb.write(destination,
                   table,
                   records,
                   schema[table],
                   gzip=gzip)


def _no_such_relation(db, name):
    """
    Return True if the relation *name* is not defined in *db* or does
    not exist, otherwise False.
    """
    if name not in db:
        return True
    try:
        tsdb.get_path(db.path, name)
    except tsdb.TSDBError:
        return True
    return False


def _tsql_distinct(records):
    distinct = []
    prev = None
    for record in records:
        if record != prev:
            distinct.append(record)
        prev = record
    return distinct


def _mkprof_cleanup(destination, skeleton, old_files):
    schema = tsdb.read_schema(destination)
    to_keep = set(schema)
    if skeleton:
        to_keep = to_keep.intersection(tsdb.TSDB_CORE_FILES)
    for name in set(schema).union(old_files):
        tx_path = destination.joinpath(name).with_suffix('')
        gz_path = destination.joinpath(name).with_suffix('.gz')
        if (tx_path.is_file()
            and (name not in to_keep
                 or (skeleton and tx_path.stat().st_size == 0))):
            tx_path.unlink()
        if (gz_path.is_file()
            and (name not in to_keep
                 or (skeleton and gz_path.stat().st_size == 0))):
            gz_path.unlink()


def _mkprof_summarize(destination, schema):
    # summarize what was done
    isatty = sys.stdout.isatty()

    def _red(s):
        return f'\x1b[1;31m{s}\x1b[0m' if isatty else s

    fmt = '{:>8} bytes\t{}'
    for filename in ['relations'] + list(schema):
        path = destination.joinpath(filename)
        if path.is_file():
            stat = path.stat()
            print(fmt.format(stat.st_size, filename))
        elif path.with_suffix('.gz').is_file():
            stat = path.with_suffix('.gz').stat()
            print(fmt.format(stat.st_size, _red(filename + '.gz')))


###############################################################################
# PROCESS #####################################################################

def process(grammar, testsuite, source=None, select=None,
            generate=False, transfer=False, full_forest=False,
            options=None, all_items=False, result_id=None, gzip=False,
            stderr=None, report_progress=True):
    """
    Process the [incr tsdb()] profile *testsuite* with *grammar*.

    Inputs are read from *source* and results are written to
    *testsuite*. If *source* is `None`, it is set to *testsuite*. It
    is common for *source* to be `None` in parsing tasks, but it is
    not recommended for transfer or generation because the MRS field
    is both read from and written to for these tasks. If *source*
    points to a valid [incr tsdb()] profile and *testsuite* is a path
    to a non-existing location, the profile directory is created at
    that path.

    The default task is parsing, but generation is done if *generate*
    is `True` and transfer is done if *transfer* is `True`; only
    one or neither may be `True`. Input data is extracted from
    *source* using the TSQL query *select*. If *select* is `None`, the
    default depends on the task:

        ==========  =========================
        Task        Default value of *select*
        ==========  =========================
        Parsing     ``item.i-input``
        Transfer    ``result.mrs``
        Generation  ``result.mrs``
        ==========  =========================

    Args:
        grammar (str, ~pathlib.Path): path to a compiled grammar image
        testsuite (str, ~pathlib.Path): path to the destination [incr
            tsdb()] testsuite
        source (str, ~pathlib.Path): path to the source [incr tsdb()]
            testsuite; if `None`, *testsuite* is used as the source of
            data
        select (str): TSQL query for selecting processor inputs
            (default depends on the processor type)
        generate (bool): if `True`, generate instead of parse
            (default: `False`)
        transfer (bool): if `True`, transfer instead of parse
            (default: `False`)
        options (list): list of ACE command-line options to use when
            invoking the ACE subprocess; unsupported options will
            give an error message
        all_items (bool): if `True`, don't exclude ignored items
            (those with ``i-wf==2``) when parsing
        result_id (int): if given, only select inputs with the
            specified ``result-id`` (transfer and generation)
        gzip (bool): if `True`, non-empty tables will be compressed
            with gzip
        stderr (file): stream for ACE's stderr
        report_progress (bool): print a progress bar to stderr if
            `True` and logging verbosity is at WARNING or lower;
            (default: `True`)
    """
    from delphin import ace

    grammar = Path(grammar).expanduser()
    testsuite = Path(testsuite).expanduser()

    if not grammar.is_file():
        raise CommandError(f'{grammar} is not a file')

    kwargs = {}
    kwargs['stderr'] = stderr
    if sum(1 if mode else 0 for mode in (generate, transfer, full_forest)) > 1:
        raise CommandError("'generate', 'transfer', and 'full-forest' "
                           "are mutually exclusive")

    if source is None:
        source = _validate_tsdb(testsuite)
    else:
        source = _validate_tsdb(source)
        if not tsdb.is_database_directory(testsuite):
            if testsuite.exists():
                raise CommandError(
                    f'{testsuite} exists and is not a TSDB database; '
                    'remove it or select a different destination path')
            mkprof(testsuite, source=source, full=False, quiet=True)
        else:
            pass  # both source and testsuite are valid TSDB databases

    if select is None:
        select = 'result.mrs' if (generate or transfer) else 'item.i-input'
    if generate:
        processor = ace.ACEGenerator
    elif transfer:
        processor = ace.ACETransferer
    else:
        if full_forest:
            kwargs['full_forest'] = True
        if not all_items:
            select += ' where i-wf != 2'
        processor = ace.ACEParser
    if result_id is not None:
        select += f' where result-id == {result_id}'

    target = itsdb.TestSuite(testsuite)
    column, relation, condition = _interpret_selection(select, source)

    with tempfile.TemporaryDirectory() as dir:
        # use a temporary test suite directory for filtered inputs
        mkprof(dir, source=source, where=condition,
               full=True, gzip=True, quiet=True)
        tmp = itsdb.TestSuite(dir)

        process_kwargs = {'selector': (relation, column),
                          'source': tmp,
                          'gzip': gzip}
        bar = None
        if (report_progress
                and len(tmp[relation])
                and not logger.isEnabledFor(logging.INFO)):
            bar = ProgressBar('Processing', max=len(tmp[relation]))
            process_kwargs['callback'] = lambda _: bar.next()

        with processor(grammar, cmdargs=options, **kwargs) as cpu:
            target.process(cpu, **process_kwargs)
            if bar:
                bar.finish()


def _interpret_selection(select, source):
    schema = tsdb.read_schema(source)
    queryobj = tsql.inspect_query('select ' + select)
    projection = queryobj['projection']
    if projection == '*' or len(projection) != 1:
        raise CommandError("select query must return a single column")
    relation, _, column = projection[0].rpartition('.')
    if not relation:
        # query could be 'i-input from item' instead of 'item.i-input'
        if len(queryobj['relations']) == 1:
            relation = queryobj['relations'][0]
        elif len(queryobj['relations']) > 1:
            raise CommandError(
                "select query may specify no more than 1 relation")
        # otherwise guess
        else:
            relation = next(
                (table for table in schema
                 if any(f.name == column for f in schema[table])),
                None)

    if relation not in schema:
        raise CommandError('invalid or missing relation in query')
    elif not any(f.name == column for f in schema[relation]):
        raise CommandError(f'invalid column in query: {column}')

    try:
        condition = select[select.index(' where ') + 7:]
    except ValueError:
        condition = ''
    return column, relation, condition


###############################################################################
# REPP ########################################################################


def repp(source, config=None, module=None, active=None,
         format=None, color=False, trace_level=0):
    """
    Tokenize with a Regular Expression PreProcessor (REPP).

    Results are printed directly to stdout. If more programmatic
    access is desired, the :mod:`delphin.repp` module provides a
    similar interface.

    Args:
        source (str, ~pathlib.Path, open file): filename, open file,
            or stream of sentence inputs
        config (str, ~pathlib.Path): path to a PET REPP configuration
            (.set) file
        module (str, ~pathlib.Path): path to a top-level REPP module;
            other modules are found by external group calls
        active (list): select which modules are active; if `None`, all
            are used; incompatible with *config* (default: `None`)
        format (str): the output format (`"yy"`, `"string"`, `"line"`,
            or `"triple"`; default: `"yy"`)
        color (bool): apply syntax highlighting if `True` (default:
            `False`)
        trace_level (int): if `0` no trace info is printed; if `1`,
            applied rules are printed, if greater than `1`, both
            applied and unapplied rules (in order) are printed
            (default: `0`)
    """
    from delphin.repp import REPP, REPPResult

    if color:
        highlight = util.make_highlighter('diff')
    else:
        highlight = str

    if config is not None and module is not None:
        raise CommandError("cannot specify both 'config' and 'module'")
    if config is not None and active:
        raise CommandError("'active' cannot be used with 'config'")
    if config:
        r = REPP.from_config(config)
    elif module:
        r = REPP.from_file(module, active=active)
    else:
        r = REPP()  # just tokenize

    def _repp(line):
        line = line.rstrip('\n')
        if trace_level > 0:
            for step in r.trace(line, verbose=True):
                if isinstance(step, REPPResult):
                    print(f'Done:{step.string}')
                elif hasattr(step.operation, 'pattern'):
                    if step.applied:
                        print('Applied:', step.operation)
                        print(highlight(f'-{step.input}\n+{step.output}'))
                    elif trace_level > 1:
                        print('Did not apply:', step.operation)
        else:
            step = r.apply(line)
        res = r.tokenize_result(step)
        if format == 'yy':
            print(res)
        elif format == 'string':
            print(' '.join(t.form for t in res.tokens))
        elif format == 'line':
            for t in res.tokens:
                print(t.form)
            print()
        elif format == 'triple':
            for t in res.tokens:
                if t.lnk.type == Lnk.CHARSPAN:
                    cfrom, cto = t.lnk.data
                else:
                    cfrom, cto = -1, -1
                print(f'({cfrom}, {cto}, {t.form})')
            print()

    if hasattr(source, 'read'):
        for line in source:
            _repp(line)
    else:
        source = Path(source).expanduser()
        with source.open(encoding='utf-8') as fh:
            for line in fh:
                _repp(line)


###############################################################################
# COMPARE #####################################################################

def compare(testsuite: Union[util.PathLike, itsdb.TestSuite],
            gold: Union[util.PathLike, itsdb.TestSuite],
            select: str = 'i-id i-input mrs') -> Iterator[Dict]:
    """
    Compare two [incr tsdb()] profiles.

    Args:
        testsuite (str, ~pathlib.Path, TestSuite): path to the test
            [incr tsdb()] testsuite or a :class:`TestSuite` object
        gold (str, ~pathlib.Path, TestSuite): path to the gold
            [incr tsdb()] testsuite or a :class:`TestSuite` object
        select: TSQL query to select (id, input, mrs) triples
            (default: `'i-id i-input mrs'`)
    Yields:
        dict: Comparison results as::

            {"id": "item identifier",
             "input": "input sentence",
             "test": number_of_unique_results_in_test,
             "shared": number_of_shared_results,
             "gold": number_of_unique_results_in_gold}
    """
    from delphin import mrs
    from delphin.codecs import simplemrs

    if not isinstance(testsuite, itsdb.TestSuite):
        testsuite = itsdb.TestSuite(_validate_tsdb(testsuite))
    if not isinstance(gold, itsdb.TestSuite):
        gold = itsdb.TestSuite(_validate_tsdb(gold))

    queryobj = tsql.inspect_query('select ' + select)
    if len(queryobj['projection']) != 3:
        raise CommandError('select does not return 3 fields: ' + select)

    input_select = '{} {}'.format(queryobj['projection'][0],
                                  queryobj['projection'][1])
    # typing of tsql.select() is complicated right now, so just ignore
    # it for the following calls. it may be easier after
    # https://github.com/delph-in/pydelphin/issues/258
    i_inputs = dict(tsql.select(input_select, testsuite))  # type: ignore

    matched_rows = itsdb.match_rows(
        tsql.select(select, testsuite),  # type: ignore
        tsql.select(select, gold),       # type: ignore
        0)

    for (key, testrows, goldrows) in matched_rows:
        (test_unique, shared, gold_unique) = mrs.compare_bags(
            [simplemrs.decode(row[2]) for row in testrows],
            [simplemrs.decode(row[2]) for row in goldrows])
        yield {'id': key,
               'input': i_inputs.get(key),
               'test': test_unique,
               'shared': shared,
               'gold': gold_unique}


###############################################################################
# HELPERS #####################################################################

def _validate_tsdb(path):
    path = Path(path).expanduser()
    if not tsdb.is_database_directory(path):
        raise CommandError(f'{path} is not a valid TSDB database')
    return path
