
"""
This command creates testsuites. There are four usage patterns:

    delphin mkprof --input=sentences.txt --relations=RELATIONS ...
    delphin mkprof --relations=RELATIONS ... < sentences.txt
    delphin mkprof --source=TESTSUITE ...
    delphin mkprof --refresh ...

The first two read sentences (one per line; '*' in the first column
indicates ungrammaticality) from --input or <stdin> and --relations
is required. The second two use an existing testsuite; --relations
defaults to that of --source; --refresh reads and overwrites DEST.

By default, testsuites are skeletons as from the `mkprof` utility of
`art`, where the tsdb-core files (e.g., 'item') are non-empty but all
other tables exist as empty files. The --full option, with --source,
will copy a full profile, while the --skeleton option will only write
the tsdb-core files and 'relations' file.
"""

import argparse

from delphin.commands import mkprof


parser = argparse.ArgumentParser(add_help=False)  # filled out below

COMMAND_INFO = {
    'name': 'mkprof',
    'help': 'Create [incr tsdb()] test suites',
    'description': __doc__,
    'parser': parser
}


def call_mkprof(args):
    return mkprof(
        args.DEST,
        source=args.source or args.input,
        schema=args.relations,
        where=args.where,
        delimiter=args.delimiter,
        refresh=args.refresh,
        skeleton=args.skeleton,
        full=args.full,
        gzip=args.gzip)


parser.set_defaults(func=call_mkprof)
parser.add_argument(
    'DEST', help='directory for the destination (output) testsuite')

grp1 = parser.add_mutually_exclusive_group()
grp1.add_argument(
    '-s', '--source', metavar='DIR', help='path to a testsuite directory')
grp1.add_argument(
    '--refresh',
    action='store_true',
    help='overwrite DEST (works with --relations or --gzip)')
grp1.add_argument(
    '-i',
    '--input',
    metavar='TXT',
    help='file of test sentences (* sents are ungrammatical)')

parser.add_argument(
    '--where', metavar='CONDITION',
    help=('filter records in the testsuite with a TSQL condition '
          '(e.g., \'i-length <= 10 && readings > 0\')'))
parser.add_argument(
    '-r',
    '--relations',
    metavar='FILE',
    help='relations file to use for destination testsuite')
parser.add_argument(
    '--delimiter',
    metavar='C',
    help=('split input lines with delimiter C; if C="@", split as a '
          'TSDB record; a header of field names is required')
)

grp2 = parser.add_mutually_exclusive_group()
grp2.add_argument(
    '--full',
    action='store_true',
    help='write all tables (must be used with --source)')
grp2.add_argument(
    '--skeleton',
    action='store_true',
    help='write only tsdb-core files for skeletons')

parser.add_argument(
    '-z', '--gzip', action='store_true', help='compress table files with gzip')
