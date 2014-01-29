import re
from .config import (GRAMMARPRED, REALPRED, STRINGPRED, QUANTIFIER_SORT)

pred_re = re.compile(r'_?(?P<lemma>.*?)_' # match until last 1 or 2 parts
                     r'((?P<pos>[a-z])_)?' # pos is always only 1 char
                     r'((?P<sense>([^_\\]|(?:\\.))+)_)?' # no unescaped _s
                     r'(?P<end>rel(ation)?)', # NB only _rel is valid
                     re.IGNORECASE)

class Pred(object):
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
        self.string = None # set by class methods

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
            logging.warn('Predicate does not end in "_rel": {}'.format(predstr))
        match = pred_re.search(predstr)
        if match is None:
            logging.warn('Unexpected predicate string: {}'.format(predstr))
            return (predstr, None, None, None)
        # _lemma_pos(_sense)?_end
        return (match.group('lemma'), match.group('pos'),
                match.group('sense'), match.group('end'))

    def is_quantifier(self):
        return self.pos == QUANTIFIER_SORT
