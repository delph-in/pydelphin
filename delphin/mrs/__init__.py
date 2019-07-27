# -*- coding: utf-8 -*-

"""
Minimal Recursion Semantics ([MRS]_).

.. [MRS] Copestake, Ann, Dan Flickinger, Carl Pollard,
  and Ivan A. Sag. "Minimal recursion semantics: An introduction."
  Research on language and computation 3, no. 2-3 (2005): 281-332.
"""

from delphin.mrs._exceptions import MRSError, MRSSyntaxError
from delphin.mrs._mrs import (
    EP,
    HCons,
    ICons,
    MRS,
    INTRINSIC_ROLE,
    RESTRICTION_ROLE,
    BODY_ROLE,
    CONSTANT_ROLE)
from delphin.mrs._operations import (
    is_connected,
    has_intrinsic_variable_property,
    has_complete_intrinsic_variables,
    has_unique_intrinsic_variables,
    is_well_formed,
    plausibly_scopes,
    is_isomorphic,
    compare_bags,
    from_dmrs)
# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401


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
