
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