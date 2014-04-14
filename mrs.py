#!/usr/bin/env python3

import sys
import argparse
from delphin.codecs import simplemrs, mrx, dmrx

mrsformats={'simplemrs':simplemrs, 'mrx':mrx, 'dmrx':dmrx}

parser = argparse.ArgumentParser(description="Utility for manipulating MRSs")
subparsers = parser.add_subparsers(dest='command')

convert_parser = subparsers.add_parser('convert', aliases=['c'])
convert_parser.add_argument('--from', '-f', dest='srcfmt',
                            choices=list(mrsformats.keys()))
convert_parser.add_argument('--to', '-t', dest='tgtfmt',
                            choices=list(mrsformats.keys()))
convert_parser.add_argument('--pretty-print', '-p', action='store_true')
convert_parser.add_argument('--color', '-c', action='store_true')
convert_parser.add_argument('infile', metavar='PATH', nargs='?')

path_parser = subparsers.add_parser('paths', aliases=['p'])
path_parser.add_argument('--format', '-f', choices=list(mrsformats.keys()))
path_parser.add_argument('infile', metavar='PATH', nargs='?')

args = parser.parse_args()
if args.command in ('convert', 'c'):
    instream = open(args.infile, 'r') if args.infile is not None else sys.stdin
    outstream = sys.stdout
    ms = mrsformats[args.srcfmt].load(instream)
    mrsformats[args.tgtfmt].dump(outstream, ms,
                                 pretty_print=args.pretty_print,
                                 color=args.color)
elif args.command in ('paths', 'p'):
    from delphin.mrs import path as mrspath
    instream = open(args.infile, 'r') if args.infile is not None else sys.stdin
    outstream = sys.stdout
    ms = mrsformats[args.format].load(instream)
    for m in ms:
    	paths = list(mrspath.get_paths(m))
    	print('\n'.join(paths))
    	print()