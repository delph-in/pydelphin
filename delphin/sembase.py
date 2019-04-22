
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

