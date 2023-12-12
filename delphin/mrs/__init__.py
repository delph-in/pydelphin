"""
Minimal Recursion Semantics ([MRS]_).

.. [MRS] Copestake, Ann, Dan Flickinger, Carl Pollard,
  and Ivan A. Sag. "Minimal recursion semantics: An introduction."
  Research on language and computation 3, no. 2-3 (2005): 281-332.
"""

# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401
from delphin.mrs._exceptions import MRSError, MRSSyntaxError
from delphin.mrs._mrs import (
    BODY_ROLE,
    CONSTANT_ROLE,
    EP,
    INTRINSIC_ROLE,
    MRS,
    RESTRICTION_ROLE,
    HCons,
    ICons,
)
from delphin.mrs._operations import (
    compare_bags,
    from_dmrs,
    has_complete_intrinsic_variables,
    has_intrinsic_variable_property,
    has_unique_intrinsic_variables,
    is_connected,
    is_isomorphic,
    is_well_formed,
    plausibly_scopes,
)

__all__ = [
    'INTRINSIC_ROLE',
    'RESTRICTION_ROLE',
    'BODY_ROLE',
    'CONSTANT_ROLE',
    'MRS',
    'EP',
    'HCons',
    'ICons',
    'is_connected',
    'has_intrinsic_variable_property',
    'has_complete_intrinsic_variables',
    'has_unique_intrinsic_variables',
    'is_well_formed',
    'plausibly_scopes',
    'is_isomorphic',
    'compare_bags',
    'from_dmrs',
    'MRSError',
    'MRSSyntaxError',
]
