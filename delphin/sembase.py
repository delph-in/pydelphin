
def role_priority(role):
    """Return a representation of role priority for ordering."""
    # canonical order: LBL ARG* RSTR BODY *-INDEX *-HNDL CARG ...
    role = role.upper()
    return (
        role != 'LBL',
        role in ('BODY', 'CARG'),
        role
    )

