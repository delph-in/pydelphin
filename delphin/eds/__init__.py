
"""
Elementary Dependency Structures ([EDS]_)

.. [EDS] Stephan Oepen, Dan Flickinger, Kristina Toutanova, and
  Christopher D Manning. Lingo Redwoods. Research on Language and
  Computation, 2(4):575–596, 2004.;

  Stephan Oepen and Jan Tore Lønning. Discriminant-based MRS
  banking. In Proceedings of the 5th International Conference on
  Language Resources and Evaluation, pages 1250–1255, 2006.

"""

from delphin.eds._exceptions import EDSSyntaxError
from delphin.eds._eds import (
    EDS,
    Node,
    BOUND_VARIABLE_ROLE,
    PREDICATE_MODIFIER_ROLE)

__all__ = [
    'BOUND_VARIABLE_ROLE',
    'PREDICATE_MODIFIER_ROLE',
    'EDS',
    'Node',
    'EDSSyntaxError',
]
