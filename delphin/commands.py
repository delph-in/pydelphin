
"""
PyDelphin API counterparts to the `delphin` commands.

The public functions in this module largely mirror the front-end
subcommands provided by the `delphin` command, with some small changes
to argument names or values to be better-suited to being called from
within Python.
"""

import sys
import os
import io
import json
from functools import partial

from delphin import itsdb
from delphin.mrs import xmrs
from delphin.util import safe_int, SExpr


###############################################################################
### CONVERT ###################################################################

def convert(path, source_fmt, target_fmt, select='result:mrs',
            properties=True, show_status=False, predicate_modifiers=False,
            color=False, pretty_print=False, indent=None):
    """
    Convert between various DELPH-IN Semantics representations.

    Args:
        path (str, file): filename, testsuite directory, open file, or
            stream of input representations
        source_fmt (str): convert from this format
        target_fmt (str): convert to this format
        select (str): data-selector (ignored if *path* is not a
            testsuite directory; default: `"result:mrs"`)
        properties (bool): include morphosemantic properties if `True`
            (default: `True`)
        show_status (bool): show disconnected EDS nodes (ignored if
            *target_fmt* is not `"eds"`; default: `False`)
        predicate_modifiers (bool): apply EDS predicate modification
            for certain kinds of patterns (ignored if *target_fmt* is
            not an EDS format; default: `False`)
        color (bool): apply syntax highlighting if `True` and
            *target_fmt* is `"simplemrs"` (default: `False`)
        pretty_print (bool): if `True`, format the output with
            newlines and default indentation (default: `False`)
        indent (int, optional): specifies an explicit number of spaces
            for indentation (implies *pretty_print*)
    Returns:
        str: the converted representation
    """
    if source_fmt.startswith('eds') and not target_fmt.startswith('eds'):
        raise ValueError(
            'Conversion from EDS to non-EDS currently not supported.')

    if indent:
        pretty_print = True
        indent = 4 if indent is True else safe_int(indent)

    sel_table, sel_col = itsdb.get_data_specifier(select)
    if len(sel_col) != 1:
        raise ValueError('Exactly 1 column must be given in data selector '
                         '(e.g., result:mrs)')

    # read
    loads = _get_codec(source_fmt)
    if path is None:
        xs = loads(sys.stdin.read())
    elif hasattr(path, 'read'):
        xs = loads(path.read())
    elif os.path.isdir(path):
        p = itsdb.ItsdbProfile(path)
        xs = [
            next(iter(loads(r[0])), None)
            for r in p.select(sel_table, sel_col)
        ]
    else:
        xs = loads(open(path, 'r').read())

    # write
    dumps = _get_codec(target_fmt, load=False)
    kwargs = {}
    if color: kwargs['color'] = color
    if pretty_print: kwargs['pretty_print'] = pretty_print
    if indent: kwargs['indent'] = indent
    if target_fmt == 'eds':
        kwargs['pretty_print'] = pretty_print
        kwargs['show_status'] = show_status
    if target_fmt.startswith('eds'):
        kwargs['predicate_modifiers'] = predicate_modifiers
    kwargs['properties'] = properties

    return dumps(xs, **kwargs)


def _get_codec(codec, load=True):
    if codec == 'simplemrs':
        from delphin.mrs import simplemrs
        return simplemrs.loads if load else simplemrs.dumps

    elif codec == 'ace' and load:
        return _read_ace_parse

    elif codec == 'mrx':
        from delphin.mrs import mrx
        return mrx.loads if load else mrx.dumps

    elif codec == 'mrs-prolog' and not load:
        from delphin.mrs import prolog
        return prolog.dumps

    elif codec == 'dmrx':
        from delphin.mrs import dmrx
        return dmrx.loads if load else dmrx.dumps

    elif codec == 'simpledmrs' and not load:
        from delphin.mrs import simpledmrs
        return simpledmrs.dumps

    elif codec == 'dmrs-tikz' and not load:
        from delphin.extra import latex
        return latex.dmrs_tikz_dependency

    elif codec in ('mrs-json', 'dmrs-json', 'eds-json'):
        cls = {'mrs-json': _MRS_JSON,
               'dmrs-json': _DMRS_JSON,
               'eds-json': _EDS_JSON}[codec]
        return cls().loads if load else cls().dumps

    elif codec in ('dmrs-penman', 'eds-penman'):
        if codec == 'dmrs-penman':
            model = xmrs.Dmrs
        elif codec == 'eds-penman':
            from delphin.mrs.eds import Eds as model
        func = _penman_loads if load else _penman_dumps
        return partial(func, model=model)

    elif codec == 'eds':
        from delphin.mrs import eds
        return eds.loads if load else eds.dumps

    elif load:
        raise ValueError('invalid source format: ' + codec)
    else:
        raise ValueError('invalid target format: ' + codec)


# simulate json codecs for MRS and DMRS

class _MRS_JSON(object):
    CLS = xmrs.Mrs

    def getlist(self, o):
        if isinstance(o, dict):
            return [o]
        else:
            return o

    def load(self, f):
        return [self.CLS.from_dict(d) for d in self.getlist(json.load(f))]

    def loads(self, s):
        return [self.CLS.from_dict(d) for d in self.getlist(json.loads(s))]

    def dumps(self,
              xs,
              properties=True,
              pretty_print=False,
              indent=None,
              **kwargs):
        if pretty_print and indent is None:
            indent = 2
        return json.dumps(
            [
                self.CLS.to_dict(
                    (x if isinstance(x, self.CLS)
                       else self.CLS.from_xmrs(x, **kwargs)),
                    properties=properties) for x in xs
            ],
            indent=indent)


class _DMRS_JSON(_MRS_JSON):
    CLS = xmrs.Dmrs


class _EDS_JSON(_MRS_JSON):
    from delphin.mrs import eds
    CLS = eds.Eds


# load Penman module on demand

def _penman_loads(s, model=None, **kwargs):
    from delphin.mrs import penman
    return penman.loads(s, model=model, **kwargs)

def _penman_dumps(xs, model=None, **kwargs):
    from delphin.mrs import penman
    strings = []
    for x in xs:
        try:
            strings.append(penman.dumps([x], model=model, **kwargs))
        except penman.penman.EncodeError:
            logging.error('Invalid graph; possibly disconnected')
            strings.append('')
    return '\n'.join(strings)

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
            m = simplemrs.loads(m, single=True)
            m.surface = surface
            yield m
        # with --tsdb-stdout
        elif line.startswith('('):
            while line:
                expr = SExpr.parse(line)
                line = expr.remainder.lstrip()
                if len(expr.data) == 2 and expr.data[0] == ':results':
                    for result in expr.data[1]:
                        for key, val in result:
                            if key == ':mrs':
                                yield simplemrs.loads(val, single=True)
        elif line == '\n':
            if newline:
                surface = None
                newline = False
            else:
                newline = True
        else:
            pass


###############################################################################
### SELECT ####################################################################

def select(dataspec, testsuite, join=None,
           filters=None, applicators=None, mode='list'):
    """
    Select data from [incr tsdb()] profiles.

    Args:
        dataspec (str): data specifier for [incr tsdb()] profiles
            (e.g., `"parse:readings"` or `"result:mrs"`)
        testsuite (str, ItsdbProfile): testsuite or path to testsuite
            containing data to select
        join (tuple): 2-tuple of table names to join; the *dataspec*
            should then include the table name for all columns
            (e.g., `"parse:i-id@result:mrs"`)
        filters (list): see :class:`delphin.itsdb.ItsdbProfile` for a
            description of filters
        applicators (list): see :class:`delphin.itsdb.ItsdbProfile`
            for a description of applicators
        mode (str): see :meth:`delphin.itsdb.ItsdbProfile.select` for
            a description of the *mode* parameter
    Returns:
        a generator that yields selected data
    """
    if not isinstance(testsuite, itsdb.ItsdbProfile):
        assert os.path.isdir(testsuite)
        testsuite = _prepare_input_profile(
            testsuite, filters=filters, applicators=applicators)
    if join:
        tbl1, tbl2 = join
        rows = testsuite.join(tbl1, tbl2, key_filter=True)
        # Adding : is just for robustness. We need something like
        # :table:col@table@col, but may have gotten table:col@table@col
        if not dataspec.startswith(':'):
            dataspec = ':' + dataspec
        table, cols = itsdb.get_data_specifier(dataspec)
    else:
        table, cols = itsdb.get_data_specifier(dataspec)
        rows = testsuite.read_table(table, key_filter=True)

    return itsdb.select_rows(cols, rows, mode=mode)


###############################################################################
### MKPROF ####################################################################

def mkprof(destination, source=None, relations=None,
           filters=None, applicators=None,
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
        filters (list): see :class:`delphin.itsdb.ItsdbProfile` for a
            description of filters
        applicators (list): see :class:`delphin.itsdb.ItsdbProfile`
            for a description of applicators
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

    _prepare_output_directory(destination)
    o = itsdb.TestSuite(path=destination, relations=relations)
    # input is sentences on stdin
    if source is None:
        o.write({'item': _lines_to_rows(sys.stdin)}, gzip=gzip)
    # input is sentence file
    elif os.path.isfile(source):
        with open(source) as fh:
            o.write({'item': _lines_to_rows(fh)}, gzip=gzip)
    # input is profile
    elif os.path.isdir(source):
        p = _prepare_input_profile(
            source, filters=filters, applicators=applicators)
        if full:
            p.write_profile(
                destination,
                relations_filename=relations,
                key_filter=True,
                gzip=gzip)
        else:
            for table in itsdb.tsdb_core_files:
                if p.size(table) > 0:
                    o.write({table: p.read_table(table)}, gzip=gzip)
    o.reload()
    # unless a skeleton was requested, make empty files for other tables
    if not skeleton:
        for table in o.relations:
            if len(o[table]) == 0:
                o.write({table: []})

    # summarize what was done
    if sys.stdout.isatty():
        _red = lambda s: '\x1b[1;31m{}\x1b[0m'.format(s)
    else:
        _red = lambda s: s
    fmt = '{:>8} bytes\t{}'
    prof = itsdb.ItsdbProfile(destination, index=False)
    relations = prof.relations
    for filename in ['relations'] + list(relations.tables):
        f = os.path.join(destination, filename)
        if os.path.isfile(f):
            stat = os.stat(f)
            print(fmt.format(stat.st_size, filename))
        elif os.path.isfile(f + '.gz'):
            stat = os.stat(f + '.gz')
            print(fmt.format(stat.st_size, _red(filename + '.gz')))


def _lines_to_rows(lines):
    for i, line in enumerate(lines):
        i_id = i * 10
        i_wf = 0 if line.startswith('*') else 1
        i_input = line[1:].strip() if line.startswith('*') else line.strip()
        yield {'i-id': i_id, 'i-wf': i_wf, 'i-input': i_input}


###############################################################################
### PROCESS ###################################################################

def process(grammar, testsuite, source=None, selector=None,
            filters=None, applicators=None,
            generate=False, transfer=False,
            all_items=False, result_id=None):
    """
    Process (e.g., parse) a [incr tsdb()] profile.

    Results are written to directly to *testsuite*.

    Args:
        grammar (str): path to a compiled grammar image
        testsuite (str): path to a [incr tsdb()] testsuite where data
            will be read from (see *source*) and written to
        source (str): see :meth:`delphin.itsdb.TestSuite.process` for
            a description of *source*
        selector (str): see :meth:`delphin.itsdb.TestSuite.process`
            for a description of *selector*
        filters (list): see :class:`delphin.itsdb.ItsdbProfile` for a
            description of filters
        applicators (list): see :class:`delphin.itsdb.ItsdbProfile`
            for a description of applicators
        generate (bool): if `True`, generate instead of parse
            (default: `False`)
        transfer (bool): if `True`, transfer instead of parse
            (default: `False`)
        all_items (bool): if `True`, don't exclude ignored items
            (those with `i-wf==2`)
        result_id (int): if given, only keep items with the specified
            `result-id`
    """
    from delphin.interfaces import ace
    if generate and transfer:
        raise ValueError("'generate' is incompatible with 'transfer'")
    if source is None:
        source = testsuite
    if filters is None:
        filters = []
    if result_id is not None:
        filters.append(
            ('result', ['result-id'], lambda row, x: x == result_id))
    if generate:
        processor = ace.AceGenerator
    elif transfer:
        processor = ace.AceTransferer
    else:
        if not all_items:
            filters.append(
                ('item', ['i-wf'], lambda row, x: x != 2))
        processor = ace.AceParser

    source = _prepare_input_profile(
        source,
        filters=filters,
        applicators=applicators,
        cast=True)

    target = itsdb.TestSuite(testsuite)

    with processor(grammar) as cpu:
        target.process(cpu, selector, source=source)

    target.write()


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
        with io.open(file, encoding='utf-8') as fh:
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

def compare(testsuite, gold, filters=None, applicators=None):
    """
    Compare two [incr tsdb()] profiles.

    Any filters or applicators are applied to both the test and gold
    testsuites.

    Args:
        testsuite: path to the test [incr tsdb()] testsuite
        gold: path to the gold [incr tsdb()] testsuite
        filters (list): see :class:`delphin.itsdb.ItsdbProfile` for a
            description of filters
        applicators (list): see :class:`delphin.itsdb.ItsdbProfile`
            for a description of applicators
    Yields:
        dict: Comparison results as:

        ```python
        {"id": "item identifier",
         "input": "input sentence",
         "test": number_of_unique_results_in_test,
         "shared": number_of_shared_results,
         "gold": number_of_unique_results_in_gold}
        ```
    """
    from delphin.mrs import simplemrs, compare as mrs_compare

    test_profile = _prepare_input_profile(
        testsuite,
        filters=filters,
        applicators=applicators)
    gold_profile = _prepare_input_profile(
        gold,
        filters=filters,
        applicators=applicators)

    i_inputs = dict((row['parse:parse-id'], row['item:i-input'])
                    for row in test_profile.join('item', 'parse'))

    matched_rows = itsdb.match_rows(
        test_profile.read_table('result'), gold_profile.read_table('result'),
        'parse-id')
    for (key, testrows, goldrows) in matched_rows:
        (test_unique, shared, gold_unique) = mrs_compare.compare_bags(
            [simplemrs.loads_one(row['mrs']) for row in testrows],
            [simplemrs.loads_one(row['mrs']) for row in goldrows])
        yield {'id': key,
               'input': i_inputs[key],
               'test': test_unique,
               'shared': shared,
               'gold': gold_unique}


###############################################################################
### HELPER FUNCTIONS ##########################################################

def _prepare_input_profile(path, filters=None, applicators=None, cast=False):
    index = filters is not None and len(filters) > 0
    prof = itsdb.ItsdbProfile(
        path, filters=filters, applicators=applicators, index=index, cast=cast)
    return prof


def _prepare_output_directory(path):
    try:
        os.makedirs(path)  # exist_ok=True is available from Python 3.2
    except OSError as ex:  # PermissionError is available from Python 3.3
        if ex.errno == 17 and os.path.isdir(path):
            pass  # existing directory; maybe it's usable
        else:
            raise
