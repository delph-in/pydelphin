# -*- coding: utf-8 -*-

"""
This module contains classes and methods related to Minimal Recursion
Semantics [MRS]_. In addition to MRS, there are the related formalisms
Robust Minimal Recursion Semantics [RMRS]_, Elementary Dependency
Structures [EDS]_, and Dependency Minimal Recursion Semantics [DMRS]_.
As a convenience, \*MRS refers to the collection of MRS and related
formalisms (so "MRS" then refers to the original formalism), and
PyDelphin accordingly defines :class:`~delphin.mrs.xmrs.Xmrs` as the
common subclass for the various formalisms.

Users will interact mostly with :class:`~delphin.mrs.xmrs.Xmrs`
objects, but will not often instantiate them directly. Instead, they
are created by serializing one of the various formats (such as
:mod:`delphin.mrs.simplemrs`, :mod:`delphin.mrs.mrx`, or
:mod;`delphin.mrs.dmrx`). No matter what serialization format (or
formalism) is used to load a \*MRS structure, it will be stored the
same way in memory, so any queries or actions taken on these structures
will use the same methods.

.. [MRS] Copestake, Ann, Dan Flickinger, Carl Pollard,
  and Ivan A. Sag. "Minimal recursion semantics: An introduction."
  Research on language and computation 3, no. 2-3 (2005): 281-332.
.. [RMRS] Copestake, Ann. "Report on the design of RMRS."
  DeepThought project deliverable (2003).
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
    Lnk, Node, ElementaryPredication,
    HandleConstraint, Pred, Link
)
from .xmrs import Xmrs, Mrs, Dmrs, Rmrs

__all__ = ['Lnk', 'Node', 'ElementaryPredication',
           'HandleConstraint', 'Pred', 'Link', 'Xmrs', 'Mrs', 'Dmrs']


def convert(txt, src_fmt, tgt_fmt, single=True, **kwargs):
    """
    Convert a textual representation of \*MRS from one the src_fmt
    representation to the tgt_fmt representation. By default, only
    read and convert a single \*MRS object (e.g. for `mrx` this
    starts at <mrs> and not <mrs-list>), but changing the `mode`
    argument to `corpus` (alternatively: `list`) reads and converts
    multiple \*MRSs.

    Args:
        txt: A string of semantic data.
        src_fmt: The original representation format of txt.
        tgt_fmt: The representation format to convert to.
        single: If True, assume txt represents a single \*MRS, otherwise
            read it as a corpus (or list) of \*MRSs.
        kwargs: Any other keyword arguments to pass to the serializer
            of the target format. See Notes.
    Returns:
        A string in the target format.
    Notes:
        src_fmt and tgt_fmt may be one of the following:

        | format    | description                  |
        | --------- | ---------------------------- |
        | simplemrs | The popular SimpleMRS format |
        | mrx       | The XML format of MRS        |
        | dmrx      | The XML format of DMRS       |

        Additional keyword arguments for the serializer may include:

        | option       | description                         |
        | ------------ | ----------------------------------- |
        | pretty_print | print with newlines and indentation |
        | color        | print with syntax highlighting      |
    """
    from importlib import import_module
    reader = import_module('{}.{}'.format('delphin.mrs', src_fmt.lower()))
    writer = import_module('{}.{}'.format('delphin.mrs', tgt_fmt.lower()))
    return writer.dumps(
        reader.loads(txt, single=single),
        single=single,
        **kwargs
    )
