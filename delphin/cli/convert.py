
"""
Convert DELPH-IN Semantics representations and formats.

Use --list to see the available codecs. A codec name may be suffixed
with "-lines" to enable line-based reading/writing.
"""

import sys
import argparse
import warnings

from delphin.exceptions import PyDelphinWarning
from delphin.commands import convert
from delphin import util


parser = argparse.ArgumentParser(add_help=False)  # filled out below

COMMAND_INFO = {
    'name': 'convert',
    'help': 'Convert DELPH-IN Semantics representations',
    'description': __doc__,
    'parser': parser
}


def call_convert(args):
    if args.list:
        _list_codecs(args.verbosity > 0)
    else:
        color = (args.color == 'always'
                 or (args.color == 'auto' and sys.stdout.isatty()))
        if color:
            try:
                import delphin.highlight  # noqa: F401
            except ImportError:
                # don't warn if color=auto
                if args.color == 'always':
                    warnings.warn(
                        'delphin.highlight must be installed for '
                        'syntax highlighting',
                        PyDelphinWarning)
                color = False
        if args.indent and args.indent is not True:
            if args.indent.lower() in ('no', 'none'):
                args.indent = None
            else:
                args.indent = int(args.indent)
        print(convert(
            args.PATH,
            vars(args)['from'],  # vars() to avoid syntax error
            args.to,
            properties=(not args.no_properties),
            lnk=(not args.no_lnk),
            color=color,
            indent=args.indent,
            select=args.select,
            # below are format-specific kwargs
            show_status=args.show_status,
            predicate_modifiers=args.predicate_modifiers,
            semi=args.semi))


def _list_codecs(verbose):
    codecs = util.inspect_codecs()

    for rep, data in sorted(codecs.items()):
        print(rep.upper())
        for name, mod, description in sorted(data):
            print('\t{:12s}\t{}/{}\t{}'.format(
                name,
                'r' if hasattr(mod, 'load') else '-',
                'w' if hasattr(mod, 'dump') else '-',
                description))


# Arguments for the convert command
parser.set_defaults(func=call_convert)
parser.add_argument(
    'PATH',
    nargs='?',
    help=('file with representations to convert or testsuite directory '
          'from which result.mrs will be selected; if not given, '
          '<stdin> is read as though it were a file'))
parser.add_argument(
    '--list',
    action='store_true',
    help='list the available codecs and capabilities')
parser.add_argument(
    '-f',
    '--from',
    metavar='FMT',
    default='simplemrs',
    help='original representation (default: simplemrs)')
parser.add_argument(
    '-t',
    '--to',
    metavar='FMT',
    default='simplemrs',
    help='target representation (default: simplemrs)')
parser.add_argument(
    '--no-properties',
    action='store_true',
    help='suppress morphosemantic properties')
parser.add_argument(
    '--no-lnk',
    action='store_true',
    help='suppress lnk surface alignments and surface strings')
parser.add_argument(
    '--indent',
    metavar='N',
    nargs='?',
    default=False,
    const=True,
    help='format with explicit indent N ("no" for no newlines)')
parser.add_argument(
    '--color',
    metavar='WHEN',
    default='auto',
    help='(auto|always|never) use ANSI color (default: auto)')
parser.add_argument(
    '--select',
    metavar='QUERY',
    default='result.mrs',
    help=('TSQL query for selecting MRS data when PATH points to '
          'a testsuite directory (default: result.mrs)'))
parser.add_argument(
    '--show-status',
    action='store_true',
    help='(--to=eds only) annotate disconnected graphs and nodes')
parser.add_argument(
    '--predicate-modifiers',
    action='store_true',
    help='(--to=eds* only) attempt to join disconnected graphs')
parser.add_argument(
    '--sem-i', '--semi',
    dest='semi',
    metavar='PATH',
    help='(--to=indexedmrs only) path to a SEM-I')
