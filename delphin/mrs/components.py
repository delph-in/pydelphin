import re
import logging
from collections import OrderedDict, namedtuple
from itertools import starmap
from functools import total_ordering

from delphin._exceptions import XmrsStructureError
from .config import (
    IVARG_ROLE, CONSTARG_ROLE,
    HANDLESORT, CVARSORT, ANCHOR_SORT, QUANTIFIER_POS,
    EQ_POST, HEQ_POST, NEQ_POST, H_POST
)

# VARIABLES, LNKS, and HOOKS

@total_ordering
class MrsVariable(namedtuple('MrsVariable', ('varstring', 'properties'))):
    """An MrsVariable has an id (vid), sort, and sometimes properties.

    MrsVariables combine an integer variable ID (or *vid*)) with a
    string sortal type (*sort*). In MRS and RMRS, variables may be the
    bearers of the properties of an |EP| (thus the name "variable
    properties"). MrsVariables are used for several purposes:

    * **intrinsic variables** (aka IVs)
    * **handles** (labels or holes)
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
    def __new__(cls, varstring, properties=None):
        return super(MrsVariable, cls).__new__(
            cls, varstring, properties
        )
        # # vid is the number of the name (e.g. 1, 10003)
        # self.vid = int(vid)
        # # sort is the letter(s) of the name (e.g. h, x)
        # self.sort = sort
        # if sort == HANDLESORT and properties:
        #     pass  # handles cannot have properties. Log this?
        # self.properties = properties or OrderedDict()

    # @classmethod
    # def from_vidsort(cls, vid, sort, properties=None):
    #     """
    #     """
    #     if sort is None:
    #         sort = 'u'
    #     varstring = '{}{}'.format(sort, vid)
    #     vid = int(vid)
    #     var = cls(varstring, properties=properties)
    #     # might as well set these now
    #     var[2] = vid
    #     var[3] = sort
    #     return var

    # @classmethod
    # def anchor(cls, vid):
    #     return cls(vid, ANCHOR_SORT)

    def __eq__(self, other):
        vareq = str(self).lower() == str(other).lower()
        return vareq and (getattr(self, 'properties', None) ==
                          getattr(other, 'properties', None))
        # try both as MrsVariables
        # try:
        #     return self.vid == other.vid and self.sort == other.sort
        # except AttributeError:
        #     pass  # other is not an MrsVariable
        # # attempt as string
        # try:
        #     sort, vid = MrsVariable.sort_vid_split(other)
        #     return self.sort == sort and self.vid == int(vid)
        # except (ValueError, TypeError):
        #     pass  # doesn't match a variable
        # # try again as vid only
        # try:
        #     vid = int(other)
        #     return self.vid == vid
        # except (ValueError, TypeError):
        #     pass  # nope.. return False
        # return False

    def __lt__(self, other):
        split = sort_vid_split
        vid1 = int(split(self[0])[1])
        vid2 = int(split(str(other))[1])
        return vid1 < vid2
        # # only compare vids for lt
        # try:
        #     return vid1 < int(other)
        # except (ValueError, TypeError):
        #     pass  # not an int or MrsVariable
        # # try as a string
        # try:
        #     sort, vid2 = MrsVariable.sort_vid_split(other)
        #     return vid1 < int(vid2)
        # except (ValueError, TypeError):
        #     pass  # not a string... no good output
        # raise ValueError('Cannot compare MrsVariable to {} of type {}'
        #                  .format(str(other), type(other)))

    # def __int__(self):
    #     return self.vid

    def __hash__(self):
        return hash(self[0])

    def __repr__(self):
        return '<MrsVariable object ({}) at {}>'.format(
            self[0], id(self)
        )

    def __str__(self):
        # if sort is None, go with the default of 'u'
        return self[0] #'{}{}'.format(str(self.sort or 'u'), str(self.vid))

    # @property
    # def sortinfo(self):
    #     """
    #     Return the properties including a mapping of "cvarsort" to
    #     the sort of the MrsVariable. Sortinfo is used in DMRS objects,
    #     which don't have variables, in order to capture the sortal type
    #     of a |Node|.
    #     """
    #     # FIXME: currently gets CVARSORT even if the var is not a IV
    #     sortinfo = OrderedDict([(CVARSORT, self.sort)])
    #     sortinfo.update(self.properties)
    #     return sortinfo


var_re = re.compile(r'^(\w*\D)(\d+)$')


def sort_vid_split(vs):
    try:
        sort, vid = var_re.match(vs).groups()
        return sort, vid
    except AttributeError:
        raise ValueError('Invalid variable string: {}'.format(str(vs)))


# I'm not sure this belongs here, but anchors are MrsVariables...
# class AnchorMixin(object):
#     @property
#     def anchor(self):
#         """
#         The anchor of the |EP|, |Node|, or |Argument| is just the
#         nodeid wrapped in an MrsVariable. In |Xmrs| functions, integer
#         nodeids are used instead of anchors.
#         """
#         if self.nodeid is not None:
#             return MrsVariable(vid=self.nodeid, sort=ANCHOR_SORT)
#         return None

#     @anchor.setter
#     def anchor(self, anchor):
#         self.nodeid = anchor.vid


class VarGenerator(object):
    """Simple class to produce MrsVariables, incrementing the vid for
       each one."""

    def __init__(self, starting_vid=1):
        self.vid = starting_vid

    def new(self, sort, properties=None):
        v = MrsVariable(self.vid, sort, properties=properties)
        self.vid += 1
        return v


class Lnk(namedtuple('Lnk', ('type', 'data'))):
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
        if self.type == Lnk.CHARSPAN:
            return '<{}:{}>'.format(self.data[0], self.data[1])
        elif self.type == Lnk.CHARTSPAN:
            return '<{}#{}>'.format(self.data[0], self.data[2])
        elif self.type == Lnk.EDGE:
            return '<@{}>'.format(self.data)
        elif self.type == Lnk.TOKENS:
            return '<{}>'.format(' '.join(self.data))

    def __repr__(self):
        return '<Lnk object {} at {}>'.format(str(self), id(self))

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


# namedtuple with defaults. thanks: http://stackoverflow.com/a/16721002/1441112
class Hook(namedtuple('Hook', ['top', 'index', 'xarg'])):
    """
    A container class for TOP, INDEX, and XARG.

    This class simply encapsulates three variables associated with an
    |Xmrs| object, and none of the arguments are required.

    Args:
        top: the global top handle
        index: the semantic index
        xarg: the external argument (not likely used for a full |Xmrs|)
        ltop: an alternate spelling of top (top is preferred)
    """
    def __new__(cls, top=None, index=None, xarg=None):
        return super(Hook, cls).__new__(cls, top, index, xarg)

    def __repr__(self):
        return '<Hook object (top={} index={} xarg={}) at {}>'.format(
            self.top, self.index, self.xarg, id(self)
        )

    # def __eq__(self, other):
    #     if not isinstance(other, Hook):
    #         return False
    #     return (
    #         self.top == other.top and
    #         self.index == other.index and
    #         self.xarg == other.xarg
    #     )

    # for compatibility
    @property
    def ltop(self):
        return self.top

    @ltop.setter
    def ltop(self, value):
        self.top = value


# ARGUMENTS, LINKS, and CONSTRAINTS

# class Argument(namedtuple('Argument',
#                           ('nodeid', 'rargname', 'value', 'type'))):
#     """
#     An argument of an \*MRS predicate.

#     Args:
#         nodeid: the nodeid of the node with the argument
#         rargname: the role argument name
#         value: the MrsVariable or constant value of the argument
#     """

#     CONSTANT_ARG = 0  # value is a constant (e.g. a string)
#     VARIABLE_ARG = 1  # value is a variable: MrsVariable or (var, props) tuple

#     def __new__(cls, nodeid, rargname, value, type=None):
#         if type is None:
#             # if value is a string (from a CARG) then value[0] still
#             # fails the var_re match, which is ok
#             var = value[0] if value else ''
#             if rargname.upper() == CONSTARG_ROLE or not var_re.match(var):
#                 type = Argument.CONSTANT_ARG
#             else:
#                 type = Argument.VARIABLE_ARG
#         return super(Argument, cls).__new__(
#             cls, nodeid, rargname, value, type
#         )

#     # def __init__(self, nodeid, rargname, value):
#     #     self.nodeid = nodeid
#     #     self.rargname = rargname
#     #     self.value = value
#         # self._type = None

#     def __repr__(self):
#         return '<Argument object ({}:{}:{}) at {}>'.format(
#             self.nodeid, self.rargname, self.value, id(self)
#         )

#     # def __eq__(self, other):
#     #     # ignore missing nodeid?
#     #     # rargname is case insensitive
#     #     snid = self.nodeid
#     #     onid = other.nodeid
#     #     return (
#     #         (None in (snid, onid) or snid == onid) and
#     #         self.rargname.lower() == other.rargname.lower() and
#     #         self.value == other.value
#     #     )

#     @classmethod
#     def mrs_argument(cls, rargname, value, type=None):
#         return cls(None, rargname, value, type=type)

#     # @classmethod
#     # def rmrs_argument(cls, anchor, rargname, value):
#     #     return cls(anchor.vid, rargname, value)

#     # def infer_argument_type(self, xmrs=None):
#     #     if self.rargname == IVARG_ROLE:
#     #         return Argument.INTRINSIC_ARG
#     #     elif isinstance(self.value, MrsVariable):
#     #         if self.value.sort == HANDLESORT:
#     #             # if there's no xmrs given, then use HANDLE_ARG as it
#     #             # is the supertype of LABEL_ARG and HCONS_ARG
#     #             if xmrs is not None:
#     #                 if xmrs.get_hcons(self.value) is not None:
#     #                     return Argument.HCONS_ARG
#     #                 else:
#     #                     return Argument.LABEL_ARG
#     #             else:
#     #                 return Argument.HANDLE_ARG
#     #         else:
#     #             return Argument.VARIABLE_ARG
#     #     else:
#     #         return Argument.CONSTANT_ARG

#     # @property
#     # def type(self):
#     #     if self._type is None:
#     #         self._type = self.infer_argument_type()
#     #     return self._type

#     # @type.setter
#     # def type(self, value):
#     #     self._type = value


# def args(xmrs):
#     """The list of all |Arguments|."""
#     return list(chain.from_iterable(ep.args for ep in xmrs.eps))


class Link(namedtuple('Link', ('start', 'end', 'rargname', 'post'))):
    """DMRS-style Links are a way of representing arguments without
       variables. A Link encodes a start and end node, the argument
       name, and label information (e.g. label equality, qeq, etc)."""
    # def __init__(self, start, end, rargname=None, post=None):
    #     self.start = int(start)
    #     self.end = int(end)
    #     self.rargname = rargname
    #     self.post = post

    def __repr__(self):
        return '<Link object (#{} :{}/{}> #{}) at {}>'.format(
            self.start, self.rargname or '', self.post, self.end, id(self)
        )


def links(xmrs):
    """The list of |Links|."""
    # Return the set of links for the XMRS structure. Links exist for
    # every non-intrinsic argument that has a variable that is the
    # intrinsic variable of some other predicate, as well as for label
    # equalities when no argument link exists (even considering
    # transitivity).
    links = []
    prelinks = []
    _eps = xmrs._eps
    _vars = xmrs._vars
    top = xmrs.top
    if top is not None:
        prelinks.append((0, top, None, _vars[xmrs.top]))
    for nid, ep in _eps.items():
        for role, val in ep[3].items():
            if role == IVARG_ROLE or val not in _vars:
                continue
            prelinks.append((nid, ep[2], role, _vars[val]))
    for src, srclbl, role, vd in prelinks:
        if 'iv' in vd:
            tgt = vd['iv']
            tgtlbl = _eps[tgt][2]
            post = EQ_POST if srclbl == tgtlbl else NEQ_POST
        elif 'hcons' in vd:
            lbl = vd['hcons'][2]
            if lbl not in _vars:
                continue
            # the LBL ref list should already be sorted by headedness
            tgt = _vars[lbl]['refs']['LBL'][0]
            post = H_POST
        elif 'LBL' in vd['refs']:
            tgt = vd['refs']['LBL'][0]  # again, should be sorted already
            post = HEQ_POST
        else:
            continue  # CARGs, maybe?
        links.append(Link(src, tgt, role, post))

    # # g = xmrs._graph
    # nids = set(g.nodeids)
    # labels = g.labels
    # attested_eqs = defaultdict(set)
    # for s, t, d in g.out_edges_iter([LTOP_NODEID] + g.nodeids, data=True):
    #     try:
    #         t_d = g.node[t]
    #         if t_d.get('iv') == s or t_d.get('bv') == s:
    #             continue  # ignore ARG0s
    #         if 'iv' in t_d and t_d['iv'] is not None:
    #             t = t_d['iv']
    #             s_lbl = g.node[s].get('label')  # LTOP_NODEID has no label
    #             t_lbl = g.node[t]['label']
    #             if s_lbl == t_lbl:
    #                 post = EQ_POST
    #                 attested_eqs[s_lbl].update([s, t])
    #             else:
    #                 post = NEQ_POST
    #         elif 'hcons' in t_d:
    #             lbl = t_d['hcons'].lo
    #             # if s is a quantifier and the quantifiee is in the
    #             # the target set, use the quantifiee
    #             s_iv = g.node[s].get('iv')
    #             if s_iv and g.node[s_iv]['iv'] in xmrs.labelset(lbl):
    #                 t = g.node[s_iv]['iv']
    #             else:
    #                 t = xmrs.labelset_head(lbl)
    #             post = H_POST
    #         elif t in g.labels:
    #             t = xmrs.labelset_head(t)
    #             post = HEQ_POST
    #         else:
    #             continue  # maybe log this
    #         links.append(Link(s, t, d.get('rargname'), post))
    #     except XmrsError as ex:
    #         warnings.warn(
    #             'Error creating a link for {}:{}:\n  {}'
    #             .format(s, d.get('rargname', ''), repr(ex))
    #         )

    # now EQ links unattested by arg links
    # for lbl in g.labels:
    #     # I'm pretty sure this does what we want
    #     heads = self.labelset_head(lbl, single=False)
    #     if len(heads) > 1:
    #         first = heads[0]
    #         for other in heads[1:]:
    #             links.append(Link(first, other, None, post=EQ_POST))
        # If not, this is more explicit
        # lblset = self.labelset(lbl)
        # sg = g.subgraph(lblset)
        # ns = [nid for nid, deg in sg.degree(lblset).items() if deg == 0]
        # head = self.labelset_head(lbl)
        # for n in ns:
        #     links.append(Link(head, n, post=EQ_POST))
    return sorted(links)#, key=lambda link: (link.start, link.end))


class HandleConstraint(
        namedtuple('HandleConstraint', ('hi', 'relation', 'lo'))):
    """A relation between two handles."""

    QEQ = 'qeq'  # Equality modulo Quantifiers
    LHEQ = 'lheq'  # Label-Handle Equality
    OUTSCOPES = 'outscopes'  # Outscopes

    # def __init__(self, hi, relation, lo):
    #     self.hi = hi
    #     self.relation = relation
    #     self.lo = lo

    @classmethod
    def qeq(cls, hi, lo):
        return cls(hi, HandleConstraint.QEQ, lo)

    # def __eq__(self, other):
    #     return (self.hi == other.hi and
    #             self.relation == other.relation and
    #             self.lo == other.lo)

    # def __hash__(self):
    #     return hash(repr(self))

    def __repr__(self):
        return '<HandleConstraint object ({} {} {}) at {}>'.format(
               str(self.hi), self.relation, str(self.lo), id(self)
        )


def hcons(xmrs):
    """The list of all |HandleConstraints|."""
    return sorted(
        (HandleConstraint(*vd['hcons'])
         for vd in xmrs._vars.values() if 'hcons' in vd),
        key=lambda hc: int(sort_vid_split(hc[0])[1])
    )
    # nodes = xmrs._graph.nodes(data=True)
    # return sorted((data['hcons'] for _, data in nodes if 'hcons' in data),
    #               key=lambda hc: hc.hi.vid)


IndividualConstraint = namedtuple('IndividualConstraint',
                                  ['left', 'relation', 'right'])


def icons(xmrs):
    """The list of all |IndividualConstraints|."""
    return sorted(
        (IndividualConstraint(*vd['icons'])
         for vd in xmrs._vars.values() if 'icons' in vd),
        key=lambda ic: int(sort_vid_split(ic[0])[1])
    )

    # nodes = xmrs._graph.nodes(data=True)
    # return sorted((data['icons'] for _, data in nodes if 'icons' in data),
    #               key=lambda ic: ic.left.vid)


# PREDICATES AND PREDICATIONS


class Pred(namedtuple('Pred', ('type', 'lemma', 'pos', 'sense', 'string'))):
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
    pred_re = re.compile(
        r'_?(?P<lemma>.*?)_'  # match until last 1 or 2 parts
        r'((?P<pos>[a-z])_)?'  # pos is always only 1 char
        r'((?P<sense>([^_\\]|(?:\\.))+)_)?'  # no unescaped _s
        r'(?P<end>rel(ation)?)$',  # NB only _rel is valid
        re.IGNORECASE
    )
    # Pred types (used mainly in input/output, not internally in pyDelphin)
    GRAMMARPRED = 0  # only a string allowed (quoted or not)
    REALPRED = 1  # may explicitly define lemma, pos, sense
    STRINGPRED = 2  # quoted string form of realpred

    # def __new__(cls, predtype, lemma=None, pos=None, sense=None, string=None):
    #     """Extract the lemma, pos, and sense (if applicable) from a pred
    #        string, if given, or construct a pred string from those
    #        components, if they are given. Treat malformed pred strings
    #        as simple preds without extracting the components."""
    #     # GRAMMARPREDs and STRINGPREDs are given by strings (with or without
    #     # quotes). STRINGPREDs have an internal structure (defined here:
    #     # http://moin.delph-in.net/RmrsPos), but basically:
    #     #   _lemma_pos(_sense)?_rel
    #     # Note that sense is optional. The initial underscore is meaningful.
    #     return super(Pred, cls).__new__(
    #         cls, predtype, lemma, pos, sense, string
    #     )

        # self.type = predtype
        # self.lemma = lemma
        # self.pos = pos
        # self.sense = str(sense) if sense is not None else sense
        # self.string = None  # set by class methods

    def __eq__(self, other):
        if other is None:
            return False
        if isinstance(other, Pred):
            other = other.string
        return self.string.strip('"\'') == other.strip('"\'')

    def __str__ (self):
        return self.string

    def __repr__(self):
        return '<Pred object {} at {}>'.format(self.string, id(self))

    def __hash__(self):
        return hash(self.string)

    @classmethod
    def stringpred(cls, predstr):
        lemma, pos, sense, end = split_pred_string(predstr.strip('"\''))
        return cls(Pred.STRINGPRED, lemma, pos, sense, predstr)

    @classmethod
    def grammarpred(cls, predstr):
        lemma, pos, sense, end = split_pred_string(predstr.strip('"\''))
        return cls(Pred.GRAMMARPRED, lemma, pos, sense, predstr)

    @staticmethod
    def string_or_grammar_pred(predstr):
        if predstr.strip('"').lstrip("'").startswith('_'):
            return Pred.stringpred(predstr)
        else:
            return Pred.grammarpred(predstr)

    @classmethod
    def realpred(cls, lemma, pos, sense=None):
        string_tokens = list(filter(bool, [lemma, pos, str(sense or '')]))
        predstr = '_'.join([''] + string_tokens + ['rel'])
        return cls(Pred.REALPRED, lemma, pos, sense, predstr)

    def short_form(self):
        """
        Return the pred string without quotes or a _rel suffix.

        Example:

            >>> p = Pred.stringpred('"_cat_n_1_rel"')
            >>> p.short_form()
            '_cat_n_1'
        """
        return self.string.strip('"').lstrip("'").rsplit('_', 1)[0]

    def is_quantifier(self):
        return self.pos == QUANTIFIER_POS


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
        logging.debug('Predicate does not end in "_rel": {}'
                      .format(predstr))
    match = Pred.pred_re.search(predstr)
    if match is None:
        logging.debug('Unexpected predicate string: {}'.format(predstr))
        return (predstr, None, None, None)
    # _lemma_pos(_sense)?_end
    return (match.group('lemma'), match.group('pos'),
            match.group('sense'), match.group('end'))


def is_valid_pred_string(predstr, suffix_required=True):
    """
    Return True if the given predicate string represents a valid
    Pred, False otherwise. If suffix_required is False,
    abbreviated Pred strings will be accepted (e.g. _dog_n_1
    instead of _dog_n_1_rel)
    """
    predstr = predstr.strip('"').lstrip("'")
    if (not suffix_required and
        predstr.rsplit('_', 1)[-1] not in ('rel', 'relation')):
        predstr += '_rel'
    return Pred.pred_re.match(predstr) is not None


def normalize_pred_string(predstr):
    """
    Make pred strings more consistent by removing quotes and using
    the _rel suffix.
    """
    predstr = predstr.strip('"').lstrip("'")
    match = (Pred.pred_re.match(predstr) or
             Pred.pred_re.match(predstr + '_rel'))
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


@total_ordering
class Node(
    namedtuple('Node', ('nodeid', 'pred', 'sortinfo',
                        'lnk', 'surface', 'base', 'carg')),
    LnkMixin):
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

    def __new__(cls, nodeid, pred, sortinfo=None,
                 lnk=None, surface=None, base=None, carg=None):
        if sortinfo is None:
            sortinfo = {}
        return super(Node, cls).__new__(
            cls, nodeid, pred, sortinfo, lnk, surface, base, carg
        )
        # self.nodeid = int(nodeid) if nodeid is not None else None
        # self.pred = pred
        # # sortinfo is the properties plus cvarsort
        # self.sortinfo = OrderedDict(sortinfo or [])
        # self.lnk = lnk
        # self.surface = surface
        # self.base = base
        # self.carg = carg
        # # accessor method
        # self.get_property = self.sortinfo.get

    def __repr__(self):
        lnk = ''
        if self.lnk is not None:
            lnk = str(self.lnk)
        return '<Node object ({} [{}{}]) at {}>'.format(
            self.nodeid, self.pred.string, lnk, id(self)
        )

    # note: without overriding __eq__, comparisons of sortinfo will be
    #       be different if they are OrderedDicts and not in the same
    #       order. Maybe this isn't a big deal?
    # def __eq__(self, other):
    #     # not doing self.__dict__ == other.__dict__ right now, because
    #     # functions like self.get_property show up there
    #     snid = self.nodeid
    #     onid = other.nodeid
    #     return ((None in (snid, onid) or snid == onid) and
    #             self.pred == other.pred and
    #             # make one side a regular dict for unordered comparison
    #             dict(self.sortinfo.items()) == other.sortinfo and
    #             self.lnk == other.lnk and
    #             self.surface == other.surface and
    #             self.base == other.base and
    #             self.carg == other.carg)

    def __lt__(self, other):
        x1 = (self.cfrom, self.cto, -self.is_quantifier(), self.pred.lemma)
        try:
            x2 = (other.cfrom, other.cto, -other.is_quantifier(),
                  other.pred.lemma)
            return x1 < x2
        except AttributeError:
            return False  # comparing Node to non-Node means Node is greater?

    @property
    def cvarsort(self):
        """
        The sortal type of the predicate.
        """
        return self.sortinfo.get(CVARSORT)

    @cvarsort.setter
    def cvarsort(self, value):
        self.sortinfo[CVARSORT] = value

    # @property
    # def properties(self):
    #     """
    #     The properties of the Node (without `cvarsort`, so it's the set
    #     of properties a corresponding |EP| would have).
    #     """
    #     return OrderedDict((k, v) for (k, v) in self.sortinfo.items()
    #                        if k != CVARSORT)

    def is_quantifier(self):
        """
        Return True if the Node is a quantifier, or False otherwise.
        """
        return self.pred.is_quantifier()

def nodes(xmrs):
    """The list of Nodes."""
    nodes = []
    _vars = xmrs._vars
    varsplit = sort_vid_split
    for ep in xmrs._eps.values():
        eplen = len(ep)
        nid = ep[0]
        pred = ep[1]
        args = ep[3]
        sortinfo = lnk = surface = base = None
        iv = args.get(IVARG_ROLE, None)
        if iv is not None:
            sort, _ = varsplit(iv)
            sortinfo = _vars[iv].get('props', {})
            sortinfo[CVARSORT] = sort
        if eplen >= 5:
            lnk = ep[4]
        if eplen >= 6:
            surface = ep[5]
        if eplen >= 7:
            base = ep[6]
        carg = args.get(CONSTARG_ROLE, None)
        nodes.append(Node(nid, pred, sortinfo, lnk, surface, base, carg))
    return sorted(nodes)


@total_ordering
class ElementaryPredication(
    namedtuple('ElementaryPredication',
               ('nodeid', 'pred', 'label', 'args', 'lnk', 'surface', 'base')),
    LnkMixin):
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
        nodeid: an int nodeid
        args: a list of the EP's |Arguments|
        lnk: |Lnk| object associated with the pred
        surface: surface string
        base: base form
    """

    def __new__(cls, nodeid, pred, label, args=None,
                 lnk=None, surface=None, base=None):
        if args is None:
            args = {}
        # else:
        #     args = dict((a.rargname, a) for a in args)
        return super(ElementaryPredication, cls).__new__(
            cls, nodeid, pred, label, args, lnk, surface, base
        )

        # self.label = label
        # # first args, then can get IV
        # self.argdict = OrderedDict((a.rargname, a) for a in (args or []))
        # # Only fill in other attributes if pred is given, otherwise ignore.
        # # This behavior is to help enable the from_node classmethod.
        # self._node = None
        # # if nodeid is None and anchor is not None:
        # #     nodeid = anchor.vid
        # if pred is not None:
        #     iv = self.iv
        #     self._node = Node(
        #         nodeid,
        #         pred,
        #         sortinfo=iv.sortinfo if iv else None,
        #         lnk=lnk,
        #         surface=surface,
        #         base=base,
        #         carg=self.carg
        #     )

    # @classmethod
    # def from_node(cls, label, node, args=None):
    #     ep = cls(None, label, args=args)
    #     ep._node = node
    #     return ep

    def __repr__(self):
        return '<ElementaryPredication object ({} ({})) at {}>'.format(
            self.pred.string, str(self.iv or '?'), id(self)
        )

    # def __eq__(self, other):
    #     return (self.label == other.label and
    #             self.argdict == other.argdict and
    #             self._node == other._node)

    def __lt__(self, other):
        x1 = (self.cfrom, self.cto, -self.is_quantifier(), self.pred.lemma)
        try:
            x2 = (other.cfrom, other.cto, -other.is_quantifier(),
                  other.pred.lemma)
            return x1 < x2
        except AttributeError:
            return False  # comparing EP to non-EP means EP is greater?

    # these properties are specific to the EP's qualities

    @property
    def intrinsic_variable(self):
        if IVARG_ROLE in self.args:
            return self.args[IVARG_ROLE]
        return None

    #: A synonym for :py:meth:`intrinsic_variable`
    iv = intrinsic_variable

    @property
    def properties(self):
        iv = self.iv
        if iv is not None:
            return iv.properties
        return {}

    @property
    def carg(self):
        return self.args.get(CONSTARG_ROLE, None)

    def add_argument(self, arg):
        if arg.nodeid is None:
            arg.nodeid = self.nodeid
        elif arg.nodeid != self.nodeid:
            raise XmrsStructureError(
                "Argument's nodeid must match the EP's (or be None)."
            )
        if arg.rargname in self.args:
            raise XmrsStructureError(
                "Argument with role {} already exists in the EP."
                .format(arg.rargname)
            )
        self.args[arg.rargname] = arg

    def is_quantifier(self):
        return self.pred.is_quantifier()


def eps(xmrs):
    """The list of |ElementaryPredications|."""
    return list(starmap(ElementaryPredication, xmrs._eps.values()))

def get_ep(xmrs, nodeid):
    """
    Retrieve the EP with the given nodeid, or raises KeyError if no
    EP matches.

    Args:
        nodeid: The nodeid of the EP to return.
    Returns:
        An ElementaryPredication.
    """
    return ElementaryPredication(*xmrs._eps[nodeid])
    # try:
    #     d = xmrs._graph.node[nodeid]
    #     args = [(nodeid, rargname, value)
    #             for rargname, value in d['rargs'].items()]
    #     ep = ElementaryPredication(
    #         nodeid=nodeid,
    #         pred=d['pred'],
    #         label=d['label'],
    #         args=args,
    #         lnk=d.get('lnk'),
    #         surface=d.get('surface'),
    #         base=d.get('base')
    #     )
    #     return ep
    # except KeyError:
    #     return None

