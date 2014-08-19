import re
import logging
from collections import OrderedDict
from delphin._exceptions import XmrsStructureError
from .config import (
    IVARG_ROLE, CONSTARG_ROLE,
    HANDLESORT, CVARSORT, ANCHOR_SORT, QUANTIFIER_SORT,
    QEQ
)

# VARIABLES, LNKS, and HOOKS

sort_vid_re = re.compile(r'^(\w*\D)(\d+)$')


def sort_vid_split(vs):
    return sort_vid_re.match(vs).groups()


class MrsVariable(object):
    """An MrsVariable has an id (vid), sort, and sometimes properties.

    MrsVariables combine an integer variable ID (or *vid*)) with a
    string sortal type (*sort*). In MRS and RMRS, variables may be the
    bearers of the properties of an |EP| (thus the name "variable
    properties"). MrsVariables are used for several purposes:
    
    * **intrinsic variables** (aka IVs)
    * **handles** (labels or holes)
    * **anchors** (a nodeid with a sort)
    * **variable argument values** (IVs, labels, holes, or
      underspecified variables for unexpressed arguments)

    Example:

    Within an Xmrs structure, a *vid* must be unique. MrsVariables
    can then be compared using either the sort and the vid or the vid
    by itself. For example, ``v1`` and ``v2`` below are not equal
    despite having the same vid (so they should not appear in the same
    Xmrs structure), but they are both equal to their shared vid of
    ``1``. Also note that an MrsVariable can be compared to its string
    representation.

    >>> v1 = MrsVariable(vid=1, sort='x')
    >>> v2 = MrsVariable(vid=1, sort='e')
    >>> v1 == v2
    False
    >>> v1 == 1
    True
    >>> v2 == 1
    True
    >>> v1 == 'x1'
    True
    >>> v1 == 'x2'
    False
    >>> v1 == 'e1'
    False

    Args:
        vid: an number for the variable ID
        sort: a string for the sortal type
        properties: a dictionary of variable properties
    Returns:
        an instantiated MrsVariable object
    Raises:
        ValueError: when *vid* is not castable to an int
    """
    def __init__(self, vid, sort, properties=None):
        # vid is the number of the name (e.g. 1, 10003)
        self.vid = int(vid)
        # sort is the letter(s) of the name (e.g. h, x)
        self.sort = sort
        if sort == HANDLESORT and properties:
            pass  # handles cannot have properties. Log this?
        self.properties = properties or OrderedDict()

    @classmethod
    def from_string(cls, varstring):
        """
        Construct an |MrsVariable| by its string representation.

        Args:
            varstring: a string containing the sort and vid of an
                MrsVariable, such as "x1" or "event3"
        Returns:
            an instantiated MrsVariable object if the string represents
            an MrsVariable, or None otherwise
        """
        srt_vid = sort_vid_split(varstring)
        if srt_vid:
            sort, vid = srt_vid
            return cls(vid, sort)
        return None

    def __eq__(self, other):
        if isinstance(other, MrsVariable):
            return self.vid == other.vid and self.sort == other.sort
        else:
            # it could be a vid like 1 or '1'
            try:
                return self.vid == int(other)
            # or a string like 'x1'
            except ValueError:
                return str(self) == other
            # other is not an int nor a string
            except TypeError:
                return False

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        return 'MrsVariable({}{})'.format(self.sort, self.vid)

    def __str__(self):
        return '{}{}'.format(str(self.sort), str(self.vid))

    @property
    def sortinfo(self):
        """
        Return the properties including a mapping of "cvarsort" to
        the sort of the MrsVariable. Sortinfo is used in DMRS objects,
        which don't have variables, in order to capture the sortal type
        of a |Node|.
        """
        # FIXME: currently gets CVARSORT even if the var is not a IV
        sortinfo = OrderedDict([(CVARSORT, self.sort)])
        sortinfo.update(self.properties)
        return sortinfo


# I'm not sure this belongs here, but anchors are MrsVariables...
class AnchorMixin(object):
    @property
    def anchor(self):
        if self.nodeid is not None:
            return MrsVariable(vid=self.nodeid, sort=ANCHOR_SORT)
        return None

    @anchor.setter
    def anchor(self, anchor):
        self.nodeid = anchor.vid


class VarGenerator(object):
    """Simple class to produce MrsVariables, incrementing the vid for
       each one."""

    def __init__(self, starting_vid=1):
        self.vid = starting_vid

    def new(self, sort, properties=None):
        v = MrsVariable(self.vid, sort, properties=properties)
        self.vid += 1
        return v


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

    # These types determine how a lnk on an EP or MRS are to be
    # interpreted, and thus determine the data type/structure of the
    # lnk data.
    CHARSPAN = 0  # Character span; a pair of offsets
    CHARTSPAN = 1  # Chart vertex span: a pair of indices
    TOKENS = 2  # Token numbers: a list of indices
    EDGE = 3  # An edge identifier: a number

    def __init__(self, data, type):
        if type not in (Lnk.CHARSPAN, Lnk.CHARTSPAN, Lnk.TOKENS, Lnk.EDGE):
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
        return cls((int(start), int(end)), Lnk.CHARSPAN)

    @classmethod
    def chartspan(cls, start, end):
        """
        Create a Lnk object for a chart span.

        Args:
            start: the initial chart vertex
            end: the final chart vertex
        """
        return cls((int(start), int(end)), Lnk.CHARTSPAN)

    @classmethod
    def tokens(cls, tokens):
        """
        Create a Lnk object for a token range.

        Args:
            tokens: a list of token identifiers
        """
        return cls(tuple(map(int, tokens)), Lnk.TOKENS)

    @classmethod
    def edge(cls, edge):
        """
        Create a Lnk object for an edge (used internally in generation).

        Args:
            edge: an edge identifier
        """
        return cls(int(edge), Lnk.EDGE)

    def __str__(self):
        if self.type == Lnk.CHARSPAN:
            return '<{}:{}>'.format(self.data[0], self.data[1])
        elif self.type == Lnk.CHARTSPAN:
            return '<{}#{}>'.format(self.data[0], self.data[2])
        elif self.type == Lnk.EDGE:
            return '<@{}>'.format(self.data)
        elif self.type == Lnk.TOKENS:
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
    if the lnk is not a Lnk.CHARSPAN type).
    """
    @property
    def cfrom(self):
        """
        The initial character position in the surface string. Defaults
        to -1 if there is no valid cfrom value.
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
        The final character position in the surface string. Defaults
        to -1 if there is no valid cto value.
        """
        cto = -1
        try:
            if self.lnk.type == Lnk.CHARSPAN:
                cto = self.lnk.data[1]
        except AttributeError:
            pass  # use default cto of -1
        return cto


class Hook(object):
    """
    A container class for LTOP, INDEX, and XARG.

    This class simply encapsulates three variables associated with an
    |Xmrs| object, and none of the arguments are required.

    Args:
        ltop: the global top handle
        index: the semantic index
        xarg: the external argument (not likely used for a full |Xmrs|)
    """
    def __init__(self, ltop=None, index=None, xarg=None):
        self.ltop = ltop
        self.index = index
        self.xarg = xarg

    def __repr__(self):
        return 'Hook(ltop={} index={} xarg={})'.format(
            self.ltop, self.index, self.xarg
        )

# ARGUMENTS, LINKS, and CONSTRAINTS

class Argument(AnchorMixin):
    """
    An argument of an \*MRS predicate.

    Args:
        nodeid: the nodeid of the node with the argument
        argname: the name of the argument (sometimes called "rargname")
        value: the MrsVariable or constant value of the argument
    """

    INTRINSIC_ARG = 0  # ARG0, conventionally
    VARIABLE_ARG = 1  # The value is the ARG0 of some other EP
    HANDLE_ARG = 2  # The value is a handle (supertype of next two)
    LABEL_ARG = 3  # The value is the label of some other EP(s)
    HCONS_ARG = 4  # The value is the hi variable of an HCONS
    CONSTANT_ARG = 5  # The value is a constant (e.g. a string)

    def __init__(self, nodeid, argname, value):
        self.nodeid = nodeid
        self.argname = argname
        self.value = value
        self._type = None

    def __repr__(self):
        return 'Argument({nodeid}:{argname}:{value})'\
               .format(**self.__dict__)

    def __eq__(self, other):
        # ignore missing nodeid?
        # argname is case insensitive
        snid = self.nodeid
        onid = other.nodeid
        return (
            (None in (snid, onid) or snid == onid) and
            self.argname.lower() == other.argname.lower() and
            self.value == other.value
        )

    @classmethod
    def mrs_argument(cls, argname, value):
        return cls(None, argname, value)

    @classmethod
    def rmrs_argument(cls, anchor, argname, value):
        return cls(anchor.vid, argname, value)

    def infer_argument_type(self, xmrs=None):
        if self.argname == IVARG_ROLE:
            return Argument.INTRINSIC_ARG
        elif isinstance(self.value, MrsVariable):
            if self.value.sort == HANDLESORT:
                # if there's no xmrs given, then use HANDLE_ARG as it
                # is the supertype of LABEL_ARG and HCONS_ARG
                if xmrs is not None:
                    if xmrs.get_hcons(self.value) is not None:
                        return Argument.HCONS_ARG
                    else:
                        return Argument.LABEL_ARG
                else:
                    return Argument.HANDLE_ARG
            else:
                return Argument.VARIABLE_ARG
        else:
            return Argument.CONSTANT_ARG

    @property
    def type(self):
        if self._type is None:
            self._type = self.infer_argument_type()
        return self._type

    @type.setter
    def type(self, value):
        self._type = value


class Link(object):
    """DMRS-style Links are a way of representing arguments without
       variables. A Link encodes a start and end node, the argument
       name, and label information (e.g. label equality, qeq, etc)."""
    def __init__(self, start, end, argname=None, post=None):
        self.start = int(start)
        self.end = int(end)
        self.argname = argname
        self.post = post

    def __repr__(self):
        return 'Link({} -> {}, {}/{})'.format(self.start, self.end,
                                              self.argname, self.post)


class HandleConstraint(object):
    """A relation between two handles."""

    def __init__(self, hi, relation, lo):
        self.hi = hi
        self.relation = relation
        self.lo = lo

    def __eq__(self, other):
        return (self.hi == other.hi and
                self.relation == other.relation and
                self.lo == other.lo)

    def __hash__(self):
        return hash(repr(self))

    def __repr__(self):
        return 'HandleConstraint({})'.format(
               ' '.join([str(self.hi), self.relation, str(self.lo)]))

    def __str__(self):
        return self.__repr__()


def qeq(hi, lo):
    return HandleConstraint(hi, QEQ, lo)


# PREDICATES AND PREDICATIONS

pred_re = re.compile(
    r'_?(?P<lemma>.*?)_'  # match until last 1 or 2 parts
    r'((?P<pos>[a-z])_)?'  # pos is always only 1 char
    r'((?P<sense>([^_\\]|(?:\\.))+)_)?'  # no unescaped _s
    r'(?P<end>rel(ation)?)$',  # NB only _rel is valid
    re.IGNORECASE
)


def is_valid_pred_string(s, suffix_required=True):
    """
    Return True if the given predicate string represents a valid Pred,
    False otherwise. If suffix_required is False, abbreviated Pred
    strings will be accepted (e.g. _dog_n_1 instead of _dog_n_1_rel)
    """
    s = s.strip('"')
    if not suffix_required and s.rsplit('_', 1)[-1] not in ('rel', 'relation'):
        s += '_rel'
    return pred_re.match(s) is not None


def normalize_pred_string(s):
    """
    Make pred strings more consistent by removing quotes and using the
    _rel suffix.
    """
    s = s.strip('"')
    match = pred_re.match(s) or pred_re.match(s + '_rel')
    if match:
        d = match.groupdict()
        tokens = [d['lemma']]
        if d['pos']:
            tokens.append(d['pos'])
        if d['sense']:
            tokens.append(d['sense'])
        tokens.append('rel')
        return '_'.join(tokens)
    return None


class Pred(object):
    """
    A semantic predicate.

    Args:
        predtype: the type of predicate; valid values are grammarpred,
            stringpred, or realpred, although in practice one won't use
            this constructor directly, but instead use one of the
            classmethods
        lemma: the lemma of the predicate
        pos: the part-of-speech; a single, lowercase character
        sense: the (often omitted) sense of the predicate
    Returns:
        an instantiated Pred object

    Preds come in three flavors:
    
    * **grammar preds** (gpreds): preds defined in a semantic hierarchy
      in the grammar, and are not necessarily tied to a lexical entry;
      grammar preds may not begin with a leading underscore
    * **real preds** (realpreds): preds that are defined as the
      composition of a lemma, a part-of-speech (pos), and sometimes a
      sense---parts-of-speech are always single characters, and senses
      may be numbers or string descriptions
    * **string preds** (spreds): a string (often double-quoted) that
      represents a real pred; string preds must begin with a leading
      underscore

    While MRS representations may distinguish real preds and string
    preds, in pyDelphin they are equivalent. All well-formed predicates,
    when represented as strings, end with ``_rel``, but in practice this
    may not be true (some may end in ``_relation``, or have no such
    suffix).

    Example:

        Preds are compared using their string representations.
        Surrounding quotes (double or single) are ignored, and
        capitalization doesn't matter. In addition, preds may be
        compared directly to their string representations:

        >>> p1 = Pred.stringpred('_dog_n_1_rel')
        >>> p2 = Pred.realpred(lemma='dog', pos='n', sense='1')
        >>> p3 = Pred.grammarpred('dog_n_1_rel')
        >>> p1 == p2
        True
        >>> p1 == '_dog_n_1_rel'
        True
        >>> p1 == p3
        False
    """

    # Pred types (used mainly in input/output, not internally in pyDelphin)
    GRAMMARPRED = 0  # only a string allowed (quoted or not)
    REALPRED = 1  # may explicitly define lemma, pos, sense
    STRINGPRED = 2  # quoted string form of realpred

    def __init__(self, predtype, lemma=None, pos=None, sense=None):
        """Extract the lemma, pos, and sense (if applicable) from a pred
           string, if given, or construct a pred string from those
           components, if they are given. Treat malformed pred strings
           as simple preds without extracting the components."""
        # GRAMMARPREDs and STRINGPREDs are given by strings (with or without
        # quotes). STRINGPREDs have an internal structure (defined here:
        # http://moin.delph-in.net/RmrsPos), but basically:
        #   _lemma_pos(_sense)?_rel
        # Note that sense is optional. The initial underscore is meaningful.
        self.type = predtype
        self.lemma = lemma
        self.pos = pos
        self.sense = str(sense) if sense is not None else sense
        self.string = None  # set by class methods

    def __eq__(self, other):

        if isinstance(other, Pred):
            other = other.string
        return self.string.strip('"\'') == other.strip('"\'')

    def __repr__(self):
        return self.string

    def __hash__(self):
        return hash(self.string)

    @classmethod
    def stringpred(cls, predstr):
        lemma, pos, sense, end = Pred.split_pred_string(predstr.strip('"\''))
        pred = cls(Pred.STRINGPRED, lemma=lemma, pos=pos, sense=sense)
        pred.string = predstr
        return pred

    @classmethod
    def grammarpred(cls, predstr):
        lemma, pos, sense, end = Pred.split_pred_string(predstr.strip('"\''))
        pred = cls(Pred.GRAMMARPRED, lemma=lemma, pos=pos, sense=sense)
        pred.string = predstr
        return pred

    @staticmethod
    def string_or_grammar_pred(predstr):
        if predstr.strip('"\'').startswith('_'):
            return Pred.stringpred(predstr)
        else:
            return Pred.grammarpred(predstr)

    @classmethod
    def realpred(cls, lemma, pos, sense=None):
        pred = cls(Pred.REALPRED, lemma=lemma, pos=pos, sense=sense)
        string_tokens = list(filter(bool, [lemma, pos, str(sense or '')]))
        pred.string = '_'.join([''] + string_tokens + ['rel'])
        return pred

    @staticmethod
    def split_pred_string(predstr):
        """
        Extract the components from a pred string and log errors for any
        malformedness.

        Args:
            predstr: a predicate string

        Examples:

            >>> Pred.split_pred_string('_dog_n_1_rel')
            ('dog', 'n', '1', 'rel')
            >>> Pred.split_pred_string('quant_rel')
            ('quant', None, None, 'rel')
        """
        if not predstr.lower().endswith('_rel'):
            logging.warn('Predicate does not end in "_rel": {}'
                         .format(predstr))
        match = pred_re.search(predstr)
        if match is None:
            logging.warn('Unexpected predicate string: {}'.format(predstr))
            return (predstr, None, None, None)
        # _lemma_pos(_sense)?_end
        return (match.group('lemma'), match.group('pos'),
                match.group('sense'), match.group('end'))

    @property
    def short_form(self):
        """
        Return the pred string without quotes or a _rel suffix.

        Example:

            >>> p = Pred.stringpred('"_cat_n_1_rel"')
            >>> p.short_form()
            '_cat_n_1'
        """
        return self.string.strip('"').rsplit('_', 1)[0]

    def is_quantifier(self):
        return self.pos == QUANTIFIER_SORT


class Node(LnkMixin):
    """
    A very simple predication for DMRSs. Nodes don't have |Arguments|
    or labels like |EPs|, but they do have a
    :py:attr:`~delphin.mrs.node.Node.carg` property for constant
    arguments, and their sortal type is given by the `cvarsort` value
    on their property mapping.

    Args:
        nodeid: node identifier
        pred: node's |Pred|
        sortinfo: node properties (with cvarsort)
        lnk: links pred to surface form or parse edges
        surface: surface string
        base: base form
        carg: constant argument string
    """

    def __init__(self, nodeid, pred, sortinfo=None,
                 lnk=None, surface=None, base=None, carg=None):
        self.nodeid = int(nodeid) if nodeid is not None else None
        self.pred = pred
        # sortinfo is the properties plus cvarsort
        self.sortinfo = OrderedDict(sortinfo or [])
        self.lnk = lnk
        self.surface = surface
        self.base = base
        self.carg = carg
        # accessor method
        self.get_property = self.sortinfo.get

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return 'Node({}[{}])'.format(self.nodeid, self.pred)

    def __eq__(self, other):
        # not doing self.__dict__ == other.__dict__ right now, because
        # functions like self.get_property show up there
        snid = self.nodeid
        onid = other.nodeid
        return ((None in (snid, onid) or snid == onid) and
                self.pred == other.pred and
                # make one side a regular dict for unordered comparison
                dict(self.sortinfo.items()) == other.sortinfo and
                self.lnk == other.lnk and
                self.surface == other.surface and
                self.base == other.base and
                self.carg == other.carg)

    @property
    def cvarsort(self):
        """
        The sortal type of the predicate.
        """
        return self.sortinfo.get(CVARSORT)

    @cvarsort.setter
    def cvarsort(self, value):
        self.sortinfo[CVARSORT] = value

    @property
    def properties(self):
        """
        The properties of the Node (without `cvarsort`, so it's the set
        of properties a corresponding |EP| would have).
        """
        return OrderedDict((k, v) for (k, v) in self.sortinfo.items()
                           if k != CVARSORT)

    def is_quantifier(self):
        """
        Return True if the Node is a quantifier, or False otherwise.
        """
        return self.pred.is_quantifier()


def sorted_eps(eps):
    return sorted(eps, key=lambda ep: (ep.cfrom,
                                       ep.cto,
                                       -ep.is_quantifier(),
                                       ep.pred.lemma))


class ElementaryPredication(LnkMixin, AnchorMixin):
    """
    An elementary predication (EP) combines a predicate with various
    structural semantic properties.

    EPs must have a |Pred| and a |MrsVariable| *label*. Well-formed EPs
    will have an intrinsic argument (e.g. ARG0) on their *args* list,
    which specifies the intrinsic variable (IV), though it is not
    required by pyDelphin. However, some methods use an index of IVs to
    calculate semantic structure, so the absence of an intrinsic
    argument could cause unexpected behavior.

    Args:
        pred: The |Pred| of the EP
        label: label handle
        anchor: an |MrsVariable| anchor or int nodeid
        args: a list of the EP's |Arguments|
        lnk: |Lnk| object associated with the pred
        surface: surface string
        base: base form
    """

    def __init__(self, pred, label, anchor=None, args=None,
                 lnk=None, surface=None, base=None):
        self.label = label
        # first args, then can get IV
        self.argdict = OrderedDict((a.argname, a) for a in (args or []))
        # Only fill in other attributes if pred is given, otherwise ignore.
        # This behavior is to help enable the from_node classmethod.
        self._node = None
        if pred is not None:
            iv = self.iv
            self._node = Node(
                anchor.vid if anchor else None,
                pred,
                sortinfo=iv.sortinfo if iv else None,
                lnk=lnk,
                surface=surface,
                base=base,
                carg=self.carg
            )

    @classmethod
    def from_node(cls, label, node, args=None):
        ep = cls(None, label, args=args)
        ep._node = node
        return ep

    def __repr__(self):
        return 'ElementaryPredication({}[{}])'.format(str(self.pred),
                                                      str(self.iv or '?'))

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        return (self.label == other.label and
                self.argdict == other.argdict and
                self._node == other._node)

    # these properties provide an interface to the node attributes

    @property
    def nodeid(self):
        return self._node.nodeid

    @nodeid.setter
    def nodeid(self, value):
        self._node.nodeid = value
        # also update the args' nodeids
        for arg in self.argdict.values():
            arg.nodeid = value

    @property
    def pred(self):
        return self._node.pred

    @pred.setter
    def pred(self, value):
        self._node.pred = value

    @property
    def sortinfo(self):
        return self.iv.sortinfo

    @property
    def lnk(self):
        return self._node.lnk

    @lnk.setter
    def lnk(self, value):
        self._node.lnk = value

    @property
    def surface(self):
        return self._node.surface

    @surface.setter
    def surface(self, value):
        self._node.surface = value

    @property
    def base(self):
        return self._node.base

    @base.setter
    def base(self, value):
        self._node.base = value

    # carg property intentionally left out. It should be accessed from
    # the arg list (see the property below)

    # these properties are specific to the EP's qualities

    @property
    def intrinsic_variable(self):
        return self.arg_value(IVARG_ROLE)

    #: A synonym for :py:meth:`intrinsic_variable`
    iv = intrinsic_variable

    @property
    def properties(self):
        try:
            return self.iv.properties
        except AttributeError:  # in case iv is None
            return OrderedDict()

    @property
    def carg(self):
        return self.arg_value(CONSTARG_ROLE)

    @property
    def args(self):
        return list(self.argdict.values())

    def get_arg(self, rargname):
        return self.argdict.get(rargname)

    def arg_value(self, rargname):
        try:
            arg = self.argdict[rargname]
            return arg.value
        except KeyError:
            return None

    def add_argument(self, arg):
        if arg.nodeid is None:
            arg.nodeid = self.nodeid
        elif arg.nodeid != self.nodeid:
            raise XmrsStructureError(
                "Argument's nodeid must match the EP's (or be None)."
            )
        if arg.argname in self.argdict:
            raise XmrsStructureError(
                "Argument with role {} already exists in the EP."
                .format(arg.argname)
            )
        self.argdict[arg.argname] = arg

    def is_quantifier(self):
        return self.pred.is_quantifier()
