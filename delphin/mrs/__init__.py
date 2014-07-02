
"""
The MRS package of pyDelphin contains classes and methods related to
Minimal Recursion Semantics (Copestake et al. 2005). A large part of
this package is an object-oriented class system for encapsulating
information relevant to MRS, such as for |ElementaryPredication| and
|HandleConstraint|. It also contains classes for other varieties of
Minimal Recursion Semantics, such as |Node| and |Link| for DMRS.

As this package is capable of handling different varieties of Minimal
Recursion Semantics, I adopt the convention of referring to the greater
formalism as XMRS (an ascii-friendly version of \*MRS), so MRS then
refers to the original formalism. Following this convention, the main
class in this package is |Xmrs|, which is a supertype of MRS, RMRS
(planned), and DMRS.

While you can certainly construct XMRS structures programmatically, most
often you will be using a serialization format (e.g. the XML formats or
SimpleMRS) to read structures from stored representations, and the
codecs to read and write such representations can be found in
:py:mod:`delphin.codecs`.
"""

# notes for future documentation:
# cvs: the variable of the intrinsic
#     argument of an |EP|. Conventionally, the sort of a CV is either
#     ``e`` or ``x``. CVs are sometimes called "distinguished
#     variables", "intrinsic variables", or "ARG0s"
# labels: Every |EP| has a label, which is used to define quantifier
#     scope. When more than one |EP| share a label, they share a scope,
#     and are said to be in an **EP Conjunction**.

# these may be order-sensitive
from .hook import Hook
from .lnk import Lnk
from .node import Node
from .ep import ElementaryPredication
from .var import MrsVariable
from .arg import Argument
from .hcons import HandleConstraint
from .pred import Pred
from .link import Link
from .xmrs import Xmrs
from .mrs import Mrs
from .dmrs import Dmrs

__all__ = [Hook, Lnk, Node, ElementaryPredication, MrsVariable,
           Argument, HandleConstraint, Pred, Link, Xmrs, Mrs, Dmrs]

from . import simplemrs, mrx, dmrx, eds, simpledmrs

serialization_formats = {
    'simplemrs': simplemrs,
    'mrx': mrx,
    'dmrx': dmrx,
    'eds': eds,
    'simpledmrs': simpledmrs
}


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
        of the target format. Some options may include:
        ============  ====================================
         option        description
        ============  ====================================
        pretty_print  print with newlines and indentation
        color         print with syntax highlighting
        ============  ====================================

    Returns:
      A string in the target format.

    Formats:
      src_fmt and tgt_fmt may be one of the following:
        =========  ============================
         format     description
        =========  ============================
        simplemrs  The popular SimpleMRS format
        mrx        The XML format of MRS
        dmrx       The XML format of DMRS
        =========  ============================
    """
    reader = serialization_formats[src_fmt.lower()]
    writer = serialization_formats[tgt_fmt.lower()]
    return writer.dumps(
        reader.loads(txt, single=single),
        single=single,
        **kwargs
    )