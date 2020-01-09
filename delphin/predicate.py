
"""
Semantic predicates.
"""

import re

from delphin.exceptions import PyDelphinException
# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401


class PredicateError(PyDelphinException):
    """Raised on invalid predicate or predicate operations."""


# allowed parts-of-speech
# 'd' ('discourse') is discouraged and may be removed
_POS = set('nvajrscpqxud')

_lemma_re = re.compile(r'[^\s_]+')
_pos_re = re.compile(r'[{}]'.format(''.join(_POS)), flags=re.IGNORECASE)
_sense_re = re.compile(r'[^\s_]+')

# strict regular expression only allows fully-compliant predicate strings
_strict_predicate_re = re.compile(
    r'(_{0}_{1}(?:_{2})?)$'  # normalized surface predicate
    r'|([^\s_]\S*)$'         # abstract predicate
    .format(_lemma_re.pattern, _pos_re.pattern, _sense_re.pattern),
    re.IGNORECASE)

# robust regular expression allows some observed variations
_robust_predicate_re = re.compile(
    r'_?'                        # allow abstract predicates, too
    r'(?P<lemma>{0}(?:_{0})*?)'  # match until last 1 or 2 parts
    r'(?:_(?P<pos>{1}))?'        # pos is optional
    r'(?:_(?P<sense>{2}))?'      # sense is optional
    r'(?:_rel)?$'                # _rel is optional
    .format(_lemma_re.pattern, _pos_re.pattern, _sense_re.pattern),
    flags=re.IGNORECASE)


def _strip_predicate(s):
    """Remove quotes and _rel suffix from predicate *s*"""
    if s.startswith('"') and s.endswith('"'):
        s = s[1:-1]
    elif s.startswith("'"):
        s = s[1:]
    if s[-4:].lower() == '_rel':
        s = s[:-4]
    return s


def split(s):
    """
    Split predicate string *s* and return the lemma, pos, and sense.

    This function uses more robust pattern matching than used by the
    validation functions :func:`is_valid`, :func:`is_surface`, and
    :func:`is_abstract`. This robustness is to accommodate inputs that
    are not entirely well-formed, such as surface predicates with
    underscores in the lemma or a missing part-of-speech. Additionally
    it can be used, with some discretion, to inspect abstract
    predicates, which technically do not have individual components
    but in practice follow the same convention as surface predicates.

    Examples:
        >>> split('_dog_n_1_rel')
        ('dog', 'n', '1')
        >>> split('udef_q')
        ('udef', 'q', None)
    """
    _s = _strip_predicate(s)
    match = _robust_predicate_re.match(_s)
    if match is None:
        raise PredicateError(f'invalid predicate: {s}')

    return (match.group('lemma'), match.group('pos'), match.group('sense'))


def create(lemma, pos, sense=None):
    """
    Create a surface predicate string from its *lemma*, *pos*, and *sense*.

    The components are validated in order to guarantee that the resulting
    predicate symbol is well-formed.

    This function cannot be used to create abstract predicate symbols.

    Examples:
        >>> create('dog', 'n', '1')
        '_dog_n_1'
        >>> create('some', 'q')
        '_some_q'
    """
    if _lemma_re.fullmatch(lemma) is None:
        raise PredicateError(f'invalid lemma: {lemma}')
    if pos.lower() not in _POS:
        raise PredicateError(f'invalid part-of-speech: {pos}')
    if sense is not None and _sense_re.fullmatch(sense) is None:
        raise PredicateError(f'invalid sense: {sense}')
    parts = [lemma, pos]
    if sense:
        parts.append(sense)
    return '_' + '_'.join(parts)


def normalize(s):
    """
    Normalize the predicate string *s* to a conventional form.

    This makes predicate strings more consistent by removing quotes and
    the `_rel` suffix, and by lowercasing them.

    Examples:
        >>> normalize('"_DOG_n_1_rel"')
        '_dog_n_1'
        >>> normalize('_dog_n_1')
        '_dog_n_1'
    """
    _s = _strip_predicate(s)
    _s = _s.lower()
    return _s


def is_valid(s):
    """
    Return `True` if *s* is a valid predicate string.

    Examples:
        >>> is_valid('"_dog_n_1_rel"')
        True
        >>> is_valid('_dog_n_1')
        True
        >>> is_valid('_dog_noun_1')
        False
        >>> is_valid('dog_noun_1')
        True
    """
    _s = _strip_predicate(s)
    return _strict_predicate_re.match(_s) is not None


def is_surface(s):
    """
    Return `True` if *s* is a valid surface predicate string.

    Examples:
        >>> is_valid('"_dog_n_1_rel"')
        True
        >>> is_valid('_dog_n_1')
        True
        >>> is_valid('_dog_noun_1')
        False
        >>> is_valid('dog_noun_1')
        False
    """
    _s = _strip_predicate(s)
    m = _strict_predicate_re.match(_s)
    return m is not None and m.lastindex == 1


def is_abstract(s):
    """
    Return `True` if *s* is a valid abstract predicate string.

    Examples:
        >>> is_abstract('udef_q_rel')
        True
        >>> is_abstract('"coord"')
        True
        >>> is_valid('"_dog_n_1_rel"')
        False
        >>> is_valid('_dog_n_1')
        False
    """
    _s = _strip_predicate(s)
    m = _strict_predicate_re.match(_s)
    return m is not None and m.lastindex == 2
