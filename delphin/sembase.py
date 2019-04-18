
def role_priority(role):
    """Return a representation of role priority for ordering."""
    # canonical order: LBL ARG* RSTR BODY *-INDEX *-HNDL CARG ...
    role = role.upper()
    return (
        role != 'LBL',
        role in ('BODY', 'CARG'),
        role
    )


def property_priority(prop):
    """
    Return a representation of property priority for ordering.

    Note:
       The ordering provided by this function was modeled on the ERG
       and Jacy grammars and may be irrelevant for others.
    """
    prop = prop.upper()
    proplist = (
        'PERS', 'NUM', 'GEND', 'IND', 'PT', 'PRONTYPE',
        'SF', 'TENSE', 'MOOD', 'PROG', 'PERF', 'ASPECT', 'PASS'
    )
    try:
        return (proplist.index(prop), prop)
    except ValueError:
        return (len(proplist), prop)

