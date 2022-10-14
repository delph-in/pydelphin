
"""
Elementary Dependency Matching
"""

from typing import Union, List, Tuple, Iterable, Any, NamedTuple, Optional
import logging
from collections import Counter
from itertools import zip_longest

from delphin.lnk import LnkMixin
from delphin.eds import EDS
from delphin.dmrs import DMRS

# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

_SemanticRepresentation = Union[EDS, DMRS]
_Span = Tuple[int, int]
_Triple = Tuple[_Span, str, Any]


class _Count(NamedTuple):
    gold: int
    test: int
    both: int

    def add(self, other: '_Count') -> '_Count':
        return _Count(self.gold + other.gold,
                      self.test + other.test,
                      self.both + other.both)


class _Match(NamedTuple):
    name: _Count
    argument: _Count
    property: _Count
    constant: _Count
    top: _Count

    def add(self, other: '_Match') -> '_Match':
        return _Match(self.name.add(other.name),
                      self.argument.add(other.argument),
                      self.property.add(other.property),
                      self.constant.add(other.constant),
                      self.top.add(other.top))


class _Score(NamedTuple):
    precision: float
    recall: float
    fscore: float


def _span(node: LnkMixin) -> _Span:
    """Return the Lnk span of a Node as a (cfrom, cto) tuple."""
    return (node.cfrom, node.cto)


def _names(sr: _SemanticRepresentation) -> List[_Triple]:
    """Return the list of name (predicate) triples for *sr*."""
    triples = []
    for node in sr.nodes:
        # the None is just a placeholder for type checking
        triples.append((_span(node), node.predicate, None))
    return triples


def _arguments(sr: _SemanticRepresentation) -> List[_Triple]:
    """Return the list of argument triples for *sr*."""
    triples = []
    args = sr.arguments()
    for node in sr.nodes:
        source_span = _span(node)
        for role, target in args[node.id]:
            if target in sr:
                triples.append((source_span, role, _span(sr[target])))
    return triples


def _properties(sr: _SemanticRepresentation) -> List[_Triple]:
    """Return the list of property triples for *sr*."""
    triples = []
    for node in sr.nodes:
        node_span = _span(node)
        for feature, value in node.properties.items():
            triples.append((node_span, feature, value))
    return triples


def _constants(sr: _SemanticRepresentation) -> List[_Triple]:
    """Return the list of constant (CARG) triples for *sr*."""
    triples = []
    for node in sr.nodes:
        if node.carg:
            triples.append((_span(node), 'carg', node.carg))
    return triples


def _match(gold: _SemanticRepresentation,
           test: _SemanticRepresentation) -> _Match:
    """
    Return the counts of *gold* and *test* triples for all categories.

    The counts are a list of lists of counts as follows::

        # gold test both
        [[gn,  tn,  bn],  # name counts
         [ga,  ta,  ba],  # argument counts
         [gp,  tp,  bp],  # property counts
         [gc,  tc,  bc],  # constant counts
         [gt,  tt,  bt]]  # top counts
    """
    gold_top = 1 if gold.top in gold else 0
    test_top = 1 if test.top in test else 0
    if (
        gold_top
        and test_top
        and _span(gold[gold.top]) == _span(test[test.top])
    ):
        both_top = 1
    else:
        both_top = 0
    top_count = _Count(gold_top, test_top, both_top)

    return _Match(_count(_names, gold, test),
                  _count(_arguments, gold, test),
                  _count(_properties, gold, test),
                  _count(_constants, gold, test),
                  top_count)


def _count(func, gold, test) -> _Count:
    """
    Return the counts of *gold* and *test* triples from *func*.
    """
    gold_triples = func(gold)
    test_triples = func(test)
    c1 = Counter(gold_triples)
    c2 = Counter(test_triples)
    both = sum(min(c1[t], c2[t]) for t in c1 if t in c2)
    return _Count(len(gold_triples), len(test_triples), both)


def _accumulate(
    golds: Iterable[Optional[_SemanticRepresentation]],
    tests: Iterable[Optional[_SemanticRepresentation]],
    ignore_missing_gold: bool,
    ignore_missing_test: bool,
) -> _Match:
    """
    Sum the matches for all *golds* and *tests*.
    """
    info = logger.isEnabledFor(logging.INFO)
    totals = _Match(_Count(0, 0, 0),
                    _Count(0, 0, 0),
                    _Count(0, 0, 0),
                    _Count(0, 0, 0),
                    _Count(0, 0, 0))

    for i, (gold, test) in enumerate(zip_longest(golds, tests), 1):
        logger.info('pair %d', i)

        if gold is None and test is None:
            logger.info('no gold or test representation; skipping')
            continue
        elif gold is None:
            if ignore_missing_gold:
                logger.info('no gold representation; skipping')
                continue
            else:
                logger.debug('missing gold representation')
                gold = EDS()
        elif test is None:
            if ignore_missing_test:
                logger.info('no test representation; skipping')
                continue
            else:
                logger.debug('missing test representation')
                test = EDS()

        assert isinstance(gold, (EDS, DMRS)) and isinstance(test, (EDS, DMRS))
        result = _match(gold, test)

        if info:
            logger.info(
                '             gold\ttest\tboth\tPrec.\tRec.\tF-Score')
            fmt = '%11s: %4d\t%4d\t%4d\t%5.3f\t%5.3f\t%5.3f'
            logger.info(
                fmt, 'Names', *result.name, *_prf(*result.name))
            logger.info(
                fmt, 'Arguments', *result.argument, *_prf(*result.argument))
            logger.info(
                fmt, 'Properties', *result.property, *_prf(*result.property))
            logger.info(
                fmt, 'Constants', *result.constant, *_prf(*result.constant))
            logger.info(
                fmt, 'Tops', *result.top, *_prf(*result.top))

        totals = totals.add(result)

    return totals


def compute(golds: Iterable[Optional[_SemanticRepresentation]],
            tests: Iterable[Optional[_SemanticRepresentation]],
            name_weight: float = 1.0,
            argument_weight: float = 1.0,
            property_weight: float = 1.0,
            constant_weight: float = 1.0,
            top_weight: float = 1.0,
            ignore_missing_gold: bool = False,
            ignore_missing_test: bool = False) -> _Score:
    """
    Compute the precision, recall, and f-score for all pairs.

    The *golds* and *tests* arguments are iterables of PyDelphin
    dependency representations, such as EDS or DMRS. The precision and
    recall are computed as follows:

    - Precision = *matching_triples* / *test_triples*
    - Recall = *matching_triples* / *gold_triples*
    - F-score = 2 * (Precision * Recall) / (Precision + Recall)

    Arguments:
        golds: gold semantic representations
        tests: test semantic representations
        name_weight: weight applied to the name score
        argument_weight: weight applied to the argument score
        property_weight: weight applied to the property score
        constant_weight: weight applied to the constant score
        top_weight: weight applied to the top score
        ignore_missing_gold: if ``True``, don't count missing gold
            items as mismatches
        ignore_missing_test: if ``True``, don't count missing test
            items as mismatches
    Returns:
        A tuple of (precision, recall, f-score)
    """
    logger.info('Computing EDM (N=%g, A=%g, P=%g, T=%g)',
                name_weight, argument_weight, property_weight, top_weight)

    totals: _Match = _accumulate(
        golds, tests, ignore_missing_gold, ignore_missing_test
    )

    gold_total = (totals.name.gold * name_weight
                  + totals.argument.gold * argument_weight
                  + totals.property.gold * property_weight
                  + totals.constant.gold * constant_weight
                  + totals.top.gold * top_weight)
    test_total = (totals.name.test * name_weight
                  + totals.argument.test * argument_weight
                  + totals.property.test * property_weight
                  + totals.constant.test * constant_weight
                  + totals.top.test * top_weight)
    both_total = (totals.name.both * name_weight
                  + totals.argument.both * argument_weight
                  + totals.property.both * property_weight
                  + totals.constant.both * constant_weight
                  + totals.top.both * top_weight)

    return _prf(gold_total, test_total, both_total)


def _prf(g, t, b) -> _Score:
    if t == 0 or g == 0 or b == 0:
        return _Score(0.0, 0.0, 0.0)
    else:
        p = b / t
        r = b / g
        f = 2 * (p * r) / (p + r)
        return _Score(p, r, f)
