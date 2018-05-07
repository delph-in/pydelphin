#!/usr/bin/env python3

from __future__ import unicode_literals

import sys
import os
import io
import argparse
import warnings
import logging
import json
import textwrap
from functools import partial

from delphin.__about__ import __version__
from delphin.exceptions import PyDelphinWarning
from delphin.mrs import xmrs, eds
from delphin.mrs.components import Lnk
from delphin import itsdb
from delphin.repp import REPP


def main():
    args = parser.parse_args()

    if not hasattr(args, 'func'):
        sys.exit(parser.print_help())

    # global init
    if args.quiet:
        args.verbosity = 0
        sys.stdout.close()
        sys.stdout = open(os.devnull, 'w')

    logging.basicConfig(level=50 - (args.verbosity * 10))

    args.func(args)


def convert(args):
    """
    Convert between various MRS codecs or to export formats.
    """
    from delphin.mrs import (simplemrs, mrx, prolog, dmrx, eds, simpledmrs)
    from delphin.extra import latex
    codecs = {
        'simplemrs': (simplemrs.loads, simplemrs.dumps),
        'mrx': (mrx.loads, mrx.dumps),
        'dmrx': (dmrx.loads, dmrx.dumps),
        'eds': (eds.loads, eds.dumps),
        'mrs-json': (_mrs_json.loads, _mrs_json.dumps),
        'mrs-prolog': (None, prolog.dumps),
        'dmrs-json': (_dmrs_json.loads, _dmrs_json.dumps),
        'eds-json': (_eds_json.loads, _eds_json.dumps),
        'dmrs-penman': (partial(_penman_loads, model=xmrs.Dmrs),
                        partial(_penman_dumps, model=xmrs.Dmrs)),
        'eds-penman': (partial(_penman_loads, model=eds.Eds),
                       partial(_penman_dumps, model=eds.Eds)),
        'simpledmrs': (None, simpledmrs.dumps),
        'dmrs-tikz': (None, latex.dmrs_tikz_dependency)
    }
    decoders = set(k for k, cd in codecs.items() if cd[0])
    encoders = set(k for k, cd in codecs.items() if cd[1])

    # arg validation
    from_fmt = vars(args)['from']  # vars() to avoid syntax error
    if from_fmt not in decoders:
        sys.exit('Source format must be one of: {}'.format(
            ', '.join(sorted(decoders))))
    if args.to not in encoders:
        sys.exit('Source format must be one of: {}'.format(
            ', '.join(sorted(encoders))))
    if from_fmt.startswith('eds') and not args.to.startswith('eds'):
        sys.exit('Conversion from EDS to non-EDS currently not supported.')
    args.color = (args.color == 'always'
                  or (args.color == 'auto' and sys.stdout.isatty()))
    if args.color:
        try:
            import pygments
        except ImportError:
            warnings.warn(
                'Pygments is not installed; output will not be highlighted.',
                PyDelphinWarning
            )
            args.color = False
    if args.indent:
        args.pretty_print = True
        if args.indent.isdigit():
            args.indent = int(args.indent)
    sel_table, sel_col = itsdb.get_data_specifier(args.select)
    if len(sel_col) != 1:
        sys.exit(
            'Exactly 1 column must be given in --select (e.g., result:mrs)')

    # read
    loads = codecs[from_fmt][0]
    if args.PATH is not None:
        if os.path.isdir(args.PATH):
            p = itsdb.ItsdbProfile(args.PATH)
            xs = [
                next(iter(loads(r[0])), None)
                for r in p.select(sel_table, sel_col)
            ]
        else:
            xs = loads(open(args.PATH, 'r').read())
    else:
        xs = loads(sys.stdin.read())

    # write
    dumps = codecs[args.to][1]
    kwargs = {}
    if args.color: kwargs['color'] = args.color
    if args.pretty_print: kwargs['pretty_print'] = args.pretty_print
    if args.indent: kwargs['indent'] = args.indent
    kwargs['properties'] = not args.no_properties
    print(dumps(xs, **kwargs))
    # try:
    #     print(dumps(xs, **kwargs))
    # except TypeError:
    #     sys.exit('One or more parameters to {} are not supported: {}'.format(
    #         args.to, ', '.join(kwargs)))


def select(args):
    """
    Select data from [incr tsdb()] profiles.
    """
    in_profile = _prepare_input_profile(
        args.TESTSUITE, filters=args.filter, applicators=args.apply)
    if args.join:
        tbl1, tbl2 = map(str.strip, args.join.split(','))
        rows = in_profile.join(tbl1, tbl2, key_filter=True)
        # Adding : is just for robustness. We need something like
        # :table:col@table@col, but may have gotten table:col@table@col
        if not args.DATASPEC.startswith(':'):
            args.DATASPEC = ':' + args.DATASPEC
        table, cols = itsdb.get_data_specifier(args.DATASPEC)
    else:
        table, cols = itsdb.get_data_specifier(args.DATASPEC)
        rows = in_profile.read_table(table, key_filter=True)
    for row in itsdb.select_rows(cols, rows, mode='row'):
        print(row)


def mkprof(args):
    """
    Create [incr tsdb()] profiles or skeletons.
    """
    outdir = args.DEST
    if args.in_place:
        if args.skeleton:
            sys.exit('Creating a skeleton with --in-place is not allowed.')
        args.source = args.DEST
    if args.source:  # input is profile
        p = _prepare_input_profile(
            args.source,
            filters=args.filter,
            applicators=args.apply)
        relations = args.relations or os.path.join(p.root, 'relations')
    else:  # input is stdin or txt file
        p = None
        relations = args.relations

    if not os.path.isfile(relations):
        sys.exit('Invalid relations file: {}'.format(relations))

    if args.full:
        _prepare_output_directory(outdir)
        p.write_profile(
            outdir,
            relations_filename=relations,
            key_filter=True,
            gzip=args.gzip)
    else:
        rows = []
        if p is None:
            if args.input is not None:
                rows = _lines_to_rows(open(args.input))
            else:
                rows = _lines_to_rows(sys.stdin)
        o = itsdb.make_skeleton(outdir, relations, rows, gzip=args.gzip)
        if p is not None:
            for table in itsdb.tsdb_core_files:
                if p.size(table) > 0:
                    o.write_table(table, p.read_table(table))
        # unless a skeleton was requested, make empty files for other tables
        if not args.skeleton:
            for table in o.relations:
                if o.size(table) == 0:
                    o.write_table(table, [])

    # summarize what was done
    if sys.stdout.isatty():
        _red = lambda s: '\x1b[1;31m{}\x1b[0m'.format(s)
    else:
        _red = lambda s: s
    fmt = '{:>8} bytes\t{}'
    prof = itsdb.ItsdbProfile(outdir, index=False)
    relations = prof.relations
    for filename in ['relations'] + list(relations.tables):
        f = os.path.join(outdir, filename)
        if os.path.isfile(f):
            stat = os.stat(f)
            print(fmt.format(stat.st_size, filename))
        elif os.path.isfile(f + '.gz'):
            stat = os.stat(f + '.gz')
            print(fmt.format(stat.st_size, _red(filename + '.gz')))


def compare(args):
    """
    Compare two [incr tsdb()] profiles.
    """
    from delphin.mrs import simplemrs, compare as mrs_compare
    template = '{id}\t<{left},{shared},{right}>'
    if args.verbosity >= 1:
        template += '\t{string}'

    test_profile = _prepare_input_profile(
        args.TESTSUITE, filters=args.filter, applicators=args.apply)
    gold_profile = _prepare_input_profile(args.GOLD)

    i_inputs = dict((row['parse:parse-id'], row['item:i-input'])
                    for row in test_profile.join('item', 'parse'))

    matched_rows = itsdb.match_rows(
        test_profile.read_table('result'), gold_profile.read_table('result'),
        'parse-id')
    for (key, testrows, goldrows) in matched_rows:
        (test_unique, shared, gold_unique) = mrs_compare.compare_bags(
            [simplemrs.loads_one(row['mrs']) for row in testrows],
            [simplemrs.loads_one(row['mrs']) for row in goldrows])
        print(
            template.format(
                id=key,
                string=i_inputs[key],
                left=test_unique,
                shared=shared,
                right=gold_unique))


def repp(args):
    if args.config:
        r = REPP.from_config(args.config)
    elif args.m:
        r = REPP.from_file(args.m)
    else:
        r = REPP()  # just tokenize

    def do_repp(stream):
        if args.trace:
            do_trace(stream)
        else:
            do_tokenize(stream)

    def do_tokenize(stream):
        for line in stream:
            res = r.tokenize(line.rstrip('\n'))
            if args.format == 'yy':
                print(res)
            elif args.format == 'string':
                print(' '.join(t.form for t in res.tokens))
            elif args.format == 'line':
                for t in res.tokens:
                    print(t.form)
                print()
            elif args.format == 'triple':
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

    def do_trace(stream):
        for line in stream:
            for step in r.trace(line.rstrip('\n'), verbose=True):
                if not hasattr(step, 'applied'):
                    print('Done:{}'.format(step.string))
                    continue
                if step.applied == True or args.verbosity >= 2:
                    print('{}:{!s}\n   In:{}\n  Out:{}'.format(
                        'Applied' if step.applied else 'Did not apply',
                        step.operation, step.input, step.output))

    if args.FILE:
        with io.open(args.FILE, encoding='utf-8') as fh:
            do_repp(fh)
    else:
        do_repp(sys.stdin)

## Helper definitions

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
                    (x if isinstance(x, self.CLS) else self.CLS.from_xmrs(x)),
                    properties=properties) for x in xs
            ],
            indent=indent)


class _DMRS_JSON(_MRS_JSON):
    CLS = xmrs.Dmrs


class _EDS_JSON(_MRS_JSON):
    CLS = eds.Eds


_mrs_json = _MRS_JSON()
_dmrs_json = _DMRS_JSON()
_eds_json = _EDS_JSON()

# load Penman module on demand

def _penman_loads(s, model=None, **kwargs):
    from delphin.mrs import penman
    return penman.loads(s, model=model, **kwargs)

def _penman_dumps(x, model=None, **kwargs):
    from delphin.mrs import penman
    return penman.dumps(x, model=model, **kwargs)

# working with directories and profiles


def _prepare_input_profile(path, filters=None, applicators=None):
    flts = [_make_itsdb_action(*f.split('=', 1)) for f in (filters or [])]
    apls = [_make_itsdb_action(*f.split('=', 1)) for f in (applicators or [])]
    index = len(flts) > 0
    prof = itsdb.ItsdbProfile(
        path, filters=flts, applicators=apls, index=index)
    return prof


def _make_itsdb_action(data_specifier, function):
    table, cols = itsdb.get_data_specifier(data_specifier)
    function = eval('lambda row, x:{}'.format(function))
    return (table, cols, function)


def _prepare_output_directory(path):
    try:
        os.makedirs(path, exist_ok=True)
    except PermissionError:
        sys.exit('Permission denied to create output directory: {}'
                 .format(path))
    if not os.access(path, os.R_OK | os.W_OK):
        sys.exit('Cannot write to output directory: {}'.format(path))


def _lines_to_rows(lines):
    for i, line in enumerate(lines):
        i_id = i * 10
        i_wf = 0 if line.startswith('*') else 1
        i_input = line[1:].strip() if line.startswith('*') else line.strip()
        yield {'i-id': i_id, 'i-wf': i_wf, 'i-input': i_input}


# textwrap does not have indent() in Python2.7, so use this for now:
def redent(s):
    lines = textwrap.dedent(s).splitlines()
    if lines[0].strip() == '':
        lines = lines[1:]
    return '\n'.join('  ' + line for line in lines)


parser = argparse.ArgumentParser(
    prog='delphin',
    description='PyDelphin command-line interface',
)
parser.add_argument(
    '-V', '--version', action='version', version='%(prog)s ' + __version__)

# Arguments for all commands
common_parser = argparse.ArgumentParser(add_help=False)
common_parser.add_argument(
    '-v',
    '--verbose',
    action='count',
    dest='verbosity',
    default=1,
    help='increase verbosity')
common_parser.add_argument(
    '-q',
    '--quiet',
    action='store_true',
    help='suppress output on <stdout> and <stderr>')

# Arguments for commands that read profiles
profile_parser = argparse.ArgumentParser(add_help=False)
profile_parser.add_argument(
    '-a',
    '--apply',
    action='append',
    metavar='APL',
    help=('apply an expression to rows/cols in the test suite; APL '
          'is a string like \'table:col=expression\''))
profile_parser.add_argument(
    '-f',
    '--filter',
    action='append',
    metavar='CND',
    help=('keep rows satisfying a condition; CND is a string like '
          '\'table:col=expression\''))

# Arguments for the convert command
convert_parser = argparse.ArgumentParser(add_help=False)
convert_parser.set_defaults(func=convert)
convert_parser.add_argument(
    'PATH',
    nargs='?',
    help=('path to a file containing representations to convert, or '
          'a test suite directory from which result:mrs will be selected; '
          'if not given, <stdin> is read as though it were a file'))
convert_parser.add_argument(
    '-f',
    '--from',
    metavar='FMT',
    default='simplemrs',
    help='original representation (default: simplemrs)')
convert_parser.add_argument(
    '-t',
    '--to',
    metavar='FMT',
    default='simplemrs',
    help='target representation (default: simplemrs)')
convert_parser.add_argument(
    '--no-properties',
    action='store_true',
    help='suppress morphosemantic properties')
convert_parser.add_argument(
    '--pretty-print',
    action='store_true',
    help='format in a more human-readable way')
convert_parser.add_argument(
    '--indent',
    metavar='N',
    help='format with explicit indent N (implies --pretty-print)')
convert_parser.add_argument(
    '--color',
    metavar='WHEN',
    default='auto',
    help='(auto|always|never) use ANSI color (default: auto)')
convert_parser.add_argument(
    '--select',
    metavar='DATASPEC',
    default='result:mrs',
    help=('table:col data specifier; ignored if PATH does not point '
          'to a test suite directory (default: result:mrs)'))

# Arguments for the select command
select_parser = argparse.ArgumentParser(add_help=False)
select_parser.set_defaults(func=select)
select_parser.add_argument(
    'DATASPEC', help='table:col[@col...] data specifier (e.g. item:i-input)')
select_parser.add_argument(
    'TESTSUITE', help='path to the test suite directory to select data from')
select_parser.add_argument(
    '-j',
    '--join',
    help=('join two tables with a shared key (e.g. parse,result); '
          'the DATASPEC argument then requires explicit tables '
          '(e.g. parse:i-id@result:mrs)'))

# mkprof subparser
mkprof_parser = argparse.ArgumentParser(add_help=False)
mkprof_parser.set_defaults(func=mkprof)
mkprof_parser.add_argument(
    'DEST', help='directory for the destination (output) test suite')
mkprof_grp1 = mkprof_parser.add_mutually_exclusive_group()
mkprof_grp1.add_argument(
    '-s', '--source', metavar='DIR', help='path to a test suite directory')
mkprof_grp1.add_argument(
    '--in-place',
    action='store_true',
    help='use DEST as the --source (use caution)')
mkprof_grp1.add_argument(
    '-i',
    '--input',
    metavar='TXT',
    help='file of test sentences (* sents are ungrammatical)')
mkprof_parser.add_argument(
    '-r',
    '--relations',
    metavar='FILE',
    help='relations file to use for destination test suite')
mkprof_grp2 = mkprof_parser.add_mutually_exclusive_group()
mkprof_grp2.add_argument(
    '--full',
    action='store_true',
    help='write all tables (must be used with --source)')
mkprof_grp2.add_argument(
    '--skeleton',
    action='store_true',
    help='write only tsdb-core files for skeletons')
mkprof_parser.add_argument(
    '-z', '--gzip', action='store_true', help='compress table files with gzip')

# compare subparser
compare_parser = argparse.ArgumentParser(add_help=False)
compare_parser.set_defaults(func=compare)
compare_parser.add_argument(
    'TESTSUITE', help='path to the current test-suite directory')
compare_parser.add_argument(
    'GOLD', help='path to the gold test-suite directory')

# repp subparser
repp_parser = argparse.ArgumentParser(add_help=False)
repp_parser.set_defaults(func=repp)
repp_parser.add_argument(
    'FILE', nargs='?', help='an input file')
repp_group = repp_parser.add_mutually_exclusive_group()
repp_group.add_argument(
    '-c', '--config', metavar='PATH',
    help='a .set configuration file')
repp_group.add_argument(
    '-m', metavar='PATH', help='the main .rpp file')
repp_parser.add_argument(
    '-a', action='append', metavar='NAME',
    help='activate an external module')
repp_parser.add_argument(
    '-f', '--format',
    metavar='FMT',
    choices=('string', 'line', 'triple', 'yy'),
    default='yy',
    help='output token format')
repp_parser.add_argument(
    '--trace', action='store_true',
    help='print each step that modifies an input string')

subparser = parser.add_subparsers(title='commands')
subparser.add_parser('convert', parents=[common_parser, convert_parser])
subparser.add_parser(
    'select', parents=[common_parser, select_parser, profile_parser])
subparser.add_parser(
    'mkprof',
    parents=[common_parser, mkprof_parser, profile_parser],
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=redent("""
        This command creates test suites. There are four usage patterns:
            delphin mkprof --input=sentences.txt --relations=../relations ...
            delphin mkprof --relations=../relations ... < sentences.txt
            delphin mkprof --source=profile/ ...
            delphin mkprof --in-place ...
        The first two read sentences (one per line; '*' in the first column
        indicates ungrammaticality) from --input or <stdin> and --relations is
        is required. The second two use an existing profile; --relations
        defaults to the source profile's; --in-place reads and overwrites DEST.

        By default, test suites are skeletons as from the `mkprof` utility of
        `art`, where the 'item' and 'relations' files are non-empty but all
        other tables exist as empty files. The --full option, with --source,
        will copy a full profile, while the --skeleton option will only write
        the tsdb-core files (e.g., 'item') and 'relations' file.
        """))
subparser.add_parser(
    'compare', parents=[common_parser, compare_parser, profile_parser])
subparser.add_parser(
    'repp', parents=[common_parser, repp_parser])

if __name__ == '__main__':
    main()
