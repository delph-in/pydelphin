
"""
PyDelphin API counterparts to the `delphin` commands.

The public functions in this module largely mirror the front-end
subcommands provided by the `delphin` command, with some small changes
to argument names or values to be better-suited to being called from
within Python.
"""

import sys
import os
import json
from functools import partial
import logging
import warnings

from delphin import itsdb, tsql
from delphin.lnk import Lnk
from delphin.semi import SemI, load as load_semi
from delphin import semops
from delphin.util import safe_int, SExpr
from delphin.exceptions import PyDelphinException


###############################################################################
### CONVERT ###################################################################

_FORMAT_MAP = {
    'simplemrs': 'mrs',
    'ace': 'mrs',
    'mrx': 'mrs',
    'mrs-json': 'mrs',
    'indexed-mrs': 'mrs',
    'mrs-prolog': 'mrs',
    'dmrx': 'dmrs',
    'dmrs-json': 'dmrs',
    'dmrs-penman': 'dmrs',
    'simpledmrs': 'dmrs',
    'dmrs-tikz': 'dmrs',
    'eds': 'eds',
    'eds-json': 'eds',
    'eds-penman': 'eds'
}


def convert(path, source_fmt, target_fmt, select='result:mrs',
            properties=True, color=False, indent=None,
            show_status=False, predicate_modifiers=False,
            semi=None):
    """
    Convert between various DELPH-IN Semantics representations.

    Args:
        path (str, file): filename, testsuite directory, open file, or
            stream of input representations
        source_fmt (str): convert from this format
        target_fmt (str): convert to this format
        select (str): TSQL query for selecting data (ignored if *path*
            is not a testsuite directory; default: `"result:mrs"`)
        properties (bool): include morphosemantic properties if `True`
            (default: `True`)
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
    if source_fmt.startswith('eds') and not target_fmt.startswith('eds'):
        raise ValueError(
            'Conversion from EDS to non-EDS currently not supported.')

    if indent is not True and indent is not False and indent is not None:
        indent = safe_int(indent)

    if len(tsql.inspect_query('select ' + select)['projection']) != 1:
        raise ValueError('Exactly 1 column must be given in selection query: '
                         '(e.g., result:mrs)')

    if semi is not None and not isinstance(semi, SemI):
        assert os.path.isfile(semi)
        # lets ignore the SEM-I warnings until the questions are resolved
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            semi = load_semi(semi)

    loads = _get_codec(source_fmt)
    dumps = _get_codec(target_fmt, load=False)
    converter = _get_converter(source_fmt, target_fmt)

    # read
    kwargs = {}
    if source_fmt == 'indexedmrs' and semi is not None:
        kwargs['semi'] = semi
    if path is None:
        xs = loads(sys.stdin.read(), **kwargs)
    elif hasattr(path, 'read'):
        xs = loads(path.read(), **kwargs)
    elif os.path.isdir(path):
        ts = itsdb.TestSuite(path)
        xs = [
            next(iter(loads(r[0], **kwargs)), None)
            for r in tsql.select(select, ts)
        ]
    else:
        xs = loads(open(path, 'r').read(), **kwargs)

    if converter:
        xs = map(converter, xs)

    # write
    kwargs = {}
    if indent: kwargs['indent'] = indent
    if target_fmt == 'eds':
        kwargs['show_status'] = show_status
    # if target_fmt.startswith('eds'):
    #     kwargs['predicate_modifiers'] = predicate_modifiers
    if target_fmt == 'indexedmrs' and semi is not None:
        kwargs['semi'] = semi
    kwargs['properties'] = properties

    # this is not a great way to improve robustness when converting
    # many representations, but it'll do until v1.0.0. Also, it only
    # improves robustness on the output, not the input.
    # Note that all the code below is to replace the following:
    #     return dumps(xs, **kwargs)
    head, joiner, tail = _get_output_details(target_fmt)
    parts = []
    if indent is not None:
        joiner = joiner.strip() + '\n'
    def _trim(s):
        if head and s.startswith(head):
            s = s[len(head):].lstrip('\n')
        if tail and s.endswith(tail):
            s = s[:-len(tail)].rstrip('\n')
        return s
    for x in xs:
        try:
            s = dumps([x], **kwargs)
        except (PyDelphinException, KeyError, IndexError):
            logging.exception('could not convert representation')
        else:
            s = _trim(s)
            parts.append(s)
    # set these after so head and tail are used correctly in _trim
    if indent is not None:
        if head:
            head += '\n'
        if tail:
            tail = '\n' + tail

    output = head + joiner.join(parts) + tail

    if color and target_fmt == 'simplemrs':
        output = _colorize(output)

    return output


def _get_codec(codec, load=True):
    if codec == 'simplemrs':
        from delphin.mrs import simplemrs
        return simplemrs.loads if load else simplemrs.dumps

    elif codec == 'ace' and load:
        return _read_ace_parse

    elif codec == 'mrx':
        from delphin.mrs import mrx
        return mrx.loads if load else mrx.dumps

    elif codec == 'mrs-json':
        from delphin.mrs import mrsjson
        return mrsjson.loads if load else mrsjson.dumps

    elif codec == 'indexedmrs':
        from delphin.mrs import indexedmrs
        return indexedmrs.loads if load else indexedmrs.dumps

    elif codec == 'mrs-prolog' and not load:
        from delphin.mrs import mrsprolog
        return mrsprolog.dumps

    elif codec == 'dmrx':
        from delphin.dmrs import dmrx
        return dmrx.loads if load else dmrx.dumps

    elif codec == 'dmrs-json':
        from delphin.dmrs import dmrsjson
        return dmrsjson.loads if load else dmrsjson.dumps

    elif codec == 'dmrs-penman':
        from delphin.dmrs import dmrspenman
        return dmrspenman.loads if load else dmrspenman.dumps

    elif codec == 'simpledmrs':
        from delphin.dmrs import simpledmrs
        return simpledmrs.loads if load else simpledmrs.dumps

    elif codec == 'dmrs-tikz' and not load:
        from delphin.extra import latex
        return latex.dmrs_tikz_dependency

    elif codec == 'eds-json':
        from delphin.eds import edsjson
        return edsjson.loads if load else edsjson.dumps

    elif codec == 'eds-penman':
        from delphin.eds import edspenman
        return edspenman.loads if load else edspenman.dumps

    elif codec == 'eds':
        from delphin.eds import edsnative
        return edsnative.loads if load else edsnative.dumps

    elif load:
        raise ValueError('invalid source format: ' + codec)
    else:
        raise ValueError('invalid target format: ' + codec)


def _get_converter(source_fmt, target_fmt):
    src = _FORMAT_MAP[source_fmt]
    tgt = _FORMAT_MAP[target_fmt]
    converter = None
    if (src, tgt) == ('mrs', 'dmrs'):
        from delphin.dmrs import from_mrs as converter
    elif (src, tgt) == ('dmrs', 'mrs'):
        from delphin.mrs import from_dmrs as converter
    return converter


def _get_output_details(codec):
    if codec == 'mrx':
        return ('<mrs-list', '', '</mrs-list>')

    elif codec == 'dmrx':
        return ('<dmrs-list>', '', '</dmrs-list>')

    elif codec in ('mrs-json', 'dmrs-json', 'eds-json'):
        return ('[', ',', ']')

    else:
        return ('', ' ', '')


# read simplemrs from ACE output

def _read_ace_parse(s):
    from delphin.mrs import simplemrs
    if hasattr(s, 'decode'):
        s = s.decode('utf-8')
    surface = None
    newline = False
    for line in s.splitlines():
        if line.startswith('SENT: '):
            surface = line[6:]
        # regular ACE output
        elif line.startswith('['):
            m = line.partition(' ;  ')[0].strip()
            m = simplemrs.decode(m)
            m.surface = surface
            yield m
        # with --tsdb-stdout
        elif line.startswith('('):
            while line:
                data, remainder = SExpr.parse(line)
                line = remainder.lstrip()
                if len(data) == 2 and data[0] == ':results':
                    for result in data[1]:
                        for key, val in result:
                            if key == ':mrs':
                                yield simplemrs.decode(val)
        elif line == '\n':
            if newline:
                surface = None
                newline = False
            else:
                newline = True
        else:
            pass


def _colorize(text):
    from pygments import highlight as hl
    from pygments.formatters import TerminalFormatter
    from delphin.extra.highlight import SimpleMrsLexer, mrs_colorscheme
    lexer = SimpleMrsLexer()
    formatter = TerminalFormatter(bg='dark', colorscheme=mrs_colorscheme)
    return hl(text, lexer, formatter)


###############################################################################
### SELECT ####################################################################

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
        testsuite = itsdb.TestSuite(testsuite)
    return tsql.select(dataspec, testsuite, mode=mode, cast=cast)


###############################################################################
### MKPROF ####################################################################

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
    # basic validation
    if skeleton and full:
        raise ValueError("'skeleton' is incompatible with 'full'")
    elif skeleton and in_place:
        raise ValueError("'skeleton' is incompatible with 'in_place'")
    elif in_place and source is not None:
        raise ValueError("'in_place' is incompatible with 'source'")
    if in_place:
        source = destination
    if full and (source is None or not os.path.isdir(source)):
        raise ValueError("'full' must be used with a source testsuite")
    if relations is None and source is not None and os.path.isdir(source):
        relations = os.path.join(source, 'relations')
    elif relations is None or not os.path.isfile(relations):
        raise ValueError('invalid or missing relations file: {}'
                         .format(relations))
    # setup destination testsuite
    os.makedirs(destination, exist_ok=True)
    dts = itsdb.TestSuite(path=destination, relations=relations)
    # input is sentences on stdin
    if source is None:
        dts.write({'item': _lines_to_rows(sys.stdin, dts.relations)},
                  gzip=gzip)
    # input is sentence file
    elif os.path.isfile(source):
        with open(source) as fh:
            dts.write({'item': _lines_to_rows(fh, dts.relations)},
                      gzip=gzip)
    # input is source testsuite
    elif os.path.isdir(source):
        sts = itsdb.TestSuite(source)
        tables = dts.relations.tables if full else itsdb.tsdb_core_files
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
        path = os.path.join(destination, filename)
        if os.path.isfile(path):
            stat = os.stat(path)
            print(fmt.format(stat.st_size, filename))
        elif os.path.isfile(path + '.gz'):
            stat = os.stat(path + '.gz')
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
### PROCESS ###################################################################

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
    from delphin.interfaces import ace

    if generate and transfer:
        raise ValueError("'generate' is incompatible with 'transfer'")
    if source is None:
        source = testsuite
    if select is None:
        select = 'result:mrs' if (generate or transfer) else 'item:i-input'
    if generate:
        processor = ace.AceGenerator
    elif transfer:
        processor = ace.AceTransferer
    else:
        if not all_items:
            select += ' where i-wf != 2'
        processor = ace.AceParser
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
### REPP ######################################################################


def repp(file, config=None, module=None, active=None,
         format=None, trace_level=0):
    """
    Tokenize with a Regular Expression PreProcessor (REPP).

    Results are printed directly to stdout. If more programmatic
    access is desired, the :mod:`delphin.repp` module provides a
    similar interface.

    Args:
        file (str, file): filename, open file, or stream of sentence
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

    if hasattr(file, 'read'):
        for line in file:
            _repp(r, line, format, trace_level)
    else:
        with open(file, encoding='utf-8') as fh:
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
### COMPARE ###################################################################

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
    from delphin.mrs import simplemrs
    from delphin.semops import isomorphism

    if not isinstance(testsuite, itsdb.TestSuite):
        testsuite = itsdb.TestSuite(testsuite)
    if not isinstance(gold, itsdb.TestSuite):
        gold = itsdb.TestSuite(gold)

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
        (test_unique, shared, gold_unique) = semops.compare_bags(
            [simplemrs.decode(row[2]) for row in testrows],
            [simplemrs.decode(row[2]) for row in goldrows])
        yield {'id': key,
               'input': i_inputs[key],
               'test': test_unique,
               'shared': shared,
               'gold': gold_unique}
