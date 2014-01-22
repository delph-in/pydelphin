import re

pred_re = re.compile(r'_?(?P<lemma>.*?)_' # match until last 1 or 2 parts
                     r'((?P<pos>[a-z])_)?' # pos is always only 1 char
                     r'((?P<sense>([^_\\]|(?:\\.))+)_)?' # no unescaped _s
                     r'(?P<end>rel(ation)?)', # NB only _rel is valid
                     re.IGNORECASE)
class Pred(object):
    GPRED    = 'grammarpred' # only a string allowed
    REALPRED = 'realpred'    # may explicitly define lemma, pos, sense
    SPRED    = 'stringpred'  # string-form of realpred

    def __init__(self, string=None, lemma=None, pos=None, sense=None):
        """Extract the lemma, pos, and sense (if applicable) from a pred
           string, if given, or construct a pred string from those
           components, if they are given. Treat malformed pred strings
           as simple preds without extracting the components."""
        # GPREDs and SPREDs are given by strings (with or without quotes).
        # SPREDs have an internal structure (defined here:
        # http://moin.delph-in.net/RmrsPos), but basically:
        #   _lemma_pos(_sense)?_rel
        # Note that sense is optional. The initial underscore is meaningful.
        if string is not None:
            self.string = string
            string = string.strip('"\'')
            self.type = Pred.SPRED if string.startswith('_') else Pred.GPRED
            self.lemma, self.pos, self.sense, self.end =\
                    self.decompose_pred_string(string.strip('"\''))
        # REALPREDs are specified by components, not strings
        else:
            self.type = None
            self.lemma = lemma
            self.pos = pos
            # str(sense) in case an int is given
            self.sense = str(sense) if sense is not None else None
            # end defaults to (and really should always be) _rel
            self.end = 'rel'
            string_tokens = list(filter(bool,
                                        [lemma, pos, self.sense, self.end]))
            self.string = '_'.join([''] + string_tokens)

    def __eq__(self, other):
        if isinstance(other, Pred):
            other = other.string
        return self.string.strip('"\'') == other.strip('"\'')

    def __repr__(self):
        return self.string

    def decompose_pred_string(self, predstr):
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
