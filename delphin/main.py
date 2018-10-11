#!/usr/bin/env python3

from __future__ import unicode_literals

import sys
import os
import argparse
import logging
import textwrap

from delphin.__about__ import __version__
from delphin.exceptions import PyDelphinException, PyDelphinWarning
from delphin import itsdb

from delphin.commands import (
    convert, select, mkprof, process, compare, repp
)


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

    try:
        args.func(args)
    except (ValueError, PyDelphinException) as ex:
        sys.exit(str(ex))


def call_convert(args):
    color = (args.color == 'always' or
             (args.color == 'auto' and sys.stdout.isatty()))
    if color:
        try:
            import pygments
        except ImportError:
            warnings.warn(
                'Pygments is not installed; output will not be highlighted.',
                PyDelphinWarning
            )
            color = False
    print(convert(
        args.PATH,
        vars(args)['from'],  # vars() to avoid syntax error
        args.to,
        properties=(not args.no_properties),
        color=color,
        pretty_print=args.pretty_print or args.indent is not None,
        indent=args.indent,
        select=args.select,
        show_status=args.show_status,
        predicate_modifiers=args.predicate_modifiers))


def call_select(args):
    rows = select(
        args.QUERY,
        args.TESTSUITE,
        mode='row',
        cast=False)
    for row in rows:
        print(row)


def call_mkprof(args):
    return mkprof(
        args.DEST,
        source=args.source or args.input,
        relations=args.relations,
        where=args.where,
        in_place=args.in_place,
        skeleton=args.skeleton,
        full=args.full,
        gzip=args.gzip)


def call_process(args):
    return process(
        args.grammar,
        args.TESTSUITE,
        source=args.source,
        select=args.select,
        generate=args.generate,
        transfer=args.transfer,
        all_items=args.all_items,
        result_id=args.p)


def call_compare(args):
    template = '{id}\t<{test},{shared},{gold}>'
    if args.verbosity > 1:
        template += '\t{input}'
    for result in compare(
            args.TESTSUITE,
            args.GOLD,
            select=args.select):
        print(template.format(**result))


def call_repp(args):
    return repp(
        args.FILE or sys.stdin,
        config=args.config,
        module=args.m,
        active=args.a,
        format=args.format,
        trace_level=(args.trace and args.verbosity) or 0)


## Helper definitions

def _make_itsdb_actions(items):
    actions = []
    if items is not None:
        for item in items:
            data_specifier, function = item.split('=', 1)
            table, cols = itsdb.get_data_specifier(data_specifier)
            function = eval('lambda row, x:{}'.format(function))
            actions.append((table, cols, function))
    return actions


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


# Arguments for the convert command
convert_parser = argparse.ArgumentParser(add_help=False)
convert_parser.set_defaults(func=call_convert)
convert_parser.add_argument(
    'PATH',
    nargs='?',
    help=('file with representations to convert or testsuite directory '
          'from which result:mrs will be selected; if not given, '
          '<stdin> is read as though it were a file'))
convert_parser.add_argument(
    '-f',
    '--from',
    metavar='FMT',
    default='simplemrs',
    choices=('simplemrs ace mrx mrs-json dmrx dmrs-json dmrs-penman '
             'eds eds-json eds-penman'.split()),
    help='original representation (default: simplemrs)')
convert_parser.add_argument(
    '-t',
    '--to',
    metavar='FMT',
    default='simplemrs',
    choices=('simplemrs mrx mrs-json mrs-prolog '
             'simpledmrs dmrx dmrs-json dmrs-penman dmrs-tikz '
             'eds eds-json eds-penman'.split()),
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
    '--show-status',
    action='store_true',
    help='(--to=eds only) annotate disconnected graphs and nodes')
convert_parser.add_argument(
    '--predicate-modifiers',
    action='store_true',
    help='(--to=eds* only) attempt to join disconnected graphs')
convert_parser.add_argument(
    '--select',
    metavar='QUERY',
    default='result:mrs',
    help=('TSQL query for selecting MRS data when PATH points to '
          'a testsuite directory (default: result:mrs)'))

# Arguments for the select command
select_parser = argparse.ArgumentParser(add_help=False)
select_parser.set_defaults(func=call_select)
select_parser.add_argument(
    'QUERY', help='TSQL selection (e.g., \'i-input where readings = 0\')')
select_parser.add_argument(
    'TESTSUITE', help='path to the testsuite directory to select data from')

# mkprof subparser
mkprof_parser = argparse.ArgumentParser(add_help=False)
mkprof_parser.set_defaults(func=call_mkprof)
mkprof_parser.add_argument(
    'DEST', help='directory for the destination (output) testsuite')
mkprof_grp1 = mkprof_parser.add_mutually_exclusive_group()
mkprof_grp1.add_argument(
    '-s', '--source', metavar='DIR', help='path to a testsuite directory')
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
    '--where', metavar='CONDITION',
    help=('filter records in the testsuite with a TSQL condition '
          '(e.g., \'i-length <= 10 && readings > 0\')'))
mkprof_parser.add_argument(
    '-r',
    '--relations',
    metavar='FILE',
    help='relations file to use for destination testsuite')
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

# process subparser
process_parser = argparse.ArgumentParser(add_help=False)
process_parser.set_defaults(func=call_process)
process_parser.add_argument(
    'TESTSUITE', help='target testsuite'
)
process_parser.add_argument(
    '-g', '--grammar', metavar='GRM', required=True,
    help='compiled grammar image'
)
process_parser.add_argument(
    '-s', '--source', metavar='PATH',
    help='source testsuite; if unset, set to TESTSUITE'
)
process_parser.add_argument(
    '--select', metavar='QUERY',
    help=('TSQL query for selecting processor inputs (e.g., '
          '\'i-input where i-length < 10\'; see above for defaults)')
)
process_parser.add_argument(
    '--all-items', action='store_true',
    help='don\'t exclude ignored items (i-wf==2) in parsing'
)
process_grp1 = process_parser.add_mutually_exclusive_group()
process_grp1.add_argument(
    '-e', '--generate', action='store_true',
    help='generation mode (--source is strongly encouraged)'
)
process_grp1.add_argument(
    '-t', '--transfer', action='store_true',
    help='transfer mode (--source is strongly encouraged)'
)
process_parser.add_argument(
    '-p', metavar='RID',
    help=('transfer or generate from result with result-id=RID; '
          'short for adding \'where result-id==RID\' to --select')
)

# compare subparser
compare_parser = argparse.ArgumentParser(add_help=False)
compare_parser.set_defaults(func=call_compare)
compare_parser.add_argument(
    'TESTSUITE', help='path to the current test-suite directory')
compare_parser.add_argument(
    'GOLD', help='path to the gold test-suite directory')
compare_parser.add_argument(
    '--select',
    metavar='QUERY',
    default='item:i-id item:i-input result:mrs',
    help=('TSQL query for selecting (id, input, mrs) triples from '
          'TESTSUITE and GOLD (default: \'i-id i-input mrs\')'))

# repp subparser
repp_parser = argparse.ArgumentParser(add_help=False)
repp_parser.set_defaults(func=call_repp)
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
subparser.add_parser(
    'convert',
    parents=[common_parser, convert_parser],
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=redent("""
        Convert between various DELPH-IN Semantics representations.

        Available bidirectional codecs:
            simplemrs, mrx, mrs-json
            dmrx, dmrs-penman, dmrs-json,
            eds, eds-penman, eds-json

        NOTE: imported EDSs can only be exported to other EDS representations

        Available export-only codec:
            mrs-prolog, simpledmrs, dmrs-tikz

        Additionally one can use --from=ace to read the simplemrs format
        output by ACE while filtering out other outputs.
        """))
subparser.add_parser(
    'select',
    parents=[common_parser, select_parser],
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=redent("""
        Select data from [incr tsdb()] testsuites.
        """))
subparser.add_parser(
    'mkprof',
    parents=[common_parser, mkprof_parser],
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=redent("""
        This command creates testsuites. There are four usage patterns:

            delphin mkprof --input=sentences.txt --relations=../relations ...
            delphin mkprof --relations=../relations ... < sentences.txt
            delphin mkprof --source=testsuite/ ...
            delphin mkprof --in-place ...

        The first two read sentences (one per line; '*' in the first column
        indicates ungrammaticality) from --input or <stdin> and --relations
        is required. The second two use an existing testsuite; --relations
        defaults to that of --source; --in-place reads and overwrites DEST.

        By default, testsuites are skeletons as from the `mkprof` utility of
        `art`, where the tsdb-core files (e.g., 'item') are non-empty but all
        other tables exist as empty files. The --full option, with --source,
        will copy a full profile, while the --skeleton option will only write
        the tsdb-core files and 'relations' file.
    """))
subparser.add_parser(
    'process',
    parents=[common_parser, process_parser],
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=redent("""
        Use a processor (namely ACE) to process each item in the [incr tsdb()]
        testsuite given by --source (TESTSUITE if --source is not given). For
        standard [incr tsdb()] schemata, input items given by the following
        selectors for each task (configurable via the --select option):

            * parse:    i-input
            * transfer: mrs
            * generate: mrs

        In addition, the following TSQL condition is applied if --source is a
        standard [incr tsdb()] profile and --all-items is not used:

            where i-wf != 2
    """))
subparser.add_parser(
    'compare', parents=[common_parser, compare_parser],
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=redent("""
        Compare MRS results in test and gold [incr tsdb()] testsuites.

        Graph isomorphism is used to determine if two MRSs are equivalent and
        the results show how many unique MRSs exist in the test and gold
        testsuites and how many are shared.
    """))
subparser.add_parser(
    'repp', parents=[common_parser, repp_parser],
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=redent("""
        Tokenize sentences using a Regular Expression PreProcessor (REPP).

        This front-end to the delphin.repp module makes it easy to tokenize
        inputs from a testsuite, a file of sentences, or sentences on stdin,
        and can present the results in a variety of formats. It also visualizes
        the application of REPP rules with the --trace option, which can be
        useful for debugging REPP modules.
    """))

if __name__ == '__main__':
    main()
