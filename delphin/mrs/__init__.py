# -*- coding: utf-8 -*-

"""
This module contains classes and methods related to Minimal
Recursion Semantics [MRS]_. In addition to MRS, there are the related
formalisms Elementary Dependency Structures [EDS]_, and Dependency
Minimal Recursion Semantics [DMRS]_.  As a convenience, \*MRS refers
to the collection of MRS and related formalisms (so "MRS" then refers
to the original formalism), and PyDelphin accordingly defines
:class:`~delphin.mrs.xmrs.Xmrs` as the common subclass for the various
formalisms.

Users will interact mostly with :class:`~delphin.mrs.xmrs.Xmrs`
objects, but will not often instantiate them directly. Instead, they
are created by serializing one of the various formats (such as
:mod:`delphin.mrs.simplemrs`, :mod:`delphin.mrs.mrx`, or
:mod:`delphin.mrs.dmrx`). No matter what serialization format (or
formalism) is used to load a \*MRS structure, it will be stored the
same way in memory, so any queries or actions taken on these structures
will use the same methods.

.. [MRS] Copestake, Ann, Dan Flickinger, Carl Pollard,
  and Ivan A. Sag. "Minimal recursion semantics: An introduction."
  Research on language and computation 3, no. 2-3 (2005): 281-332.
.. [EDS] Stephan Oepen, Dan Flickinger, Kristina Toutanova, and
  Christopher D Manning. Lingo Redwoods. Research on Language and
  Computation, 2(4):575–596, 2004.;

  Stephan Oepen and Jan Tore Lønning. Discriminant-based MRS
  banking. In Proceedings of the 5th International Conference on
  Language Resources and Evaluation, pages 1250–1255, 2006.
.. [DMRS] Copestake, Ann. Slacker Semantics: Why superficiality,
  dependency and avoidance of commitment can be the right way to go.
  In Proceedings of the 12th Conference of the European Chapter of
  the Association for Computational Linguistics, pages 1–9.
  Association for Computational Linguistics, 2009.
"""

# these may be order-sensitive
from .components import (
    Node, ElementaryPredication,
    HandleConstraint, Link
)
from .xmrs import Xmrs, Mrs, Dmrs

from ._exceptions import MRSSyntaxError
from ._mrs import (
    EP,
    HCons,
    ICons,
    MRS,
    INTRINSIC_ROLE,
    RESTRICTION_ROLE,
    BODY_ROLE,
    CONSTANT_ROLE)

__all__ = ['Node', 'ElementaryPredication',
           'HandleConstraint', 'Link', 'Xmrs', 'Mrs', 'Dmrs']
