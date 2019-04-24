
from delphin.lnk import LnkMixin

def role_priority(role):
    """Return a representation of role priority for ordering."""
    # canonical order: LBL ARG* RSTR BODY *-INDEX *-HNDL CARG ...
    role = role.upper()
    return (
        role != 'LBL',
        role in ('BODY', 'CARG'),
        role
    )


_COMMON_PROPERTIES = (
    'PERS',      # [x] person (ERG, Jacy)
    'NUM',       # [x] number (ERG, Jacy)
    'GEND',      # [x] gender (ERG, Jacy)
    'IND',       # [x] individuated (ERG)
    'PT',        # [x] pronoun-type (ERG)
    'PRONTYPE',  # [x] pronoun-type (Jacy)
    'SF',        # [e] sentential-force (ERG)
    'TENSE',     # [e] tense (ERG, Jacy)
    'MOOD',      # [e] mood (ERG, Jacy)
    'PROG',      # [e] progressive (ERG, Jacy)
    'PERF',      # [e] perfective (ERG, Jacy)
    'ASPECT',    # [e] other aspect (Jacy)
    'PASS',      # [e] passive (Jacy)
    )

_COMMON_PROPERTY_INDEX = dict((p, i) for i, p in enumerate(_COMMON_PROPERTIES))


def property_priority(prop):
    """
    Return a representation of property priority for ordering.

    Note:

       The ordering provided by this function was modeled on the ERG
       and Jacy grammars and may be inaccurate for others. Properties
       not known to this function will be sorted alphabetically.
    """
    index = _COMMON_PROPERTY_INDEX.get(prop.upper(), len(_COMMON_PROPERTIES))
    return (index, prop)


class Predication(LnkMixin):

    __slots__ = ('id', 'predicate', 'lnk', 'surface', 'base')

    def __init__(self, id, predicate, lnk, surface, base):
        super().__init__(lnk, surface)
        self.id = id
        self.predicate = predicate
        self.base = base


class SemanticStructure(LnkMixin):

    __slots__ = ('top', 'identifier')

    def __init__(self, top, lnk, surface, identifier):
        super().__init__(lnk, surface)
        self.top = top
        self.identifier = identifier

    def arguments(self, types=None):
        """Return a mapping of the argument structure."""
        raise NotImplementedError()

    def properties(self, node_id):
        """Return the morphosemantic properties for *node_id*."""
        raise NotImplementedError()

    def is_quantifier(self, node_id):
        """Return `True` if *node_id* represents a quantifier."""
        raise NotImplementedError()


class ScopingSemanticStructure(SemanticStructure):

    __slots__ = ('index',)

    def __init__(self, top, index, lnk, surface, identifier):
        super().__init__(top, lnk, surface, identifier)
        self.index = index

    def scopal_arguments(self, qeq=None):
        """
        Return scopal arguments in the structure.

        Scopal arguments are those whose value is a range of nodes."""
        raise NotImplementedError()

    def non_scopal_arguments(self):
        """
        Return non-scopal arguments in the structure.

        Non-scopal arguments are those whose value is a single node.
        """
        raise NotImplementedError()

    def scopes(self):
        """
        Return a mapping of scope labels to nodes sharing the scope.
        """
        raise NotImplementedError()
