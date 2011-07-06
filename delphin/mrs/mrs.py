from collections import defaultdict

left_bracket = r'['
right_bracket = r']'
left_angle = r'<'
right_angle = r'>'
colon = r':'
ltop = r'LTOP'
index = r'INDEX'
rels = r'RELS'
hcons = r'HCONS'
qeq = r'qeq'
# other strings used for internal representation
mrs_top = r'__mrs_top__'
#frame_type = r'__type__'

##############################################################################
##############################################################################
### Mrs helper classes

class MrsParseError(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

    def __repr__(self):
        return self.__str__()

class MrsVarMap:
    """
    Class for mapping the MRS variables of two MRSs. Used in
    isomorphism calculations.
    """

    def __init__(self, pairs=None):
        self.lr = {} # left to right mapping (mrs1 to mrs2)
        self.rl = {} # right to left mapping (mrs2 to mrs1)
        if pairs:
            for (lvar, rvar) in pairs:
                self.add(lvar, rvar)

    def __eq__(self, other):
        try:
            return self.lr == other.lr
        except AttributeError:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def add(self, lvar, rvar):
        # don't add a mapping if it violates a previous mapping
        if (lvar in self.lr and self.lr[lvar] != rvar) or \
           (rvar in self.rl and self.rl[rvar] != lvar):
            raise KeyError
        # otherwise map both directions
        self.lr[lvar] = rvar
        self.rl[rvar] = lvar

    def mapped(self, lvar, rvar):
        return self.lmapped(lvar, rvar) or self.rmapped(rvar, lvar)

    def lmapped(self, lvar, rvar):
        return lvar in self.lr and self.lr[lvar] == rvar

    def rmapped(self, rvar, lvar):
        return rvar in self.rl and self.rl[rvar] == lvar

    def pairs(self):
        return self.lr.items()

class MrsFrame:
    def __init__(self, identifier, variables=None):
        self.identifier = identifier
        self.variables = variables or {}

    def __getitem__(self, key):
        """
        Return the MRS value for the variable specified by the key.
        """
        return self.variables.get(key, None)

    def __setitem__(self, key, value):
        self.variables[key] = value

    def __iter__(self):
        """
        Return an iterator for the variables.
        """
        return self.variables.__iter__()

    def __len__(self):
        """
        Return the length of the variables dictionary.
        """
        return len(self.variables)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return 'MrsFrame(identifier=%s, variables=%s)' % \
                (self.identifier, str(self.variables))

##############################################################################
##############################################################################
### Mrs class

class Mrs(MrsFrame):
    """
    A class for parsing text-based forms of MRSs and for evaluating the
    equivalence of two MRSs.
    """

    def __init__(self, text=None):
        """
        Initialize a MRS object.
        """
        self.reset_member_variables()
        if text is not None:
            self.initialize_mrs_from_text(text)

    def __eq__(self, other):
        return isomorphic(self, other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        try:
            return self.text
        except AttributeError:
            return ''

    ##########################################################################
    ### Parsing/Decoding Methods

    def validate_token(self, token, expected):
        if token != expected:
            self.invalid_token_error(token, expected)

    def validate_term(self, term):
        if not term.endswith(colon) or len(term) < 2:
            self.invalid_token_error(' ', colon)

    def invalid_token_error(self, token, expected):
        raise MrsParseError('Invalid token: ' + token +\
                    '\n  Expected: ' + expected)

    def unexpected_termination_error(self):
        raise MrsParseError('Invalid MRS: Unexpected termination.')

    def initialize_mrs_from_text(self, text):
        self.text = text
        self.variables = self.parse_text_mrs(text)

    def reset_member_variables(self):
        self.identifier = mrs_top
        self.text = None
        self.variables = {}
        self.properties = {}
        # vartypemap is a mapping of variable name to its type in a
        # relation (e.g. x1 in dog_n_rel is ARG0).
        # it is used for optimizations in isomorphism checks
        self.vartypemap = defaultdict(dict)

    def parse_text_mrs(self, text):
        tokens = text.split()
        variables = {}
        try:
            self.validate_token(tokens.pop(0), left_bracket)
            variables = self.parse_terms(tokens)
            self.validate_token(tokens.pop(0), right_bracket)
        except IndexError:
            self.unexpected_termination_error()
        return variables

    def parse_terms(self, tokens):
        variables = {}
        while tokens[0] != right_bracket:
            term = self.parse_term(tokens)
            if term == rels:
                variables[rels] = self.parse_rels(tokens)
            elif term == hcons:
                variables[hcons] = self.parse_hcons(tokens)
            else:
                variables[term] = self.parse_variable(tokens)
                self.vartypemap[variables[term]][mrs_top] = term
        return variables

    def parse_term(self, tokens):
        term = tokens.pop(0)
        self.validate_term(term)
        return term[:-1]

    def parse_variable(self, tokens):
        variable = tokens.pop(0)
        if tokens[0] == left_bracket:
            properties = self.parse_frame(tokens)
            self.properties[variable] = properties
        return variable

    def parse_frame(self, tokens):
        self.validate_token(tokens.pop(0), left_bracket)
        identifier = tokens.pop(0)
        frame = MrsFrame(identifier)
        while tokens[0] != right_bracket:
            term = self.parse_term(tokens)
            val = self.parse_variable(tokens)
            frame[term] = val
        self.validate_token(tokens.pop(0), right_bracket)
        return frame

    def parse_hcons(self, tokens):
        self.validate_token(tokens.pop(0), left_angle)
        hcons = {}
        while tokens[0] != right_angle:
            qeq_left = tokens.pop(0)
            self.validate_token(tokens.pop(0), qeq)
            qeq_right = tokens.pop(0)
            hcons[qeq_left] = qeq_right
        self.validate_token(tokens.pop(0), right_angle)
        return hcons

    def parse_rels(self, tokens):
        self.validate_token(tokens.pop(0), left_angle)
        rels = []
        while tokens[0] != right_angle:
            frame = self.parse_frame(tokens)
            rels += [frame]
            for attr in frame:
                self.vartypemap[frame[attr]][frame.identifier] = attr
        self.validate_token(tokens.pop(0), right_angle)
        return rels

##############################################################################
##############################################################################
### Comparison Functions

def isomorphic(mrs1, mrs2):
    """
    Given another MRS, return True if the two MRSs are isomorphic,
    otherwise return False.
    """
    # some simple tests to save time
    if mrs1.text == mrs2.text: return True
    if len(mrs1) != len(mrs2): return False
    if len(mrs1[rels]) != len(mrs2[rels]): return False
    if len(mrs1[hcons]) != len(mrs2[hcons]): return False
    try:
        # first map variables not in RELS or HCONS
        varmap = MrsVarMap([(mrs1[var], mrs2[var])
                            for var in mrs1
                            if var not in (rels, hcons)])
        # For RELS, sort them by length so we map those with the fewest
        # attributes first
        varmap = isomorphic_rels(mrs1, mrs2,
                                 sorted(mrs1[rels], key=len),
                                 sorted(mrs2[rels], key=len),
                                 varmap)
        if varmap is None:
            return False
        # HCONS is not actually checked yet. If it is to be done, it
        # should be done here
    except KeyError:
        return False
    return True

def isomorphic_rels(mrs1, mrs2, lhs_rels, rhs_rels, varmap):
    """
    Return a valid varmap, if it exists, for the RELS lists of two
    given MRSs.
    """
    # base condition: map_vars returned None or there are no more rels
    if varmap is None:
        return None
    if len(lhs_rels) == len(rhs_rels) == 0:
        return varmap
    # Otherwise look for valid mappings
    lhs = lhs_rels[0]
    for i, rhs in enumerate(rhs_rels):
        if not validate_rels(mrs1, mrs2, lhs, rhs):
            continue
        # with a valid varmap, assume it is correct and recursively
        # find mappings for the rest of the variables
        new_varmap = isomorphic_rels(mrs1, mrs2,
                                     lhs_rels[1:],
                                     rhs_rels[:i] + rhs_rels[i+1:],
                                     map_vars(lhs, rhs, varmap))
        # return the first valid varmap and break out of the loop
        if new_varmap is not None:
            return new_varmap
    return None

def map_vars(lhs, rhs, varmap):
    """
    If the variables in lhs and rhs are consistent with those in
    varmap, return a new varmap that include those from all three.
    """
    try:
        pairs = varmap.pairs() + [(lhs[attr], rhs[attr]) for attr in lhs]
        new_varmap = MrsVarMap(pairs)
        return new_varmap
    except KeyError:
        pass
    return None

def validate_rels(mrs1, mrs2, lhs, rhs):
    """
    Return True if the two relations can be mapped. Being mappable
    means that the rels have the same length and every variable
    appears in the same set of relations in the same attributes. For
    instance, if lhs's ARG0 is x1 and rhs's ARG0 is x2, and x1 has a
    vartypemap of {'dog_n_rel':'ARG0', 'the_q_rel':'ARG0',
    'bark_v_rel':'ARG1'}, then x2 must also have the same vartypemap
    in order to be mappable. This property must apply to all
    attributes in both rels.
    """
    if mrs1.identifier != mrs2.identifier or len(lhs) != len(rhs):
        return False
    try:
        for attr in lhs:
            if mrs1.vartypemap[lhs[attr]] != mrs2.vartypemap[rhs[attr]]:
                return False
    except KeyError:
        return False
    return True
