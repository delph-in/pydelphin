
"""
The `mrs` package of pyDelphin contains classes and methods related to
Minimal Recursion Semantics (Copestake et al. 2005). In addition to
MRS, there are the related formalisms Robust Minimal Recursion Semantics
(RMRS; Copestake, 2003) and Dependency Minimal Recursion Semantics
(DMRS; Copestake, 2009). In pyDelphin, the greater MRS formalism is
referred to as \*MRS (so "MRS" then refers to the original formalism),
and the |Xmrs| class is implemented to handle all of them (note: RMRS
support is postponed until a need is established).

Users will interact mostly with |Xmrs| objects, but will not often
instantiate them directly. Instead, they are created by serializing
one of the various formats (such as :py:mod:`~delphin.mrs.simplemrs`,
:py:mod:`~delphin.mrs.mrx`, or :py:mod:`~delphin.mrs.dmrx`). No matter
what serialization format (or formalism) is used to load a \*MRS
structure, it will be stored the same way in memory, so any queries or
actions taken on these structures will use the same methods.

Internally, an |Xmrs| object may be built up of various component
classes, such as |ElementaryPredication|, |Node|, or
|HandleConstraint|.
"""

# notes for future documentation:
# ivs: the variable of the intrinsic
#     argument of an |EP|. Conventionally, the sort of a IV is either
#     ``e`` or ``x``. IVs are sometimes called "distinguished
#     variables", "characteristic variables", or "ARG0s"
# labels: Every |EP| has a label, which is used to define quantifier
#     scope. When more than one |EP| share a label, they share a scope,
#     and are said to be in an **EP Conjunction**.

# check dependencies

import imp
try:
    imp.find_module('networkx')
except ImportError as ex:
    msg = '''\n
The `networkx` package is required for the `delphin.mrs` package.
You can install `networkx` in several ways:
  * With your operating system\'s package manager (e.g.
    `apt-get install python3-networkx` or `pacman -S python-networkx)
  * With PIP (e.g. `pip install networkx`); make sure you're installing
    for Python3 (you may need to use `pip3` instead of `pip`)
  * Or from the project homepage: http://networkx.github.io'''
    raise ImportError(msg) from ex

# these may be order-sensitive
from .components import (
    Hook, Lnk, Node, ElementaryPredication, MrsVariable, Argument,
    HandleConstraint, Pred, Link
)
from .xmrs import Xmrs, Mrs, Dmrs, Rmrs

__all__ = [Hook, Lnk, Node, ElementaryPredication, MrsVariable,
           Argument, HandleConstraint, Pred, Link, Xmrs, Mrs, Dmrs]


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
    from importlib import import_module
    try:
        reader = import_module('{}.{}'.format('delphin.mrs', src_fmt.lower()))
    except ImportError as ex:
        msg = '\nCannot find serializer: {}'.format(src_fmt.lower())
        raise ImportError(msg) from ex
    try:
        writer = import_module('{}.{}'.format('delphin.mrs', tgt_fmt.lower()))
    except ImportError as ex:
        msg = '\nCannot find serializer: {}'.format(tgt_fmt.lower())
        raise ImportError(msg) from ex
    return writer.dumps(
        reader.loads(txt, single=single),
        single=single,
        **kwargs
    )

#def load(fh, fmt, **kwargs):
#    return loads(fh.read(), fmt, single=single)
#
#def loads(s, fmt, **kwargs):
#    reader = serialization_formats[fmt.lower()]
#    return reader.deserialize_corpus(s, **kwargs)
#
#def dump(fh, x, fmt, **kwargs):
#    print(dumps(x, fmt, **kwargs), file=fh)
#
#def dumps(x, fmt, **kwargs):
#    writer = serialization_formats[fmt.lower()]
#    return writer.serialize_corpus(x, **kwargs)
#
#def load_one(fh, fmt, **kwargs):
#    return loads_one(fh, fmt, **kwargs)
#
#def loads_one(s, fmt, **kwargs):
#    reader = serialization_formats[fmt.lower()]
#    return reader.deserialize_one(s, **kwargs)
#
#def dump_one(fh, x, fmt, **kwargs):
#    print(dumps_one(x, fmt, **kwargs), file=fh)
#
#def dumps_one(x, fmt, **kwargs):
#    writer = serialization_formats[fmt.lower()]
#    return writer.serialize_one(x, **kwargs)
