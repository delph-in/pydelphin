
"""
Elementary Dependency Structures ([EDS]_)

.. [EDS] Stephan Oepen, Dan Flickinger, Kristina Toutanova, and
  Christopher D Manning. Lingo Redwoods. Research on Language and
  Computation, 2(4):575–596, 2004.;

  Stephan Oepen and Jan Tore Lønning. Discriminant-based MRS
  banking. In Proceedings of the 5th International Conference on
  Language Resources and Evaluation, pages 1250–1255, 2006.

"""

from delphin.eds._exceptions import EDSError, EDSSyntaxError
from delphin.eds._eds import (
    BOUND_VARIABLE_ROLE,
    PREDICATE_MODIFIER_ROLE,
    EDS,
    Node,
)
from delphin.eds._operations import (
    from_mrs,
    find_predicate_modifiers,
    make_ids_unique
)
# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401


__all__ = [
    'BOUND_VARIABLE_ROLE',
    'PREDICATE_MODIFIER_ROLE',
    'EDS',
    'Node',
    'from_mrs',
    'find_predicate_modifiers',
    'make_ids_unique',
    'EDSError',
    'EDSSyntaxError',
]
