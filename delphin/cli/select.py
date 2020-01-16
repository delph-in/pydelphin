
"""
Select data from [incr tsdb()] test suites.
"""

import argparse
import logging

from delphin import tsdb
from delphin.commands import select

logger = logging.getLogger('delphin.commands')

parser = argparse.ArgumentParser(add_help=False)  # filled out below

COMMAND_INFO = {
    'name': 'select',
    'help': 'Select data from [incr tsdb()] test suites',
    'description': __doc__,
    'parser': parser
}


def call_select(args):
    rows = select(
        args.QUERY,
        args.TESTSUITE)
    try:
        for row in rows:
            print(tsdb.join(row))
    except (BrokenPipeError):
        logger.info('broken pipe')


# Arguments for the select command
parser.set_defaults(func=call_select)
parser.add_argument(
    'QUERY', help='TSQL selection (e.g., \'i-input where readings = 0\')')
parser.add_argument(
    'TESTSUITE', help='path to the testsuite directory to select data from')
