
"""
Compute the EDM (Elementary Dependency Match) score for two collections.

The collections, GOLD and TEST, may be files containing semantic
representations, decoded using '--format'; or an [incr tsdb()] test
suite directory, selecting MRSs using '-p' for the parse result
number. GOLD and TEST should contain the same number of items. MRS
representations will be converted to EDS for comparison.
"""

import argparse
import logging
import warnings
from pathlib import Path
from typing import Iterator, Optional, Union

from delphin import dmrs, edm, eds, itsdb, mrs, tsdb, util

logger = logging.getLogger(__name__)

_SemanticRepresentation = Union[eds.EDS, dmrs.DMRS]

parser = argparse.ArgumentParser(add_help=False)

COMMAND_INFO = {
    'name': 'edm',
    'help': 'Evaluate with Elementary Dependency Match',
    'description': __doc__,
    'parser': parser,
}


def call_compute(args):
    golds = _iter_representations(args.GOLD, args.format, args.p)
    tests = _iter_representations(args.TEST, args.format, args.p)
    p, r, f = edm.compute(
        golds,
        tests,
        name_weight=args.N,
        argument_weight=args.A,
        property_weight=args.P,
        constant_weight=args.C,
        top_weight=args.T,
        ignore_missing_gold=args.ignore_missing in ('gold', 'both'),
        ignore_missing_test=args.ignore_missing in ('test', 'both'))
    print(f'Precision:\t{p}')
    print(f'   Recall:\t{r}')
    print(f'  F-score:\t{f}')


def _iter_representations(
    path: Path,
    fmt: str,
    p: int
) -> Iterator[Optional[_SemanticRepresentation]]:
    if tsdb.is_database_directory(path):
        logger.debug('reading MRSs from profile: %s', (path,))
        ts = itsdb.TestSuite(path)
        for response in ts.processed_items():
            try:
                result = response.result(p)
            except IndexError:
                yield None
            else:
                yield _eds_from_mrs(result.mrs(), predicate_modifiers=True)

    elif path.is_file():
        logger.debug('reading %s from file: %s', (fmt, path,))
        codec = util.import_codec(fmt)
        rep = codec.CODEC_INFO.get('representation', '').lower()
        if rep == 'mrs':
            for sr in codec.load(path):
                yield _eds_from_mrs(sr, predicate_modifiers=True)
        elif rep in ('dmrs', 'eds'):
            for sr in codec.load(path):
                yield sr
        else:
            raise ValueError(f'unsupported representation: {rep}')

    else:
        raise ValueError(f'not a file or TSDB database: {path}')


def _eds_from_mrs(
    m: mrs.MRS,
    predicate_modifiers: bool,
    errors: str = 'warn',
) -> Optional[eds.EDS]:
    try:
        e = eds.from_mrs(m, predicate_modifiers=predicate_modifiers)
    except Exception:
        logger.debug('could not convert MRS to EDS')
        if errors == 'warn':
            warnings.warn(
                "error in EDS conversion; skipping entry",
                stacklevel=2,
            )
        elif errors == 'strict':
            raise
        e = None
    return e


parser.set_defaults(func=call_compute)
# data selection
parser.add_argument(
    'GOLD',
    type=Path,
    help='corpus of gold semantic representations')
parser.add_argument(
    'TEST',
    type=Path,
    help='corpus of test semantic representations')
parser.add_argument(
    '-f',
    '--format',
    metavar='FMT',
    default='eds',
    help='semantic representation format (default: eds)')
parser.add_argument(
    '-p',
    metavar='N',
    type=int,
    default=0,
    help='parse result number (default: 0)')
parser.add_argument(
    '--ignore-missing',
    metavar='X',
    choices=('gold', 'test', 'both', 'none'),
    default='none',
    help='do not treat missing Xs as a mismatch (default: none)')
# comparison configuration
parser.add_argument(
    '-A', metavar='WEIGHT', type=float, default=1.0,
    help='weight for argument triples (default: 1.0)')
parser.add_argument(
    '-N', metavar='WEIGHT', type=float, default=1.0,
    help='weight for name (predicate) triples (default: 1.0)')
parser.add_argument(
    '-P', metavar='WEIGHT', type=float, default=1.0,
    help='weight for property triples (default: 1.0)')
parser.add_argument(
    '-C', metavar='WEIGHT', type=float, default=1.0,
    help='weight for constant triples (default: 1.0)')
parser.add_argument(
    '-T', metavar='WEIGHT', type=float, default=1.0,
    help='weight for matching top triples (default: 1.0)')
