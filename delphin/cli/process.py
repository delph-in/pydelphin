
"""
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
"""

import argparse
import shlex

from delphin.commands import process


parser = argparse.ArgumentParser(add_help=False)  # filled out below

COMMAND_INFO = {
    'name': 'process',
    'help': 'Process [incr tsdb()] test suites using ACE',
    'description': __doc__,
    'parser': parser
}


def call_process(args):
    return process(
        args.grammar,
        args.TESTSUITE,
        source=args.source,
        select=args.select,
        generate=args.generate,
        transfer=args.transfer,
        full_forest=args.full_forest,
        options=shlex.split(args.options),
        all_items=args.all_items,
        result_id=args.p,
        gzip=args.gzip)


# process subparser
parser.set_defaults(func=call_process)
parser.add_argument(
    'TESTSUITE', help='target testsuite'
)
parser.add_argument(
    '-g', '--grammar', metavar='GRM', required=True,
    help='compiled grammar image'
)
parser.add_argument(
    '-o', '--options', metavar='OPTIONS', type=str, default='',
    help='ACE options (see http://moin.delph-in.net/AceOptions)'
)
parser.add_argument(
    '-s', '--source', metavar='PATH',
    help='source testsuite; if unset, set to TESTSUITE'
)
parser.add_argument(
    '--select', metavar='QUERY',
    help=('TSQL query for selecting processor inputs (e.g., '
          '\'i-input where i-length < 10\'; see above for defaults)')
)
parser.add_argument(
    '--all-items', action='store_true',
    help='don\'t exclude ignored items (i-wf==2) in parsing'
)
grp1 = parser.add_mutually_exclusive_group()
grp1.add_argument(
    '-e', '--generate', action='store_true',
    help='generation mode (--source is strongly encouraged)'
)
grp1.add_argument(
    '-t', '--transfer', action='store_true',
    help='transfer mode (--source is strongly encouraged)'
)
grp1.add_argument(
    '--full-forest', action='store_true',
    help='full-forest parsing mode (record the full parse chart)'
)
parser.add_argument(
    '-p', metavar='RID',
    help=('transfer or generate from result with result-id=RID; '
          'short for adding \'where result-id==RID\' to --select')
)
parser.add_argument(
    '-z', '--gzip', action='store_true', help='compress table files with gzip')
