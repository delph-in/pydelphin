#!/usr/bin/env python
#
# itsdb.py: A top-level executable script for using the DELPH-IN
#           library for tasks related to [incr tsdb()].
#
# Author: Michael Wayne Goodman <goodmami@uw.edu>
#

import argparse
import os
import shutil
import filecmp
import logging
from delphin import itsdb
import util

descr = "A script for [incr tsdb()] tasks."

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s %(name)s: %(message)s')
logger = logging.getLogger('itsdb.py')


def main():
    ap = argparse.ArgumentParser(description=descr)
    sp = ap.add_subparsers(help='commands')

    up = sp.add_parser('update',
                       help='Update a [incr tsdb()] profile to a new schema '
                            '(relations file). If --overwrite is not '
                            'specified, the original is copied to PATH.NNN')
    up.add_argument('profile', metavar='PATH',
                    help='The path of the profile to update')
    up.add_argument('--relations', '-r', metavar='PATH',
                    help='The path of the target relations file '
                         '(optional; otherwise obtained via the LOGON SVN)')
    up.add_argument('--overwrite', '-o', action='store_true', default=False,
                    help='Overwrite the existing profile without providing '
                         'a backup.')
    up.set_defaults(func=update_profile)

    ex = sp.add_parser('extract',
                       help='Extract a field or fields from a profile and '
                            'output as text.')
    ex.add_argument('profile', metavar='PATH',
                    help='The path of the profile to extract fields from')
    ex.add_argument('--table', '-t', help='The table to pull fields from'
                                          ' (e.g. "item")')
    ex.add_argument('--field', '-f', action='append', dest='fields',
                    help='The field names in the profile (e.g. "i-input")')
    ex.add_argument('--field-delimiter', '-d', default='\t',
                    help='The delimiter of fields for a single instance')
    ex.set_defaults(func=extract_fields)

    args = ap.parse_args()
    args.func(args)


def update_profile(args):
    # The idea is to first load a profile with the current relations file,
    # then replace the relations file with the new one, then write it out.
    # Backup the original unless overwrite is specified.
    logger.debug('update_profile\n'
                 '  profile: {}\n'
                 '  relations: {}\n'
                 '  overwrite: {}\n'
                 .format(args.profile, args.relations, str(args.overwrite)))
    profile_dir = args.profile
    profile_dir = os.path.normpath(profile_dir)
    if filecmp.cmp(os.path.join(profile_dir, 'relations'), args.relations):
        logger.error('Target schema and existing profile schema are the same.')
        return
    backup_profile = util.unique_filename(profile_dir + '.bak')
    shutil.copytree(profile_dir, backup_profile,
                    ignore=shutil.ignore_patterns(*['.svn']))
    profile = itsdb.ItsdbProfile(backup_profile)
    profile.write_profile(profile_dir, args.relations)
    if args.overwrite:
        shutil.rmtree(backup_profile)
    logging.info('Profile updated: {}'.format(profile_dir))


def extract_fields(args):
    import os.path
    # don't crash with "Broken Pipe" when using head or tail, etc.
    import signal
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    profile_dir = os.path.normpath(args.profile)
    profile = itsdb.ItsdbProfile(profile_dir)
    for row in profile.read_table(args.table):
        print(args.field_delimiter.join(str(row.get(f)) for f in args.fields))

if __name__ == '__main__':
    main()
