
"""
Classes and functions for working with the components of \*MRS objects.
"""

import re
import logging
import warnings
from collections import namedtuple, MutableMapping
from itertools import starmap

from delphin.exceptions import (XmrsError)
from delphin import predicate
from delphin.lnk import Lnk, _LnkMixin
from delphin import variable
from .config import (
    IVARG_ROLE, CONSTARG_ROLE, RSTR_ROLE,
    CVARSORT, QUANTIFIER_POS,
    EQ_POST, HEQ_POST, NEQ_POST, H_POST,
    BARE_EQ_ROLE
)

# The classes below are generally just namedtuples with extra methods.
# The namedtuples sometimes have default values. thanks:
#   http://stackoverflow.com/a/16721002/1441112

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
        for hi, reln, lo
        in sorted(xmrs.hcons(), key=lambda hc: variable.id(hc[0]))
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
                                        key=lambda ic: variable.id(ic[0]))
    ]


# PREDICATES AND PREDICATIONS

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
        pred (str): semantic predicate
        sortinfo (dict, optional): mapping of morphosyntactic
            properties and values; the `cvarsort` property is
            specified in this mapping
        lnk (:class:`Lnk`, optional): surface alignment
        surface (str, optional): surface string
        base (str, optional): base form
        carg (str, optional): constant argument string
    Attributes:
        Attributes:
        pred (str): semantic predicate
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

    def __eq__(self, other):
        if not isinstance(other, Node):
            return NotImplemented
        return (
            predicate.normalize(self.pred) == predicate.normalize(other.pred)
            and dict(self.sortinfo.items()) == other.sortinfo
            and self.carg == other.carg
        )

    def __ne__(self, other):
        if not isinstance(other, Node):
            return NotImplemented
        return not (self == other)

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


def nodes(xmrs):
    """Return the list of Nodes for *xmrs*."""
    nodes = []
    _props = xmrs.properties
    varsplit = variable.split
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
        pred (str): semantic predicate
        label (str): scope handle
        args (dict, optional): mapping of roles to values
        lnk (:class:`Lnk`, optional): surface alignment
        surface (str, optional): surface string
        base (str, optional): base form
    Attributes:
        nodeid: a nodeid
        pred (str): semantic predicate
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
        return super(ElementaryPredication, cls).__new__(
            cls, nodeid, pred, label, args, lnk, surface, base
        )

    def __repr__(self):
        return '<ElementaryPredication object ({} ({})) at {}>'.format(
            self.pred, str(self.iv or '?'), id(self)
        )

    def __eq__(self, other):
        if not isinstance(other, ElementaryPredication):
            return NotImplemented
        return (
            predicate.normalize(self.pred) == predicate.normalize(other.pred)
            and self.label == other.label
            and self.args == other.args
        )

    def __ne__(self, other):
        if not isinstance(other, ElementaryPredication):
            return NotImplemented
        return not (self == other)

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
        :exc:`KeyError`: if no EP matches
    """
    return ElementaryPredication(*xmrs.ep(nodeid))
