#!/usr/bin/env python3

USAGE = """
pyDelphin command

Usage:
  delphin (--help|--version)
  delphin <command> [<args>...]

Commands:
  convert               convert MRS representations
  select                select data from [incr tsdb()] profiles
  mkprof                create [incr tsdb()] profiles
  compare               compare two [incr tsdb()] profiles

Options:
  -h, --help            print usage and exit
  -V, --version         print the version and exit
"""

CONVERT_USAGE = """
Usage:
  delphin convert [PATH] [--from=FMT] [--to=FMT]
                  [--pretty-print|--indent=N]
                  [--color=WHEN] [-v...|-q]

Arguments:
  PATH                  path to a file containing representations to convert,
                        or a profile directory from which result:mrs will be
                        selected; if not given, <stdin> is read as though it
                        were a file.

Options:
  -h, --help            print usage and exit
  -v, --verbose         increase verbosity
  -q, --quiet           don't print to stdout/stderr
  -f FMT, --from FMT    original representation [default: simplemrs]
  -t FMT, --to FMT      target representation [default: simplemrs]
  --pretty-print        format in a more human-readable way
  --indent N            format with explicit indent N (implies --pretty-print)
  --color WHEN          (auto|always|never) use ANSI color [default: auto]
"""

SELECT_USAGE = """
Usage:
  delphin select DATASPEC PROFILE [--join=TABLES]
                 [--apply=APL]... [--filter=CND]... [-v...|-q]

Arguments:
  DATASPEC              table:col[@col...] data specifier (e.g. item:i-input)
  PROFILE               path to the profile directory to select data from

Options:
  -h, --help            print usage and exit
  -v, --verbose         increase verbosity
  -q, --quiet           don't print to stdout/stderr
  -j TBLS, --join TBLS  join two tables with a shared key (e.g. parse,result);
                        dataspecs require table (e.g. parse:i-id@result:mrs)
  -a APL, --apply APL   apply an expression to rows/cols in the profile;
                        APL is a string like 'table:col=expression'
  -f CND, --filter CND  keep rows satisfying a condition; CND is a
                        string like 'table:col=expression'
"""

MKPROF_USAGE = """
Usage:
  delphin mkprof DEST (--source PROFILE | --in-place)
                      [--apply=APL]... [--filter=CND]...
                      [--relations=FILE] [--full|--skeleton] [--gzip]
                      [-v...|-q]
  delphin mkprof DEST --relations=FILE [--input TXT] [--skeleton] [--gzip]
                      [-v...|-q]

Item data for the mkprof command may come from a --source profile, a
text --input file, or from <stdin>. In the latter two cases, each line
is a sentence ('*' in the first column indicates an ungrammatical
sentence), the --relations option is required, and only the i-id,
i-input, and i-wf fields will be filled with a meaningful value. By
default, mkprof produces skeletons like the `mkprof` utility of `art`,
where the 'item' and 'relations' files are non-empty but all other
tables exist as empty files. The --full option, with --source, will copy
a full profile, while the --skeleton option will only write the 'item'
and 'relations' files.

Arguments:
  DEST                  directory for the destination (output) profile

Options:
  -h, --help            print usage and exit
  -v, --verbose         increase verbosity
  -q, --quiet           don't print to stdout/stderr
  -i TXT, --input TXT   file of test sentences (* sents are ungrammatical)
  -r FILE, --relations FILE
                        relations file to use for destination profile
  -s PROFILE, --source PROFILE
                        path to a profile directory
  --in-place            use DEST as the --source
  --full                write all tables (must be used with --source)
  --skeleton            write only 'item' and 'relations' files
  -a APL, --apply APL   apply an expression to rows/cols in the profile;
                        APL is a string like 'table:col=expression'
  -f CND, --filter CND  keep rows satisfying a condition; CND is a
                        string like 'table:col=expression'
  -z, --gzip            compress table files with gzip
"""

COMPARE_USAGE = """
Usage:
  delphin compare PROFILE GOLD [--apply=APL]... [--filter=CND]... [-v...|-q]

Arguments:
  PROFILE               path to the current profile directory
  GOLD                  path to the gold profile directory

Options:
  -h, --help            print usage and exit
  -v, --verbose         increase verbosity
  -q, --quiet           don't print to stdout/stderr
  -a APL, --apply APL   apply an expression to rows/cols in the profile;
                        APL is a string like 'table:col=expression'
  -f CND, --filter CND  keep rows satisfying a condition; CND is a
                        string like 'table:col=expression'
"""

import sys
import os
import logging
import json
from functools import partial

from docopt import docopt

from delphin.__about__ import __version__
from delphin.mrs import xmrs, eds
from delphin import itsdb


def main():
    args = docopt(
        USAGE,
        version='pyDelphin {}'.format(__version__),
        options_first=True
    )

    cmd = args['<command>']
    try:
        command, usage = {
            'convert': (convert, CONVERT_USAGE),
            'select': (select, SELECT_USAGE),
            'mkprof': (mkprof, MKPROF_USAGE),
            'compare': (compare, COMPARE_USAGE),
        }[cmd]
    except KeyError:
        sys.exit('{} is not a valid command. See `delphin --help`'.format(cmd))

    args = docopt(usage, [cmd] + args['<args>'])

    # global init
    if args.get('--quiet', False):
        args['--verbose'] = 0
        sys.stdout.close()
        sys.stdout = open(os.devnull, 'w')

    logging.basicConfig(level=50 - ((args['--verbose'] + 2) * 10))

    command(args)


def convert(args):
    """
    Convert between various MRS codecs or to export formats.
    """
    from delphin.mrs import (
        simplemrs,
        mrx,
        dmrx,
        eds,
        simpledmrs,
        penman
    )
    from delphin.extra import latex
    codecs = dict([
        ('simplemrs', (simplemrs.loads, simplemrs.dumps)),
        ('mrx', (mrx.loads, mrx.dumps)),
        ('dmrx', (dmrx.loads, dmrx.dumps)),
        ('eds', (eds.loads, eds.dumps)),
        ('mrs-json', (_mrs_json.loads, _mrs_json.dumps)),
        ('dmrs-json', (_dmrs_json.loads, _dmrs_json.dumps)),
        ('eds-json', (_eds_json.loads, _eds_json.dumps)),
        ('dmrs-penman', (partial(penman.loads, model=xmrs.Dmrs),
                         partial(penman.dumps, model=xmrs.Dmrs))),
        ('eds-penman', (partial(penman.loads, model=eds.Eds),
                         partial(penman.dumps, model=eds.Eds))),
        ('simpledmrs', (None, simpledmrs.dumps)),
        ('dmrs-tikz', (None, latex.dmrs_tikz_dependency))
    ])
    decoders = set(k for k, cd in codecs.items() if cd[0])
    encoders = set(k for k, cd in codecs.items() if cd[1])

    # arg validation
    if args['--from'] not in decoders:
        sys.exit('Source format must be one of: {}'
                 .format(', '.join(sorted(decoders))))
    if args['--to'] not in encoders:
        sys.exit('Source format must be one of: {}'
                 .format(', '.join(sorted(encoders))))
    if args['--from'].startswith('eds') and not args['--to'].startswith('eds'):
        sys.exit('Conversion from EDS to non-EDS currently not supported.')
    args['--color'] = (
        args['--color'] == 'always' or
        (args['--color'] == 'auto' and sys.stdout.isatty())
    )
    if args['--indent']:
        args['--pretty-print'] = True
        if args['--indent'].isdigit():
            args['--indent'] = int(args['--indent'])

    # read
    loads = codecs[args['--from']][0]
    if args['PATH'] is not None:
        if os.path.isdir(args['PATH']):
            p = itsdb.ItsdbProfile(args['PATH'])
            xs = [next(iter(loads(r[0])), None)
                  for r in p.select('result', ['mrs'])]
        else:
            xs = loads(open(args['PATH'], 'r').read())
    else:
        xs = loads(sys.stdin.read())

    # write
    dumps = codecs[args['--to']][1]
    kwargs = {}
    if args['--color']: kwargs['color'] = args['--color']
    if args['--pretty-print']: kwargs['pretty_print'] = args['--pretty-print']
    if args['--indent']: kwargs['indent'] = args['--indent']
    try:
        print(dumps(xs, **kwargs))
    except TypeError:
        sys.exit(
            'One or more parameters to {} are not supported: {}'
            .format(args['--to'], ', '.join(kwargs))
        )

def select(args):
    """
    Select data from [incr tsdb()] profiles.
    """
    in_profile = _prepare_input_profile(args['PROFILE'],
                                        filters=args['--filter'],
                                        applicators=args['--apply'])
    if args['--join']:
        tbl1, tbl2 = map(str.strip, args['--join'].split(','))
        rows = in_profile.join(tbl1, tbl2, key_filter=True)
        # Adding : is just for robustness. We need something like
        # :table:col@table@col, but may have gotten table:col@table@col
        if not args['DATASPEC'].startswith(':'):
            args['DATASPEC'] = ':' + args['DATASPEC']
        table, cols = itsdb.get_data_specifier(args['DATASPEC'])
    else:
        table, cols = itsdb.get_data_specifier(args['DATASPEC'])
        rows = in_profile.read_table(table, key_filter=True)
    for row in itsdb.select_rows(cols, rows, mode='row'):
        print(row)


def mkprof(args):
    """
    Create [incr tsdb()] profiles or skeletons.
    """
    outdir = args['DEST']
    if args['--in-place']:
        if args['--skeleton']:
            sys.exit('Creating a skeleton with --in-place is not allowed.')
        args['--source'] = args['DEST']
    if args['--source']:  # input is profile
        p = _prepare_input_profile(args['--source'],
                                   filters=args['--filter'],
                                   applicators=args['--apply'])
        relations = args['--relations'] or os.path.join(p.root, 'relations')
    else:  # input is stdin or txt file
        p = None
        relations = args['--relations']

    if not os.path.isfile(relations):
        sys.exit('Invalid relations file: {}'.format(relations))

    if args['--full']:
        _prepare_output_directory(outdir)
        p.write_profile(outdir, relations_filename=relations, key_filter=True,
                        gzip=args['--gzip'])
    else:
        if p is not None:
            rows = p.read_table('item')
        elif args['--input'] is not None:
            rows = _lines_to_rows(open(args['--input']))
        else:
            rows = _lines_to_rows(sys.stdin)
        p = itsdb.make_skeleton(outdir, relations, rows, gzip=args['--gzip'])
        # unless a skeleton was requested, make empty files for other tables
        if not args['--skeleton']:
            for tbl in p.relations:
                p.write_table(tbl, [])

    # summarize what was done
    if sys.stdout.isatty():
        _red = lambda s: '\x1b[1;31m{}\x1b[0m'.format(s)
    else:
        _red = lambda s: s
    fmt = '{:>8} bytes\t{}'
    prof = itsdb.ItsdbProfile(outdir, index=False)
    relations = prof.relations
    tables = [tbl for i, tbl in sorted(enumerate(relations))]
    for filename in ['relations'] + tables:
        f = os.path.join(outdir, filename)
        if os.path.isfile(f):
            stat = os.stat(f)
            print(fmt.format(stat.st_size, filename))
        elif os.path.isfile(f + '.gz'):
            stat = os.stat(f + '.gz')
            print(fmt.format(stat.st_size, _red(filename + '.gz')))


def compare(args):
    """
    Compare two [incr tsdb()] profiles.
    """
    from delphin.mrs import simplemrs, compare as mrs_compare
    template = '{id}\t<{left},{shared},{right}>'
    if args['--verbose'] >= 1:
        template += '\t{string}'

    test_profile = _prepare_input_profile(args['PROFILE'],
                                          filters=args['--filter'],
                                          applicators=args['--apply'])
    gold_profile = _prepare_input_profile(args['GOLD'])

    i_inputs = dict((row['parse:parse-id'], row['item:i-input'])
                    for row in test_profile.join('item', 'parse'))
    
    matched_rows = itsdb.match_rows(
        test_profile.read_table('result'),
        gold_profile.read_table('result'),
        'parse-id'
    )
    for (key, testrows, goldrows) in matched_rows:
        (test_unique, shared, gold_unique) = mrs_compare.compare_bags(
            [simplemrs.loads_one(row['mrs']) for row in testrows],
            [simplemrs.loads_one(row['mrs']) for row in goldrows]
        )
        print(template.format(
            id=key,
            string=i_inputs[key],
            left=test_unique,
            shared=shared,
            right=gold_unique
        ))


## Helper definitions

# simulate json codecs for MRS and DMRS

class _MRS_JSON(object):
    CLS = xmrs.Mrs
    def getlist(self, o):
        if isinstance(o, dict):
            return [o]
        else:
            return o
    def load(self, f):
        return [self.CLS.from_dict(d) for d in self.getlist(json.load(f))]
    def loads(self, s):
        return [self.CLS.from_dict(d) for d in self.getlist(json.loads(s))]
    def dumps(self, xs, pretty_print=False, indent=None, **kwargs):
        if pretty_print and indent is None:
            indent = 2
        return json.dumps(
            [self.CLS.to_dict(
                x if isinstance(x, self.CLS) else self.CLS.from_xmrs(x)
             ) for x in xs],
            indent=indent
        )

class _DMRS_JSON(_MRS_JSON):
    CLS = xmrs.Dmrs

class _EDS_JSON(_MRS_JSON):
    CLS = eds.Eds


_mrs_json = _MRS_JSON()
_dmrs_json = _DMRS_JSON()
_eds_json = _EDS_JSON()

# working with directories and profiles

def _prepare_input_profile(path, filters=None, applicators=None):
    flts = [_make_itsdb_action(*f.split('=', 1)) for f in (filters or [])]
    apls = [_make_itsdb_action(*f.split('=', 1)) for f in (applicators or [])]
    index = len(flts) > 0
    prof = itsdb.ItsdbProfile(path,
                              filters=flts,
                              applicators=apls,
                              index=index)
    return prof


def _make_itsdb_action(data_specifier, function):
    table, cols = itsdb.get_data_specifier(data_specifier)
    function = eval('lambda row, x:{}'.format(function))
    return (table, cols, function)


def _prepare_output_directory(path):
    try:
        os.makedirs(path, exist_ok=True)
    except PermissionError:
        sys.exit('Permission denied to create output directory: {}'
                 .format(path))
    if not os.access(path, os.R_OK|os.W_OK):
        sys.exit('Cannot write to output directory: {}'
                 .format(path))


def _lines_to_rows(lines):
    for i, line in enumerate(lines):
        i_id = i * 10
        i_wf = 0 if line.startswith('*') else 1
        i_input = line[1:].strip() if line.startswith('*') else line.strip()
        yield {'i-id': i_id, 'i-wf': i_wf, 'i-input': i_input}


if __name__ == '__main__':
    main()
