import re
import logging
from .config import (GRAMMARPRED, REALPRED, STRINGPRED, QUANTIFIER_SORT)

pred_re = re.compile(
    r'_?(?P<lemma>.*?)_'  # match until last 1 or 2 parts
    r'((?P<pos>[a-z])_)?'  # pos is always only 1 char
    r'((?P<sense>([^_\\]|(?:\\.))+)_)?'  # no unescaped _s
    r'(?P<end>rel(ation)?)',  # NB only _rel is valid
    re.IGNORECASE
)


def is_valid_pred_string(s, suffix_required=True):
    """
    Return True if the given predicate string represents a valid Pred,
    False otherwise. If suffix_required is False, abbreviated Pred
    strings will be accepted (e.g. _dog_n_1 instead of _dog_n_1_rel)
    """
    s = s.strip('"')
    if not suffix_required and s.rsplit('_', 1)[-1] not in ('rel', 'relation'):
        s += '_rel'
    return pred_re.match(s) is not None


def normalize_pred_string(s):
    """
    Make pred strings more consistent by removing quotes and using the
    _rel suffix.
    """
    s = s.strip('"')
    match = pred_re.match(s) or pred_re.match(s + '_rel')
    if match:
        d = match.groupdict()
        tokens = [d['lemma']]
        if d['pos']:
            tokens.append(d['pos'])
        if d['sense']:
            tokens.append(d['sense'])
        tokens.append('rel')
        return '_'.join(tokens)
    return None


class Pred(object):
    """
    A semantic predicate.

    Preds come in three flavors:
    
    * **grammar preds** (gpreds): preds defined in a semantic hierarchy
      in the grammar, and are not necessarily tied to a lexical entry;
      grammar preds may not begin with a leading underscore
    * **real preds** (realpreds): preds that are defined as the
      composition of a lemma, a part-of-speech (pos), and sometimes a
      sense---parts-of-speech are always single characters, and senses
      may be numbers or string descriptions
    * **string preds** (spreds): a string (often double-quoted) that
      represents a real pred; string preds must begin with a leading
      underscore

    While MRS representations may distinguish real preds and string
    preds, in pyDelphin they are equivalent. All well-formed predicates,
    when represented as strings, end with ``_rel``, but in practice this
    may not be true (some may end in ``_relation``, or have no such
    suffix).

    Example:

    Preds are compared using their string representations. Surrounding
    quotes (double or single) are ignored, and capitalization doesn't
    matter. In addition, preds may be compared directly to their string
    representations:

    >>> p1 = Pred.stringpred('_dog_n_1_rel')
    >>> p2 = Pred.realpred(lemma='dog', pos='n', sense='1')
    >>> p3 = Pred.grammarpred('dog_n_1_rel')
    >>> p1 == p2
    True
    >>> p1 == '_dog_n_1_rel'
    True
    >>> p1 == p3
    False

    Args:
        predtype: the type of predicate; valid values are grammarpred,
            stringpred, or realpred, although in practice one won't use
            this constructor directly, but instead use one of the
            classmethods
        lemma: the lemma of the predicate
        pos: the part-of-speech; a single, lowercase character
        sense: the (often omitted) sense of the predicate
    Returns:
        an instantiated Pred object
    """

    def __init__(self, predtype, lemma=None, pos=None, sense=None):
        """Extract the lemma, pos, and sense (if applicable) from a pred
           string, if given, or construct a pred string from those
           components, if they are given. Treat malformed pred strings
           as simple preds without extracting the components."""
        # GRAMMARPREDs and STRINGPREDs are given by strings (with or without
        # quotes). STRINGPREDs have an internal structure (defined here:
        # http://moin.delph-in.net/RmrsPos), but basically:
        #   _lemma_pos(_sense)?_rel
        # Note that sense is optional. The initial underscore is meaningful.
        self.type = predtype
        self.lemma = lemma
        self.pos = pos
        self.sense = str(sense) if sense is not None else sense
        self.string = None  # set by class methods

    def __eq__(self, other):

        if isinstance(other, Pred):
            other = other.string
        return self.string.strip('"\'') == other.strip('"\'')

    def __repr__(self):
        return self.string

    def __hash__(self):
        return hash(self.string)

    @classmethod
    def stringpred(cls, predstr):
        lemma, pos, sense, end = Pred.split_pred_string(predstr.strip('"\''))
        pred = cls(STRINGPRED, lemma=lemma, pos=pos, sense=sense)
        pred.string = predstr
        return pred

    @classmethod
    def grammarpred(cls, predstr):
        lemma, pos, sense, end = Pred.split_pred_string(predstr.strip('"\''))
        pred = cls(GRAMMARPRED, lemma=lemma, pos=pos, sense=sense)
        pred.string = predstr
        return pred

    @staticmethod
    def string_or_grammar_pred(predstr):
        if predstr.strip('"\'').startswith('_'):
            return Pred.stringpred(predstr)
        else:
            return Pred.grammarpred(predstr)

    @classmethod
    def realpred(cls, lemma, pos, sense=None):
        pred = cls(REALPRED, lemma=lemma, pos=pos, sense=sense)
        string_tokens = list(filter(bool, [lemma, pos, str(sense or '')]))
        pred.string = '_'.join([''] + string_tokens + ['rel'])
        return pred

    @staticmethod
    def split_pred_string(predstr):
        """Extract the components from a pred string and log errors
           for any malformedness."""
        if not predstr.lower().endswith('_rel'):
            logging.warn('Predicate does not end in "_rel": {}'
                         .format(predstr))
        match = pred_re.search(predstr)
        if match is None:
            logging.warn('Unexpected predicate string: {}'.format(predstr))
            return (predstr, None, None, None)
        # _lemma_pos(_sense)?_end
        return (match.group('lemma'), match.group('pos'),
                match.group('sense'), match.group('end'))

    def is_quantifier(self):
        return self.pos == QUANTIFIER_SORT

    def short_form(self):
        """
        Return the pred string without quotes or a _rel suffix.
        """
        return self.string.strip('"').rsplit('_', 1)[0]
