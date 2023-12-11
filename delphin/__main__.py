#!/usr/bin/env python3

"""
Entry-point for the 'delphin' command.
"""

import sys
import os
import importlib
import argparse
import logging

from delphin.exceptions import PyDelphinException
from delphin import util
import delphin.cli
# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__


logging.basicConfig()  # just use defaults here
logger = logging.getLogger(__name__)  # for this module


def main():
    args = parser.parse_args()

    if not hasattr(args, 'func'):
        sys.exit(parser.print_help())

    # global init
    if args.quiet:
        args.verbosity = 0
        sys.stdout.close()
        sys.stdout = open(os.devnull, 'w')
    else:
        args.verbosity = min(args.verbosity, 3)

    logging.getLogger('delphin').setLevel(
        logging.ERROR - (args.verbosity * 10))

    try:
        args.func(args)
    except PyDelphinException as exc:
        if logger.isEnabledFor(logging.DEBUG):
            logger.exception('an error has occurred; see below')
        else:
            sys.exit(str(exc))


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
    default=0,
    help='increase verbosity')
common_parser.add_argument(
    '-q',
    '--quiet',
    action='store_true',
    help='suppress output on <stdout> and <stderr>')


# Dynamically add subparsers from delphin.cli namespace
subparser = parser.add_subparsers(title='available subcommands', metavar='')
for name, fullname in util.namespace_modules(delphin.cli).items():
    try:
        mod = importlib.import_module(fullname)
    except ImportError:
        logger.exception('could not import %s', fullname)
        continue

    try:
        INFO = getattr(mod, 'COMMAND_INFO')
    except AttributeError:
        logger.exception('%s does not define COMMAND_INFO', fullname)
        continue

    try:
        subparser.add_parser(
            INFO['name'],
            help=INFO.get('help'),
            parents=[common_parser, INFO['parser']],
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=INFO.get('description'),
        )
    except KeyError:
        logger.exception('required info missing')


if __name__ == '__main__':
    main()
