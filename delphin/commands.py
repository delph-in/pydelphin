
"""
PyDelphin API counterparts to the `delphin` commands.

The public functions in this module largely mirror the front-end
subcommands provided by the `delphin` command, with some small changes
to argument names or values to be better-suited to being called from
within Python.
"""

import sys
from pathlib import Path
import importlib
import logging
import warnings

from delphin import itsdb, tsql
from delphin.lnk import Lnk
from delphin.semi import SemI, load as load_semi
from delphin import util
from delphin.exceptions import PyDelphinException
import delphin.codecs


###############################################################################
# CONVERT #####################################################################

_CODECS = util.namespace_modules(delphin.codecs)


def convert(path, source_fmt, target_fmt, select='result:mrs',
            properties=True, lnk=True, color=False, indent=None,
            show_status=False, predicate_modifiers=False,
            semi=None):
    """
    Convert between various DELPH-IN Semantics representations.

    The *source_fmt* and *target_fmt* arguments are downcased and
    hyphens are removed to normalize the codec name.

    Args:
        path (str, file): filename, testsuite directory, open file, or
            stream of input representations
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
        indent (int, optional): specifies an explicit number of spaces
            for indentation
        show_status (bool): show disconnected EDS nodes (ignored if
            *target_fmt* is not `"eds"`; default: `False`)
        predicate_modifiers (bool): apply EDS predicate modification
            for certain kinds of patterns (ignored if *target_fmt* is
            not an EDS format; default: `False`)
        semi: a :class:`delphin.semi.SemI` object or path to a SEM-I
            (ignored if *target_fmt* is not `indexedmrs`)
    Returns:
        str: the converted representation
    """
    if path is None:
        path = sys.stdin

    # normalize codec names
    source_fmt = source_fmt.replace('-', '').lower()
    target_fmt = target_fmt.replace('-', '').lower()

    source_codec = _get_codec(source_fmt)
    target_codec = _get_codec(target_fmt)
    converter = _get_converter(source_codec, target_codec, predicate_modifiers)

    if indent is not True and indent is not False and indent is not None:
        indent = int(indent)

    if len(tsql.inspect_query('select ' + select)['projection']) != 1:
        raise ValueError('Exactly 1 column must be given in selection query: '
                         '(e.g., result:mrs)')

    if semi is not None and not isinstance(semi, SemI):
        # lets ignore the SEM-I warnings until questions regarding
        # valid SEM-Is are resolved
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            semi = load_semi(semi)

    # read
    kwargs = {}
    if source_fmt == 'indexedmrs' and semi is not None:
        kwargs['semi'] = semi

    if hasattr(path, 'read'):
        xs = list(source_codec.load(path, **kwargs))
    else:
        path = Path(path).expanduser()
        if path.is_dir():
            ts = itsdb.TestSuite(path)
            xs = [
                next(iter(source_codec.loads(r[0], **kwargs)), None)
                for r in tsql.select(select, ts)
            ]
        elif path.is_file():
            xs = list(source_codec.load(path, **kwargs))

    # convert if source representation != target representation
    if converter:
        xs = map(converter, xs)

    # write
    kwargs = {}
    if indent:
        kwargs['indent'] = indent
    if target_fmt == 'eds':
        kwargs['show_status'] = show_status
    # if target_fmt.startswith('eds'):
    #     kwargs['predicate_modifiers'] = predicate_modifiers
    if target_fmt == 'indexedmrs' and semi is not None:
        kwargs['semi'] = semi
    kwargs['properties'] = properties
    kwargs['lnk'] = lnk

    # Manually dealing with headers, joiners, and footers is to
    # accommodate streaming output. Otherwise it is the same as
    # calling the following:
    #     target_codec.dumps(xs, **kwargs)
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
            logging.exception('could not convert representation')
        else:
            parts.append(s)

    output = header + joiner.join(parts) + footer

    if color and target_fmt in ('simplemrs', 'simple-mrs'):
        output = _colorize(output)

    return output


def _get_codec(name):
    if name not in _CODECS:
        raise ValueError('invalid codec: {}'.format(name))
    fullname = _CODECS[name]
    codec = importlib.import_module(fullname)
    return codec


def _get_converter(source_codec, target_codec, predicate_modifiers):
    src_rep = source_codec.CODEC_INFO['representation'].lower()
    tgt_rep = target_codec.CODEC_INFO['representation'].lower()

    # The following could be done dynamically by inspecting if the
    # target representation has a from_{src_rep} function, but that
    # seems like overkill, and it's not clear what to do about
    # EDS's predicate_modifiers argument in that case.

    if (src_rep, tgt_rep) == ('mrs', 'dmrs'):
        from delphin.dmrs import from_mrs as converter

    elif (src_rep, tgt_rep) == ('dmrs', 'mrs'):
        from delphin.mrs import from_dmrs as converter

    elif (src_rep, tgt_rep) == ('mrs', 'eds'):
        from delphin.eds import from_mrs

        def converter(m):
            return from_mrs(m, predicate_modifiers=predicate_modifiers)

    elif src_rep == tgt_rep:
        converter = None

    else:
        raise ValueError('{} -> {} conversion is not supported'.format(
            src_rep.upper(), tgt_rep.upper()))

    return converter


def _colorize(text):
    from pygments import highlight as hl
    from pygments.formatters import Terminal256Formatter as Formatter
    from delphin.extra.highlight import SimpleMRSLexer, MRSStyle
    lexer = SimpleMRSLexer()
    formatter = Formatter(style=MRSStyle)
    return hl(text, lexer, formatter)


###############################################################################
# SELECT ######################################################################

def select(dataspec, testsuite, mode='list', cast=True):
    """
    Select data from [incr tsdb()] profiles.

    Args:
        query (str): TSQL select query (e.g., `'i-id i-input mrs'` or
            `'* from item where readings > 0'`)
        testsuite (str, TestSuite): testsuite or path to testsuite
            containing data to select
        mode (str): see :func:`delphin.itsdb.select_rows` for a
            description of the *mode* parameter (default: `list`)
        cast (bool): if `True`, cast column values to their datatype
            according to the relations file (default: `True`)
    Returns:
        a generator that yields selected data
    """
    if not isinstance(testsuite, itsdb.TestSuite):
        source = Path(testsuite).expanduser()
        testsuite = itsdb.TestSuite(source)
    return tsql.select(dataspec, testsuite, mode=mode, cast=cast)


###############################################################################
# MKPROF ######################################################################

def mkprof(destination, source=None, relations=None, where=None,
           in_place=False, skeleton=False, full=False, gzip=False):
    """
    Create [incr tsdb()] profiles or skeletons.

    Data for the testsuite may come from an existing testsuite or from
    a list of sentences. There are four main usage patterns:

        - `source="testsuite/"` -- read data from `testsuite/`
        - `source=None, in_place=True` -- read data from *destination*
        - `source=None, in_place=False` -- read sentences from stdin
        - `source="sents.txt"` -- read sentences from `sents.txt`

    For the latter two, the *relations* parameter must be specified.

    Args:
        destination (str): path of the new testsuite
        source (str): path to a source testsuite or a file containing
            sentences; if not given and *in_place* is `False`,
            sentences are read from stdin
        relations (str): path to a relations file to use for the
            created testsuite; if `None` and *source* is given, the
            relations file of the source testsuite is used
        where (str): TSQL condition to filter records by; ignored if
            *source* is not a testsuite
        in_place (bool): if `True` and *source* is not given, use
            *destination* as the source for data (default: `False`)
        skeleton (bool): if `True`, only write tsdb-core files
            (default: `False`)
        full (bool): if `True`, copy all data from the source
            testsuite (requires *source* to be a testsuite path;
            default: `False`)
        gzip (bool): if `True`, non-empty tables will be compressed
            with gzip
    """
    destination = Path(destination).expanduser()
    # basic validation
    if skeleton and full:
        raise ValueError("'skeleton' is incompatible with 'full'")
    elif skeleton and in_place:
        raise ValueError("'skeleton' is incompatible with 'in_place'")
    elif in_place and source is not None:
        raise ValueError("'in_place' is incompatible with 'source'")
    if in_place:
        source = destination
    elif source is not None:
        source = Path(source)
    if full and (source is None or not source.is_dir()):
        raise ValueError("'full' must be used with a source testsuite")
    if relations is not None:
        relations = Path(relations).expanduser()
    if relations is None and source is not None and source.is_dir():
        relations = source.joinpath('relations')
    if relations is None or not relations.is_file():
        raise ValueError('invalid or missing relations file: {}'
                         .format(relations))
    # setup destination testsuite
    destination.mkdir(parents=True, exist_ok=True)
    dts = itsdb.TestSuite(path=destination, relations=relations)
    # input is sentences on stdin
    if source is None:
        dts.write({'item': _lines_to_rows(sys.stdin, dts.relations)},
                  gzip=gzip)
    # input is sentence file
    elif source.is_file():
        with source.open() as fh:
            dts.write({'item': _lines_to_rows(fh, dts.relations)},
                      gzip=gzip)
    # input is source testsuite
    elif source.is_dir():
        sts = itsdb.TestSuite(source)
        tables = dts.relations.tables if full else itsdb.TSDB_CORE_FILES
        where = '' if where is None else 'where ' + where
        for table in tables:
            if sts.size(table) > 0:
                # filter the data, but use all if the query fails
                # (e.g., if the filter and table cannot be joined)
                try:
                    rows = tsql.select(
                        '* from {} {}'.format(table, where), sts, cast=False)
                except itsdb.ITSDBError:
                    rows = sts[table]
                dts.write({table: rows}, gzip=gzip)
    dts.reload()
    # unless a skeleton was requested, make empty files for other tables
    if not skeleton:
        for table in dts.relations:
            if len(dts[table]) == 0:
                dts.write({table: []})

    # summarize what was done
    if sys.stdout.isatty():
        _red = lambda s: '\x1b[1;31m{}\x1b[0m'.format(s)
    else:
        _red = lambda s: s
    fmt = '{:>8} bytes\t{}'
    for filename in ['relations'] + list(dts.relations.tables):
        path = destination.joinpath(filename)
        if path.is_file():
            stat = path.stat()
            print(fmt.format(stat.st_size, filename))
        elif path.with_suffix('.gz').is_file():
            stat = path.with_suffix('.gz').stat()
            print(fmt.format(stat.st_size, _red(filename + '.gz')))


def _lines_to_rows(lines, relations):
    # field indices only need to be computed once, so don't use
    # itsdb.Record.from_dict()
    i_id_idx = relations['item'].index('i-id')
    i_wf_idx = relations['item'].index('i-wf')
    i_input_idx = relations['item'].index('i-input')
    num_fields = len(relations['item'])

    def make_row(i_id, i_wf, i_input):
        row = [None] * num_fields
        row[i_id_idx] = i_id
        row[i_wf_idx] = i_wf
        row[i_input_idx] = i_input
        return itsdb.Record(relations['item'], row)

    for i, line in enumerate(lines):
        i_wf, i_input = (0, line[1:]) if line.startswith('*') else (1, line)
        yield make_row(i * 10, i_wf, i_input.strip())


###############################################################################
# PROCESS #####################################################################

def process(grammar, testsuite, source=None, select=None,
            generate=False, transfer=False, options=None,
            all_items=False, result_id=None, gzip=False):
    """
    Process (e.g., parse) a [incr tsdb()] profile.

    Results are written to directly to *testsuite*.

    If *select* is `None`, the defaults depend on the task:

        ==========  =========================
        Task        Default value of *select*
        ==========  =========================
        Parsing     `item:i-input`
        Transfer    `result:mrs`
        Generation  `result:mrs`
        ==========  =========================

    Args:
        grammar (str): path to a compiled grammar image
        testsuite (str): path to a [incr tsdb()] testsuite where data
            will be read from (see *source*) and written to
        source (str): path to a [incr tsdb()] testsuite; if `None`,
            *testsuite* is used as the source of data
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
            (those with `i-wf==2`) when parsing
        result_id (int): if given, only keep items with the specified
            `result-id`
        gzip (bool): if `True`, non-empty tables will be compressed
            with gzip
    """
    from delphin import ace

    grammar = Path(grammar).expanduser()
    testsuite = Path(testsuite).expanduser()

    if generate and transfer:
        raise ValueError("'generate' is incompatible with 'transfer'")
    if source is None:
        source = testsuite
    if select is None:
        select = 'result:mrs' if (generate or transfer) else 'item:i-input'
    if generate:
        processor = ace.ACEGenerator
    elif transfer:
        processor = ace.ACETransferer
    else:
        if not all_items:
            select += ' where i-wf != 2'
        processor = ace.ACEParser
    if result_id is not None:
        select += ' where result-id == {}'.format(result_id)

    source = itsdb.TestSuite(source)
    target = itsdb.TestSuite(testsuite)
    column, tablename, condition = _interpret_selection(select, source)
    table = itsdb.Table(
        source[tablename].fields,
        tsql.select(
            '* from {} {}'.format(tablename, condition),
            source,
            cast=False))

    with processor(grammar, cmdargs=options) as cpu:
        target.process(cpu, ':' + column, source=table, gzip=gzip)


def _interpret_selection(select, source):
    queryobj = tsql.inspect_query('select ' + select)
    projection = queryobj['projection']
    if projection == '*' or len(projection) != 1:
        raise ValueError("'select' must return a single column")
    tablename, _, column = projection[0].rpartition(':')
    if not tablename:
        # query could be 'i-input from item' instead of 'item:i-input'
        if len(queryobj['tables']) == 1:
            tablename = queryobj['tables'][0]
        # otherwise guess
        else:
            tablename = source.relations.find(column)[0]
    try:
        condition = select[select.index(' where ') + 1:]
    except ValueError:
        condition = ''
    return column, tablename, condition


###############################################################################
# REPP ########################################################################


def repp(source, config=None, module=None, active=None,
         format=None, trace_level=0):
    """
    Tokenize with a Regular Expression PreProcessor (REPP).

    Results are printed directly to stdout. If more programmatic
    access is desired, the :mod:`delphin.repp` module provides a
    similar interface.

    Args:
        source (str, file): filename, open file, or stream of sentence
            inputs
        config (str): path to a PET REPP configuration (.set) file
        module (str): path to a top-level REPP module; other modules
            are found by external group calls
        active (list): select which modules are active; if `None`, all
            are used; incompatible with *config* (default: `None`)
        format (str): the output format (`"yy"`, `"string"`, `"line"`,
            or `"triple"`; default: `"yy"`)
        trace_level (int): if `0` no trace info is printed; if `1`,
            applied rules are printed, if greather than `1`, both
            applied and unapplied rules (in order) are printed
            (default: `0`)
    """
    from delphin.repp import REPP

    if config is not None and module is not None:
        raise ValueError("cannot specify both 'config' and 'module'")
    if config is not None and active:
        raise ValueError("'active' cannot be used with 'config'")
    if config:
        r = REPP.from_config(config)
    elif module:
        r = REPP.from_file(module, active=active)
    else:
        r = REPP()  # just tokenize

    if hasattr(source, 'read'):
        for line in source:
            _repp(r, line, format, trace_level)
    else:
        source = Path(source).expanduser()
        with source.open(encoding='utf-8') as fh:
            for line in fh:
                _repp(r, line, format, trace_level)


def _repp(r, line, format, trace_level):
    if trace_level > 0:
        for step in r.trace(line.rstrip('\n'), verbose=True):
            if not hasattr(step, 'applied'):
                print('Done:{}'.format(step.string))
                continue
            if step.applied == True or trace_level > 1:
                print('{}:{!s}\n   In:{}\n  Out:{}'.format(
                    'Applied' if step.applied else 'Did not apply',
                    step.operation, step.input, step.output))
    res = r.tokenize(line.rstrip('\n'))
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
            print(
                '({}, {}, {})'
                .format(cfrom, cto, t.form)
            )
        print()


###############################################################################
# COMPARE #####################################################################

def compare(testsuite, gold, select='i-id i-input mrs'):
    """
    Compare two [incr tsdb()] profiles.

    Args:
        testsuite (str, TestSuite): path to the test [incr tsdb()]
            testsuite or a :class:`TestSuite` object
        gold (str, TestSuite): path to the gold [incr tsdb()]
            testsuite or a :class:`TestSuite` object
        select: TSQL query to select (id, input, mrs) triples
            (default: `i-id i-input mrs`)
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
        source = Path(testsuite).expanduser()
        testsuite = itsdb.TestSuite(source)
    if not isinstance(gold, itsdb.TestSuite):
        source = Path(gold).expanduser()
        gold = itsdb.TestSuite(source)

    queryobj = tsql.inspect_query('select ' + select)
    if len(queryobj['projection']) != 3:
        raise ValueError('select does not return 3 fields: ' + select)

    input_select = '{} {}'.format(queryobj['projection'][0],
                                  queryobj['projection'][1])
    i_inputs = dict(tsql.select(input_select, testsuite))

    matched_rows = itsdb.match_rows(
        tsql.select(select, testsuite),
        tsql.select(select, gold),
        0)

    for (key, testrows, goldrows) in matched_rows:
        (test_unique, shared, gold_unique) = mrs.compare_bags(
            [simplemrs.decode(row[2]) for row in testrows],
            [simplemrs.decode(row[2]) for row in goldrows])
        yield {'id': key,
               'input': i_inputs[key],
               'test': test_unique,
               'shared': shared,
               'gold': gold_unique}
