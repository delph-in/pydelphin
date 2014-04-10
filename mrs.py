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
convert_parser.add_argument('infile', metavar='PATH')

args = parser.parse_args()
if args.command in ('convert', 'c'):
    instream = open(args.infile, 'r') if args.infile is not None else sys.stdin
    outstream = sys.stdout
    m = mrsformats[args.srcfmt].load(instream)
    mrsformats[args.tgtfmt].dump(outstream, m,
                                 pretty_print=args.pretty_print,
                                 color=args.color)
