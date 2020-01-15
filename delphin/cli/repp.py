
"""
Tokenize sentences using a Regular Expression PreProcessor (REPP).

This front-end to the delphin.repp module makes it easy to tokenize
inputs from a testsuite, a file of sentences, or sentences on stdin,
and can present the results in a variety of formats. It also visualizes
the application of REPP rules with the --trace option, which can be
useful for debugging REPP modules.
"""

import sys
import argparse
import warnings

from delphin.exceptions import PyDelphinWarning
from delphin.commands import repp


parser = argparse.ArgumentParser(add_help=False)  # filled out below

COMMAND_INFO = {
    'name': 'repp',
    'help': 'Tokenize sentences using REPP',
    'description': __doc__,
    'parser': parser
}


def call_repp(args):
    color = (args.color == 'always'
             or (args.color == 'auto' and sys.stdout.isatty()))
    if color:
        try:
            import pygments  # noqa: F401
        except ImportError:
            # don't warn if color=auto
            if args.color == 'always':
                warnings.warn(
                    'Pygments must be installed for diff highlighting',
                    PyDelphinWarning)
            color = False
    return repp(
        args.FILE or sys.stdin,
        config=args.config,
        module=args.m,
        active=args.a,
        format=args.format,
        color=color,
        trace_level=1 if args.trace else 0)


parser.set_defaults(func=call_repp)
parser.add_argument(
    'FILE', nargs='?', help='an input file')
group = parser.add_mutually_exclusive_group()
group.add_argument(
    '-c', '--config', metavar='PATH',
    help='a .set configuration file')
group.add_argument(
    '-m', metavar='PATH', help='the main .rpp file')
parser.add_argument(
    '-a', action='append', metavar='NAME',
    help='activate an external module')
parser.add_argument(
    '-f', '--format',
    metavar='FMT',
    choices=('string', 'line', 'triple', 'yy'),
    default='yy',
    help='output token format')
parser.add_argument(
    '--color',
    metavar='WHEN',
    default='auto',
    help='(auto|always|never) use ANSI color (default: auto)')
parser.add_argument(
    '--trace', action='store_true',
    help='print each step that modifies an input string')
