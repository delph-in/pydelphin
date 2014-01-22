from collections import defaultdict, OrderedDict
import logging
import re



###############################################################################
###############################################################################
#### Comparison Functions (A2)

class BidirectionalMap(object):
    """
    Class for a bi-directional mapping the MRS variables of two MRSs.
    Used in isomorphism calculations.
    """

    def __init__(self, pairs=None):
        self._lr = {} # left to right mapping (mrs1 to mrs2)
        self._rl = {} # right to left mapping (mrs2 to mrs1)
        if pairs:
            for (lvar, rvar) in pairs:
                self.add(lvar, rvar)

    def __eq__(self, other):
        try:
            # since we ensure rl mappings don't violate lr mappings,
            # just check one side for equality.
            return self._lr == other._lr
        except AttributeError:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def add(self, lvar, rvar):
        # don't add a mapping if it violates a previous mapping
        if (lvar in self._lr and self._lr[lvar] != rvar) or \
           (rvar in self._rl and self._rl[rvar] != lvar):
            raise KeyError
        # otherwise map both directions
        self._lr[lvar] = rvar
        self._rl[rvar] = lvar

    def mapped(self, lvar, rvar):
        # We only need to check one direction
        return lvar in self._lr and self._lr[lvar] == rvar

    def pairs(self):
        return list(self._lr.items())

def isomorphic(mrs1, mrs2, ignore_varprops=False):
    """
    Given another MRS, return True if the two MRSs are isomorphic,
    otherwise return False. Isomorphism is when the MRSs share the same
    structure, including all nodes and arcs. In other words, while
    handle and variable names may be different, there is a mapping of
    the handles and variables such that the two MRSs have the same EPs
    with all labels and arguments linked to the same
    entities, and used in the same handle constraints. Variable
    properties must also be the same, but this can be ignored by
    setting the ignore_varprops parameter to True (useful when comparing
    MRSs where one has gone through a SEMI.vpm mapping).
    """
    # some simple tests to save time
    if len(mrs1.rels) != len(mrs2.rels) or\
       len(mrs1.variables) != len(mrs2.variables) or\
       len(mrs1.hcons) != len(mrs2.hcons):
        return False
    mapping = BidirectionalMap(pairs=[(mrs1.ltop, mrs2.ltop),
                                      (mrs1.index.vid, mrs2.index.vid)])
    # For RELS, sort them by length so we map those with the fewest
    # attributes first
    mapping = isomorphic_rels(mrs1, mrs2,
                              sorted(mrs1.rels, key=len),
                              sorted(mrs2.rels, key=len),
                              mapping)
    if mapping is None:
        return False
    # We know mrs1 and mrs2 have the same number of HCONS, but now
    # we that we have a mapping we can check that they are the same
    mapped_hcons1 = set((mapping._lr[h.lhandle], h.relation,
                         mapping._lr[h.rhandle])
                        for h in mrs1.hcons)
    hcons2 = set((h.lhandle, h.relation, h.rhandle) for h in mrs2.hcons)
    if mapped_hcons1 != hcons2:
        return False
    # Checking variable properties should be easy with a mapping, as
    # long as we aren't doing SEMI conversions
    if not ignore_varprops:
        for k, v in mrs1.variables.items():
            v2 = mrs2.variables[mapping._lr[k]]
            if v.properties != v2.properties:
                return False
    return True

def isomorphic_rels(mrs1, mrs2, lhs_rels, rhs_rels, mapping):
    """
    Return a valid mapping of handles and variables, if it exists, for
    the RELS lists of two given MRSs.
    """
    # base condition: map_vars returned None or there are no more rels
    if mapping is None:
        return None
    if len(lhs_rels) == len(rhs_rels) == 0:
        return mapping
    # Otherwise look for valid mappings
    lhs = lhs_rels[0]
    for i, rhs in enumerate(rhs_rels):
        if not validate_eps(mrs1, mrs2, lhs, rhs):
            continue
        # with a valid varmap, assume it is correct and recursively
        # find mappings for the rest of the variables
        new_mapping = isomorphic_rels(mrs1, mrs2,
                                      lhs_rels[1:],
                                      rhs_rels[:i] + rhs_rels[i+1:],
                                      map_vars(lhs, rhs, mapping))
        # return the first valid varmap and break out of the loop
        if new_mapping is not None:
            return new_mapping
    return None

def map_vars(lhs, rhs, mapping):
    """ If the variables in lhs and rhs are consistent with those in
        mapping, return a new mapping including those from all three."""
    try:
        new_mapping = BidirectionalMap(mapping.pairs() +\
            [(lhs.label, rhs.label)] +\
            [(lhs.args[v].vid, rhs.args[v].vid) for v in lhs.args])
        return new_mapping
    except KeyError:
        pass
    return None

def validate_eps(mrs1, mrs2, lhs, rhs):
    """
    Return True if the two EPs can be mapped. Being mappable
    means that the rels have the same length and every variable
    appears in the same set of EPs in the same attributes. For
    instance, if lhs's ARG0 is x1 and rhs's ARG0 is x2, and x1 has a
    role_map of {'dog_n_rel':'ARG0', 'the_q_rel':'ARG0',
    'bark_v_rel':'ARG1'}, then x2 must also have the same role_map
    in order to be mappable. This property must apply to all
    attributes in both EPs.
    """
    if lhs.pred != rhs.pred or len(lhs) != len(rhs):
        return False
    try:
        for v in lhs.args:
            if mrs1._role_map[lhs.args[v]] != mrs2._role_map[rhs.args[v]]:
                return False
    except KeyError:
        return False
    return True
