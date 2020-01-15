
"""
Compare MRS results in test and gold [incr tsdb()] testsuites.

Graph isomorphism is used to determine if two MRSs are equivalent and
the results show how many unique MRSs exist in the test and gold
testsuites and how many are shared.
"""

import argparse

from delphin.commands import compare


parser = argparse.ArgumentParser(add_help=False)  # filled out below

COMMAND_INFO = {
    'name': 'compare',
    'help': 'Compare MRS results across test suites',
    'description': __doc__,
    'parser': parser
}


def call_compare(args):
    template = '{id}\t<{test},{shared},{gold}>'
    if args.verbosity > 0:
        template += '\t{input}'
    for result in compare(
            args.TESTSUITE,
            args.GOLD,
            select=args.select):
        print(template.format(**result))


parser.set_defaults(func=call_compare)
parser.add_argument(
    'TESTSUITE', help='path to the current test-suite directory')
parser.add_argument(
    'GOLD', help='path to the gold test-suite directory')
parser.add_argument(
    '--select',
    metavar='QUERY',
    default='item.i-id item.i-input result.mrs',
    help=('TSQL query for selecting (id, input, mrs) triples from '
          'TESTSUITE and GOLD (default: \'i-id i-input mrs\')'))
