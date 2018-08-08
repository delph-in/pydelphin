
"""
Classes and functions for working with the components of \*MRS objects.
"""

import re
import logging
import warnings
from collections import namedtuple, MutableMapping
from itertools import starmap

from delphin.exceptions import (XmrsError, XmrsStructureError)
from delphin.util import deprecated
from .config import (
    IVARG_ROLE, CONSTARG_ROLE, RSTR_ROLE,
    UNKNOWNSORT, HANDLESORT, CVARSORT, QUANTIFIER_POS,
    EQ_POST, HEQ_POST, NEQ_POST, H_POST,
    BARE_EQ_ROLE
)

# The classes below are generally just namedtuples with extra methods.
# The namedtuples sometimes have default values. thanks:
#   http://stackoverflow.com/a/16721002/1441112


# VARIABLES and LNKS

var_re = re.compile(r'^([-\w]*\D)(\d+)$')


def sort_vid_split(vs):
    """
    Split a valid variable string into its variable sort and id.

    Examples:
        >>> sort_vid_split('h3')
        ('h', '3')
        >>> sort_vid_split('ref-ind12')
        ('ref-ind', '12')
    """
    match = var_re.match(vs)
    if match is None:
        raise ValueError('Invalid variable string: {}'.format(str(vs)))
    else:
        return match.groups()


def var_sort(v):
    """
    Return the sort of a valid variable string.

    Examples:
        >>> var_sort('h3')
        'h'
        >>> var_sort('ref-ind12')
        'ref-ind'
    """
    return sort_vid_split(v)[0]


def var_id(v):
    """
    Return the integer id of a valid variable string.

    Examples:
        >>> var_id('h3')
        3
        >>> var_id('ref-ind12')
        12
    """
    return int(sort_vid_split(v)[1])


class _VarGenerator(object):
    """
    Simple class to produce variables, incrementing the vid for each
    one.
    """

    def __init__(self, starting_vid=1):
        self.vid = starting_vid
        self.index = {}  # to map vid to created variable
        self.store = {}  # to recall properties from varstrings

    def new(self, sort, properties=None):
        """
        Create a new variable for the given *sort*.
        """
        if sort is None:
            sort = UNKNOWNSORT
        # find next available vid
        vid, index = self.vid, self.index
        while vid in index:
            vid += 1
        varstring = '{}{}'.format(sort, vid)
        index[vid] = varstring
        if properties is None:
            properties = []
        self.store[varstring] = properties
        self.vid = vid + 1
        return (varstring, properties)


class Lnk(namedtuple('Lnk', ('type', 'data'))):
    """
    Surface-alignment information for predications.

    Lnk objects link predicates to the surface form in one of several
    ways, the most common of which being the character span of the
    original string.

    Args:
        type: the way the Lnk relates the semantics to the surface form
        data: the Lnk specifiers, whose quality depends on *type*
    Attributes:
        type: the way the Lnk relates the semantics to the surface form
        data: the Lnk specifiers, whose quality depends on *type*
    Note:
        Valid *types* and their associated *data* shown in the table
        below.

        =========  ===================  =========
        type       data                 example
        =========  ===================  =========
        charspan   surface string span  (0, 5)
        chartspan  chart vertex span    (0, 5)
        tokens     token identifiers    (0, 1, 2)
        edge       edge identifier      1
        =========  ===================  =========


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

    def __init__(self, type, data):
        # class methods below use __new__ to instantiate data, so
        # don't do it here
        if type not in (Lnk.CHARSPAN, Lnk.CHARTSPAN, Lnk.TOKENS, Lnk.EDGE):
            raise XmrsError('Invalid Lnk type: {}'.format(type))

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
            return '<{}#{}>'.format(self.data[0], self.data[1])
        elif self.type == Lnk.EDGE:
            return '<@{}>'.format(self.data)
        elif self.type == Lnk.TOKENS:
            return '<{}>'.format(' '.join(map(str, self.data)))

    def __repr__(self):
        return '<Lnk object {} at {}>'.format(str(self), id(self))

    def __eq__(self, other):
        return self.type == other.type and self.data == other.data


class _LnkMixin(object):
    """
    A mixin class for adding `cfrom` and `cto` properties on structures.

    By far the most common :class:`Lnk` type is for character spans,
    and these spans are conveniently described by `cfrom` and `cto`
    properties. This mixin is used by larger structures, such as
    :class:`ElementaryPredication`, :class:`Node`, and
    :class:`~delphin.mrs.xmrs.Xmrs`, to add `cfrom` and `cto`
    properties. These properties exist regardless of the whether the
    Lnk is a character span or not; if not, or if Lnk information is
    missing, they return the default value of `-1`.
    """
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


# LINKS and CONSTRAINTS

class Link(namedtuple('Link', ('start', 'end', 'rargname', 'post'))):
    """
    DMRS-style dependency link.

    Links are a way of representing arguments without variables. A
    Link encodes a start and end node, the role name, and the scopal
    relationship between the start and end (e.g. label equality, qeq,
    etc).

    Args:
        start: nodeid of the start of the Link
        end: nodeid of the end of the Link
        rargname (str): role of the argument
        post (str): "post-slash label" indicating the scopal
            relationship between the start and end of the Link;
            possible values are `NEQ`, `EQ`, `HEQ`, and `H`
    Attributes:
        start: nodeid of the start of the Link
        end: nodeid of the end of the Link
        rargname (str): role of the argument
        post (str): "post-slash label" indicating the scopal
            relationship between the start and end of the Link
    """
    def __new__(cls, start, end, rargname, post):
        return super(Link, cls).__new__(
            cls, start, end, rargname, post
        )

    def __repr__(self):
        return '<Link object (#{} :{}/{}> #{}) at {}>'.format(
            self.start, self.rargname or '', self.post, self.end, id(self)
        )


def links(xmrs):
    """Return the list of Links for the *xmrs*."""

    # Links exist for every non-intrinsic argument that has a variable
    # that is the intrinsic variable of some other predicate, as well
    # as for label equalities when no argument link exists (even
    # considering transitivity).
    links = []
    prelinks = []

    _eps = xmrs._eps
    _hcons = xmrs._hcons
    _vars = xmrs._vars

    lsh = xmrs.labelset_heads
    lblheads = {v: lsh(v) for v, vd in _vars.items() if 'LBL' in vd['refs']}

    top = xmrs.top
    if top is not None:
        prelinks.append((0, top, None, top, _vars[top]))

    for nid, ep in _eps.items():
        for role, val in ep[3].items():
            if role == IVARG_ROLE or val not in _vars:
                continue
            prelinks.append((nid, ep[2], role, val, _vars[val]))

    for src, srclbl, role, val, vd in prelinks:
        if IVARG_ROLE in vd['refs']:
            tgtnids = [n for n in vd['refs'][IVARG_ROLE]
                       if not _eps[n].is_quantifier()]
            if len(tgtnids) == 0:
                continue  # maybe some bad MRS with a lonely quantifier
            tgt = tgtnids[0]  # what do we do if len > 1?
            tgtlbl = _eps[tgt][2]
            post = EQ_POST if srclbl == tgtlbl else NEQ_POST
        elif val in _hcons:
            lbl = _hcons[val][2]
            if lbl not in lblheads or len(lblheads[lbl]) == 0:
                continue  # broken MRS; log this?
            tgt = lblheads[lbl][0]  # sorted list; first item is most "heady"
            post = H_POST
        elif 'LBL' in vd['refs']:
            if val not in lblheads or len(lblheads[val]) == 0:
                continue  # broken MRS; log this?
            tgt = lblheads[val][0]  # again, should be sorted already
            post = HEQ_POST
        else:
            continue  # CARGs, maybe?
        links.append(Link(src, tgt, role, post))

    # now EQ links unattested by arg links
    for lbl, heads in lblheads.items():
        # I'm pretty sure this does what we want
        if len(heads) > 1:
            first = heads[0]
            for other in heads[1:]:
                links.append(Link(other, first, BARE_EQ_ROLE, EQ_POST))
        # If not, something like this is more explicit
        # lblset = self.labelset(lbl)
        # sg = g.subgraph(lblset)
        # ns = [nid for nid, deg in sg.degree(lblset).items() if deg == 0]
        # head = self.labelset_head(lbl)
        # for n in ns:
        #     links.append(Link(head, n, post=EQ_POST))
    def _int(x):
        try:
            return int(x)
        except ValueError:
            return 0
    return sorted(
        links,
        key=lambda link: (_int(link.start), _int(link.end), link.rargname)
    )


class HandleConstraint(
        namedtuple('HandleConstraint', ('hi', 'relation', 'lo'))):
    """
    A relation between two handles.

    Arguments:
        hi (str): hi handle (hole) of the constraint
        relation (str): relation of the constraint (nearly always
            `"qeq"`, but `"lheq"` and `"outscopes"` are also valid)
        lo (str): lo handle (label) of the constraint
    Attributes:
        hi (str): hi handle (hole) of the constraint
        relation (str): relation of the constraint
        lo (str): lo handle (label) of the constraint
    """

    QEQ = 'qeq'  # Equality modulo Quantifiers
    LHEQ = 'lheq'  # Label-Handle Equality
    OUTSCOPES = 'outscopes'  # Outscopes

    @classmethod
    def qeq(cls, hi, lo):
        return cls(hi, HandleConstraint.QEQ, lo)

    def __repr__(self):
        return '<HandleConstraint object ({} {} {}) at {}>'.format(
               str(self.hi), self.relation, str(self.lo), id(self)
        )


def hcons(xmrs):
    """Return the list of all HandleConstraints in *xmrs*."""
    return [
        HandleConstraint(hi, reln, lo)
        for hi, reln, lo in sorted(xmrs.hcons(), key=lambda hc: var_id(hc[0]))
    ]


class IndividualConstraint(
        namedtuple('IndividualConstraint', ['left', 'relation', 'right'])):
    """
    A relation between two variables.

    Arguments:
        left (str): left variable of the constraint
        relation (str): relation of the constraint
        right (str): right variable of the constraint
    Attributes:
        left (str): left variable of the constraint
        relation (str): relation of the constraint
        right (str): right variable of the constraint
    """

def icons(xmrs):
    """Return the list of all IndividualConstraints in *xmrs*."""
    return [
        IndividualConstraint(left, reln, right)
        for left, reln, right in sorted(xmrs.icons(),
                                        key=lambda ic: var_id(ic[0]))
    ]


# PREDICATES AND PREDICATIONS


class Pred(namedtuple('Pred', ('type', 'lemma', 'pos', 'sense', 'string'))):
    """
    A semantic predicate.

    **Abstract** predicates don't begin with an underscore, and they
    generally are defined as types in a grammar. **Surface** predicates
    always begin with an underscore (ignoring possible quotes), and are
    often defined as strings in a lexicon.

    In PyDelphin, Preds are equivalent if they have the same lemma,
    pos, and sense, and are both abstract or both surface preds. Other
    factors are ignored for comparison, such as their being surface-,
    abstract-, or real-preds, whether they are quoted or not, whether
    they end with `_rel` or not, or differences in capitalization.
    Hashed Pred objects (e.g., in a dict or set) also use the
    normalized form. However, unlike with equality comparisons,
    Pred-formatted strings are not treated as equivalent in a hash.

    Args:
        type: the type of predicate; valid values are
            Pred.ABSTRACT, Pred.REALPRED, and Pred.SURFACE,
            although in practice Preds are instantiated via
            classmethods that select the type
        lemma: the lemma of the predicate
        pos: the part-of-speech; a single, lowercase character
        sense: the (often omitted) sense of the predicate
    Returns:
        a Pred object
    Attributes:
        type: predicate type (Pred.ABSTRACT, Pred.REALPRED, 
            and Pred.SURFACE)
        lemma: lemma component of the predicate
        pos: part-of-speech component of the predicate
        sense: sense component of the predicate
    Example:
        Preds are compared using their string representations.
        Surrounding quotes (double or single) are ignored, and
        capitalization doesn't matter. In addition, preds may be
        compared directly to their string representations:

        >>> p1 = Pred.surface('_dog_n_1_rel')
        >>> p2 = Pred.realpred(lemma='dog', pos='n', sense='1')
        >>> p3 = Pred.abstract('dog_n_1_rel')
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
        r'(?P<end>rel)$',
        re.IGNORECASE
    )
    # Pred types (used mainly in input/output, not internally in pyDelphin)
    ABSTRACT = GRAMMARPRED = 0  # only a string allowed (quoted or not)
    REALPRED = 1  # may explicitly define lemma, pos, sense
    SURFACE = STRINGPRED = 2  # quoted string form of realpred

    def __eq__(self, other):
        if other is None:
            return False
        if not isinstance(other, Pred):
            other = Pred.surface(other)
        return self.short_form().lower() == other.short_form().lower()

    def __str__ (self):
        return self.string

    def __repr__(self):
        return '<Pred object {} at {}>'.format(self.string, id(self))

    def __hash__(self):
        return hash(self.short_form())

    @classmethod
    @deprecated(final_version='1.0.0', alternative='Pred.surface()')
    def stringpred(cls, predstr): 
        """Instantiate a Pred from its quoted string representation."""
        return cls.surface(predstr)

    @classmethod
    def surface(cls, predstr):
        """Instantiate a Pred from its quoted string representation."""
        lemma, pos, sense, _ = split_pred_string(predstr)
        return cls(Pred.SURFACE, lemma, pos, sense, predstr)

    @classmethod
    @deprecated(final_version='1.0.0', alternative='Pred.abstract()')
    def grammarpred(cls, predstr):
        """Instantiate a Pred from its symbol string."""
        return cls.abstract(predstr)

    @classmethod
    def abstract(cls, predstr):
        """Instantiate a Pred from its symbol string."""
        lemma, pos, sense, _ = split_pred_string(predstr)
        return cls(Pred.ABSTRACT, lemma, pos, sense, predstr)

    @classmethod
    @deprecated(final_version='1.0.0', alternative='Pred.surface_or_abstract()')
    def string_or_grammar_pred(cls, predstr):
        """Instantiate a Pred from either its surface or abstract symbol."""
        return cls.surface_or_abstract(predstr)

    @classmethod
    def surface_or_abstract(cls, predstr):
        """Instantiate a Pred from either its surface or abstract symbol."""
        if predstr.strip('"').lstrip("'").startswith('_'):
            return cls.surface(predstr)
        else:
            return cls.abstract(predstr)

    @classmethod
    def realpred(cls, lemma, pos, sense=None):
        """Instantiate a Pred from its components."""
        string_tokens = [lemma]
        if pos is not None:
            string_tokens.append(pos)
        if sense is not None:
            sense = str(sense)
            string_tokens.append(sense)
        predstr = '_'.join([''] + string_tokens + ['rel'])
        return cls(Pred.REALPRED, lemma, pos, sense, predstr)

    def short_form(self):
        """
        Return the pred string without quotes or a `_rel` suffix.

        The short form is the same as the normalized form from
        :func:`normalize_pred_string`.

        Example:

            >>> p = Pred.surface('"_cat_n_1_rel"')
            >>> p.short_form()
            '_cat_n_1'
        """
        return normalize_pred_string(self.string)

    def is_quantifier(self):
        """
        Return `True` if the predicate has a quantifier part-of-speech.

        *Deprecated since v0.6.0*
        """
        warnings.warn(
            'Deprecated; try checking xmrs.nodeids(quantifier=True)',
            DeprecationWarning
        )
        return self.pos == QUANTIFIER_POS


def split_pred_string(predstr):
    """
    Split *predstr* and return the (lemma, pos, sense, suffix) components.

    Examples:
        >>> Pred.split_pred_string('_dog_n_1_rel')
        ('dog', 'n', '1', 'rel')
        >>> Pred.split_pred_string('quant_rel')
        ('quant', None, None, 'rel')
    """
    predstr = predstr.strip('"\'')  # surrounding quotes don't matter
    rel_added = False
    if not predstr.lower().endswith('_rel'):
        logging.debug('Predicate does not end in "_rel": {}'
                      .format(predstr))
        rel_added = True
        predstr += '_rel'
    match = Pred.pred_re.search(predstr)
    if match is None:
        logging.debug('Unexpected predicate string: {}'.format(predstr))
        return (predstr, None, None, None)
    # _lemma_pos(_sense)?_end
    return (match.group('lemma'), match.group('pos'),
            match.group('sense'), None if rel_added else match.group('end'))


def is_valid_pred_string(predstr):
    """
    Return `True` if *predstr* is a valid predicate string.

    Examples:
        >>> is_valid_pred_string('"_dog_n_1_rel"')
        True
        >>> is_valid_pred_string('_dog_n_1')
        True
        >>> is_valid_pred_string('_dog_noun_1')
        False
        >>> is_valid_pred_string('dog_noun_1')
        True
    """
    predstr = predstr.strip('"').lstrip("'")
    # this is a stricter regex than in Pred, but doesn't check POS
    return re.match(
        r'_([^ _\\]|\\.)+_[a-z](_([^ _\\]|\\.)+)?(_rel)?$'
        r'|[^_]([^ \\]|\\.)+(_rel)?$',
        predstr
    ) is not None


def normalize_pred_string(predstr):
    """
    Normalize the predicate string *predstr* to a conventional form.

    This makes predicate strings more consistent by removing quotes and
    the `_rel` suffix, and by lowercasing them.

    Examples:
        >>> normalize_pred_string('"_dog_n_1_rel"')
        '_dog_n_1'
        >>> normalize_pred_string('_dog_n_1')
        '_dog_n_1'
    """
    tokens = [t for t in split_pred_string(predstr)[:3] if t is not None]
    if predstr.lstrip('\'"')[:1] == '_':
        tokens = [''] + tokens
    return '_'.join(tokens).lower()


class Node(
    namedtuple('Node', ('nodeid', 'pred', 'sortinfo',
                        'lnk', 'surface', 'base', 'carg')),
    _LnkMixin):
    """
    A DMRS node.

    Nodes are very simple predications for DMRSs. Nodes don't have
    arguments or labels like :class:`ElementaryPredication` objects,
    but they do have a property for CARGs and contain their variable
    sort and properties in `sortinfo`.

    Args:
        nodeid: node identifier
        pred (:class:`Pred`): semantic predicate
        sortinfo (dict, optional): mapping of morphosyntactic
            properties and values; the `cvarsort` property is
            specified in this mapping
        lnk (:class:`Lnk`, optional): surface alignment
        surface (str, optional): surface string
        base (str, optional): base form
        carg (str, optional): constant argument string
    Attributes:
        Attributes:
        pred (:class:`Pred`): semantic predicate
        sortinfo (dict): mapping of morphosyntactic
            properties and values; the `cvarsort` property is
            specified in this mapping
        lnk (:class:`Lnk`): surface alignment
        surface (str): surface string
        base (str): base form
        carg (str): constant argument string
        cfrom (int): surface alignment starting position
        cto (int): surface alignment ending position
    """

    def __new__(cls, nodeid, pred, sortinfo=None,
                 lnk=None, surface=None, base=None, carg=None):
        if sortinfo is None:
            sortinfo = {}
        elif not isinstance(sortinfo, MutableMapping):
            sortinfo = dict(sortinfo)
        return super(Node, cls).__new__(
            cls, nodeid, pred, sortinfo, lnk, surface, base, carg
        )

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
        warnings.warn("Deprecated", DeprecationWarning)
        x1 = (self.cfrom, self.cto, self.pred.pos != QUANTIFIER_POS,
              self.pred.lemma)
        try:
            x2 = (other.cfrom, other.cto, other.pred.pos != QUANTIFIER_POS,
                  other.pred.lemma)
            return x1 < x2
        except AttributeError:
            return NotImplemented

    @property
    def cvarsort(self):
        """
        The "variable" type of the predicate.

        Note:
          DMRS does not use variables, but it is useful to indicate
          whether a node is an individual, eventuality, etc., so this
          property encodes that information.
        """
        return self.sortinfo.get(CVARSORT)

    @cvarsort.setter
    def cvarsort(self, value):
        self.sortinfo[CVARSORT] = value

    @property
    def properties(self):
        """
        Morphosemantic property mapping.

        Unlike :attr:`sortinfo`, this does not include `cvarsort`.
        """
        d = dict(self.sortinfo)
        if CVARSORT in d:
            del d[CVARSORT]
        return d

    def is_quantifier(self):
        """
        Return `True` if the Node's predicate appears to be a quantifier.

        *Deprecated since v0.6.0*
        """
        warnings.warn(
            'Deprecated; try checking xmrs.nodeids(quantifier=True)',
            DeprecationWarning
        )
        return self.pred.is_quantifier()


def nodes(xmrs):
    """Return the list of Nodes for *xmrs*."""
    nodes = []
    _props = xmrs.properties
    varsplit = sort_vid_split
    for p in xmrs.eps():
        sortinfo = None
        iv = p.intrinsic_variable
        if iv is not None:
            sort, _ = varsplit(iv)
            sortinfo = _props(iv)
            sortinfo[CVARSORT] = sort
        nodes.append(
            Node(p.nodeid, p.pred, sortinfo, p.lnk, p.surface, p.base, p.carg)
        )
    return nodes


class ElementaryPredication(
    namedtuple('ElementaryPredication',
               ('nodeid', 'pred', 'label', 'args', 'lnk', 'surface', 'base')),
    _LnkMixin):
    """
    An MRS elementary predication (EP).

    EPs combine a predicate with various structural semantic
    properties. They must have a `nodeid`, `pred`, and `label`.
    Arguments and other properties are optional. Note nodeids are not a
    formal property of MRS (unlike DMRS, or the "anchors" of RMRS), but
    they are required for Pydelphin to uniquely identify EPs in an
    :class:`~delphin.mrs.xmrs.Xmrs`. Intrinsic arguments (`ARG0`) are
    not required, but they are important for many semantic operations,
    and therefore it is a good idea to include them.

    Args:
        nodeid: a nodeid
        pred (:class:`Pred`): semantic predicate
        label (str): scope handle
        args (dict, optional): mapping of roles to values
        lnk (:class:`Lnk`, optional): surface alignment
        surface (str, optional): surface string
        base (str, optional): base form
    Attributes:
        nodeid: a nodeid
        pred (:class:`Pred`): semantic predicate
        label (str): scope handle
        args (dict): mapping of roles to values
        lnk (:class:`Lnk`): surface alignment
        surface (str): surface string
        base (str): base form
        cfrom (int): surface alignment starting position
        cto (int): surface alignment ending position
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

    def __repr__(self):
        return '<ElementaryPredication object ({} ({})) at {}>'.format(
            self.pred.string, str(self.iv or '?'), id(self)
        )

    def __lt__(self, other):
        warnings.warn("Deprecated", DeprecationWarning)
        x1 = (self.cfrom, self.cto, -self.is_quantifier(), self.pred.lemma)
        try:
            x2 = (other.cfrom, other.cto, -other.is_quantifier(),
                  other.pred.lemma)
            return x1 < x2
        except AttributeError:
            return NotImplemented

    # these properties are specific to the EP's qualities

    @property
    def intrinsic_variable(self):
        """
        The value of the intrinsic argument (likely `ARG0`).
        """
        if IVARG_ROLE in self.args:
            return self.args[IVARG_ROLE]
        return None

    #: A synonym for :attr:`ElementaryPredication.intrinsic_variable`
    iv = intrinsic_variable

    @property
    def carg(self):
        """
        The value of the constant argument.
        """
        return self.args.get(CONSTARG_ROLE, None)

    def is_quantifier(self):
        """
        Return `True` if this is a quantifier predication.
        """
        return RSTR_ROLE in self.args


def elementarypredications(xmrs):
    """
    Return the list of :class:`ElementaryPredication` objects in *xmrs*.
    """
    return list(starmap(ElementaryPredication, xmrs.eps()))


def elementarypredication(xmrs, nodeid):
    """
    Retrieve the elementary predication with the given nodeid.

    Args:
        nodeid: nodeid of the EP to return
    Returns:
        :class:`ElementaryPredication`
    Raises:
        :py:exc:`KeyError` if no EP matches
    """
    return ElementaryPredication(*xmrs.ep(nodeid))
