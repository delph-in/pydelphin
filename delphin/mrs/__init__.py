# -*- coding: UTF-8 -*-

"""

This module contains classes and methods related to Minimal Recursion
Semantics (Copestake et al. 2005). In addition to MRS, there are the
related formalisms Robust Minimal Recursion Semantics (RMRS;
Copestake, 2003), Elementary Dependency Structures (Oepen and Lønning,
2006), and Dependency Minimal Recursion Semantics (DMRS; Copestake,
2009). In pyDelphin, the greater MRS formalism is referred to as \*MRS
(so "MRS" then refers to the original formalism), and the [Xmrs] class
is implemented to handle all of them (note: RMRS support is postponed
until a need is established).

Users will interact mostly with [Xmrs] objects, but will not often
instantiate them directly. Instead, they are created by serializing
one of the various formats (such as delphin.mrs.simplemrs,
delphin.mrs.mrx, or delphin.mrs.dmrx). No matter
what serialization format (or formalism) is used to load a \*MRS
structure, it will be stored the same way in memory, so any queries or
actions taken on these structures will use the same methods.

Internally, an [Xmrs] object may be built up of various component
classes, such as [ElementaryPredication], [Node], or
[HandleConstraint].
"""

# these may be order-sensitive
from .components import (
    Lnk, Node, ElementaryPredication,
    HandleConstraint, Pred, Link
)
from .xmrs import Xmrs, Mrs, Dmrs, Rmrs

__all__ = [Lnk, Node, ElementaryPredication,
           HandleConstraint, Pred, Link, Xmrs, Mrs, Dmrs]


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
