from .config import (CHARSPAN, CHARTSPAN, TOKENS, EDGE)


class Lnk(object):
    """
    Lnk objects link predicates to the surface form in one of several
    ways, the most common of which being the character span of the
    original string.

    Args:
        data: the Lnk specifiers, whose quality depends on *type*
        type: the way the Lnk relates the semantics to the surface form

    Note:
    
        Valid *types* and their associated *data* shown in the table
        below.

        =========  =================================================
        type       data
        =========  =================================================
        charspan   a tuple of start and end character positions from
                   the surface string
        chartspan  a tuple of start and end parse chart vertices
        tokens     a list of token identifiers
        edge       an edge identifier
        =========  =================================================

    Example:

        Lnk objects should be created using the classmethods:

        >>> Lnk.charspan(0,5)
        '<0:5>'
        >>> Lnk.chartspan(0,5)
        '<0#5>'
        >>> Lnk.tokens([0,1,2])
        '<0 1 2>'
        >>> Lnk.edge(1)
        '<@1>'

    """
    def __init__(self, data, type):
        if type not in (CHARSPAN, CHARTSPAN, TOKENS, EDGE):
            raise ValueError('Invalid lnk type: {}'.format(type))
        self.type = type
        self.data = data

    @classmethod
    def charspan(cls, start, end):
        """
        Create a Lnk object for a character span.

        Args:
            start: the initial character position (cfrom)
            end: the final character position (cto)
        """
        return cls((int(start), int(end)), CHARSPAN)

    @classmethod
    def chartspan(cls, start, end):
        """
        Create a Lnk object for a chart span.

        Args:
            start: the initial chart vertex
            end: the final chart vertex
        """
        return cls((int(start), int(end)), CHARTSPAN)

    @classmethod
    def tokens(cls, tokens):
        """
        Create a Lnk object for a token range.

        Args:
            tokens: a list of token identifiers
        """
        return cls(tuple(map(int, tokens)), TOKENS)

    @classmethod
    def edge(cls, edge):
        """
        Create a Lnk object for an edge (used internally in generation).

        Args:
            edge: an edge identifier
        """
        return cls(int(edge), EDGE)

    def __str__(self):
        if self.type == CHARSPAN:
            return '<{}:{}>'.format(self.data[0], self.data[1])
        elif self.type == CHARTSPAN:
            return '<{}#{}>'.format(self.data[0], self.data[2])
        elif self.type == EDGE:
            return '<@{}>'.format(self.data)
        elif self.type == TOKENS:
            return '<{}>'.format(' '.join(self.data))

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return self.type == other.type and self.data == other.data


class LnkMixin(object):
    """
    A mixin class for predications (|EPs| or |Nodes|) or full |Xmrs|
    objects, which are the types that can be linked to surface strings.
    This class provides the :py:attr:`~delphin.mrs.lnk.LnkMixin.cfrom`
    and :py:attr:`~delphin.mrs.lnk.LnkMixin.cto` properties so they are
    always available (defaulting to a value of -1 if there is no lnk or
    if the lnk is not a CHARSPAN type).
    """
    @property
    def cfrom(self):
        """
        The initial character position in the surface string. Defaults
        to -1 if there is no valid cfrom value.
        """
        if self.lnk is not None and self.lnk.type == CHARSPAN:
            return self.lnk.data[0]
        else:
            return -1

    @property
    def cto(self):
        """
        The final character position in the surface string. Defaults
        to -1 if there is no valid cto value.
        """
        if self.lnk is not None and self.lnk.type == CHARSPAN:
            return self.lnk.data[1]
        else:
            return -1
