
"""
Surface alignment for semantic entities.

In DELPH-IN semantic representations, entities are aligned to the
input surface string is through the so-called "lnk" (pronounced
"link") values. There are four types of lnk values which align to the
surface in different ways:

* Character spans (also called "characterization pointers"); e.g.,
  `<0:4>`

* Token indices; e.g., `<0 1 3>`

* Chart vertex spans; e.g., `<0#2>`

* Edge identifier; e.g., `<@42>`

The latter two are unlikely to be encountered by users. Chart vertices
were used by the `PET`_ parser but are now essentially deprecated and
edge identifiers are only used internally in the `LKB`_ for
generation. I will therefore focus on the first two kinds.

.. _`PET`: http://moin.delph-in.net/PetTop
.. _`LKB`: http://moin.delph-in.net/LkbTop

Character spans (sometimes called "characterization pointers") are by
far the most commonly used type---possibly even the only type most
users will encounter. These spans indicate the positions *between*
characters in the input string that correspond to a semantic entity,
similar to how Python and Perl do string indexing. For example,
`<0:4>` would capture the first through fourth characters---a span
that would correspond to the first word in a sentence like "Dogs
bark". These spans assume the input is a flat, or linear, string and
can only select contiguous chunks. Character spans are used by REPP
(the Regular Expression PreProcessor; see :mod:`delphin.repp`) to
track the surface alignment prior to string changes introduced by
tokenization.

Token indices select input tokens rather than characters. This method,
though not widely used, is more suitable for input sources that are
not flat strings (e.g., a lattice of automatic speech recognition
(ASR) hypotheses), or where non-contiguous sequences are needed (e.g.,
from input containing markup or other noise).

.. note::

  Much of this background is from comments in the `LKB`_ source code:
  See: http://svn.emmtee.net/trunk/lingo/lkb/src/mrs/lnk.lisp

Support for lnk values in PyDelphin is rather simple. The :class:`Lnk`
class is able to parse lnk strings and model the contents for
serialization of semantic representations. In addition, semantic
entities such as DMRS :class:`Nodes <delphin.dmrs.Node>` and MRS
:class:`EPs <delphin.mrs.EP>` have `cfrom` and `cto` attributes which
are the start and end pointers for character spans (defaulting to `-1`
if a character span is not specified for the entity).
"""

from delphin.exceptions import PyDelphinException


class LnkError(PyDelphinException):
    """Raised on invalid Lnk values or operations."""


class Lnk(object):
    """
    Surface-alignment information for predications.

    Lnk objects link predicates to the surface form in one of several
    ways, the most common of which being the character span of the
    original string.

    Valid types and their associated *data* shown in the table below.

    =============  ===================  =========
    type           data                 example
    =============  ===================  =========
    Lnk.CHARSPAN   surface string span  (0, 5)
    Lnk.CHARTSPAN  chart vertex span    (0, 5)
    Lnk.TOKENS     token identifiers    (0, 1, 2)
    Lnk.EDGE       edge identifier      1
    =============  ===================  =========

    Args:
        arg: Lnk type or the string representation of a Lnk
        data: alignment data (assumes *arg* is a Lnk type)
    Attributes:
        type: the way the Lnk relates the semantics to the surface form
        data: the alignment data (depends on the Lnk type)

    Example:

        >>> Lnk('<0:5>').data
        (0, 5)
        >>> str(Lnk.charspan(0,5))
        '<0:5>'
        >>> str(Lnk.chartspan(0,5))
        '<0#5>'
        >>> str(Lnk.tokens([0,1,2]))
        '<0 1 2>'
        >>> str(Lnk.edge(1))
        '<@1>'
    """

    __slots__ = ('type', 'data')

    # These types determine how a lnk on an EP or MRS are to be
    # interpreted, and thus determine the data type/structure of the
    # lnk data.
    UNSPECIFIED = -1
    CHARSPAN = 0  # Character span; a pair of offsets
    CHARTSPAN = 1  # Chart vertex span: a pair of indices
    TOKENS = 2  # Token numbers: a list of indices
    EDGE = 3  # An edge identifier: a number

    def __init__(self, arg, data=None):
        if not arg:
            self.type = Lnk.UNSPECIFIED
            self.data = None
        elif data is None and (arg[:1], arg[-1:]) == ('<', '>'):
            arg = arg[1:-1]
            if arg.startswith('@'):
                self.type = Lnk.EDGE
                self.data = int(arg[1:])
            elif ':' in arg:
                cfrom, cto = arg.split(':')
                self.type = Lnk.CHARSPAN
                self.data = (int(cfrom), int(cto))
            elif '#' in arg:
                vfrom, vto = arg.split('#')
                self.type = Lnk.CHARTSPAN
                self.data = (int(vfrom), int(vto))
            else:
                self.type = Lnk.TOKENS
                self.data = tuple(map(int, arg.split()))
        elif arg in (Lnk.CHARSPAN, Lnk.CHARTSPAN, Lnk.TOKENS, Lnk.EDGE):
            self.type = arg
            self.data = data
        else:
            raise LnkError('invalid Lnk: {}'.format(repr((arg, data))))

    @classmethod
    def default(cls):
        """
        Create a Lnk object for when no information is given.
        """
        return cls(None)

    @classmethod
    def charspan(cls, start, end):
        """
        Create a Lnk object for a character span.

        Args:
            start: the initial character position (cfrom)
            end: the final character position (cto)
        """
        return cls(Lnk.CHARSPAN, (int(start), int(end)))

    @classmethod
    def chartspan(cls, start, end):
        """
        Create a Lnk object for a chart span.

        Args:
            start: the initial chart vertex
            end: the final chart vertex
        """
        return cls(Lnk.CHARTSPAN, (int(start), int(end)))

    @classmethod
    def tokens(cls, tokens):
        """
        Create a Lnk object for a token range.

        Args:
            tokens: a list of token identifiers
        """
        return cls(Lnk.TOKENS, tuple(map(int, tokens)))

    @classmethod
    def edge(cls, edge):
        """
        Create a Lnk object for an edge (used internally in generation).

        Args:
            edge: an edge identifier
        """
        return cls(Lnk.EDGE, int(edge))

    def __str__(self):
        if self.type == Lnk.UNSPECIFIED:
            return ''
        elif self.type == Lnk.CHARSPAN:
            return '<{}:{}>'.format(self.data[0], self.data[1])
        elif self.type == Lnk.CHARTSPAN:
            return '<{}#{}>'.format(self.data[0], self.data[1])
        elif self.type == Lnk.EDGE:
            return '<@{}>'.format(self.data)
        elif self.type == Lnk.TOKENS:
            return '<{}>'.format(' '.join(map(str, self.data)))

    def __repr__(self):
        return '<Lnk object {} at {}>'.format(str(self), id(self))

    def __eq__(self, other):
        return self.type == other.type and self.data == other.data

    def __ne__(self, other):
        if not isinstance(other, Lnk):
            return NotImplemented
        return not (self == other)

    def __bool__(self):
        if self.type == Lnk.UNSPECIFIED or not self.data:
            return False
        if self.type == Lnk.CHARSPAN and self.data == (-1, -1):
            return False
        return True


class LnkMixin(object):
    """
    A mixin class for adding `cfrom` and `cto` properties on structures.
    """

    __slots__ = ('lnk', 'surface')

    def __init__(self, lnk=None, surface=None):
        if lnk is None:
            lnk = Lnk.default()
        self.lnk = lnk
        self.surface = surface

    @property
    def cfrom(self):
        """
        The initial character position in the surface string.

        Defaults to -1 if there is no valid cfrom value.
        """
        cfrom = -1
        try:
            if self.lnk.type == Lnk.CHARSPAN:
                cfrom = self.lnk.data[0]
        except AttributeError:
            pass  # use default cfrom of -1
        return cfrom

    @property
    def cto(self):
        """
        The final character position in the surface string.

        Defaults to -1 if there is no valid cto value.
        """
        cto = -1
        try:
            if self.lnk.type == Lnk.CHARSPAN:
                cto = self.lnk.data[1]
        except AttributeError:
            pass  # use default cto of -1
        return cto
