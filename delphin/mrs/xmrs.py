
from collections import (OrderedDict, defaultdict)
from itertools import chain
import warnings
# consider using this:
# from functools import lru_cache

import networkx as nx
from networkx import DiGraph, relabel_nodes

from delphin._exceptions import (XmrsError, XmrsStructureError)
from . import components
from .components import (
    Hook, MrsVariable, ElementaryPredication, Node,
    HandleConstraint, Lnk, LnkMixin
)
from .config import (
    HANDLESORT, IVARG_ROLE, CONSTARG_ROLE, LTOP_NODEID, FIRST_NODEID,
    RSTR_ROLE, EQ_POST, NEQ_POST, HEQ_POST, H_POST, NIL_POST
)
from .util import first, second


def Mrs(top=None, index=None, xarg=None, rels=None, hcons=None, icons=None,
        lnk=None, surface=None, identifier=None):
    """
    Construct an |Xmrs| using MRS components.

    Formally, Minimal Recursion Semantics (MRS) have a top handle, a
    bag of |ElementaryPredications|, and a bag of |HandleConstraints|.
    All |Arguments|, including intrinsic arguments and constant
    arguments, are expected to be contained by the |EPs|.

    Args:
        hook: A |Hook| object to contain LTOP, INDEX, etc.
        rels: An iterable of |ElementaryPredications|
        hcons: An iterable of |HandleConstraints|
        icons: An iterable of IndividualConstraints (planned feature)
        lnk: The |Lnk| object associating the MRS to the surface form
        surface: The surface string
        identifier: A discourse-utterance id
    Returns:
        An |Xmrs| object

    Example:

    >>> ltop = MrsVariable(vid=0, sort='h')
    >>> rain_label = MrsVariable(vid=1, sort='h')
    >>> index = MrsVariable(vid=2, sort='e')
    >>> m = Mrs(
    >>>     hook=Hook(ltop=ltop, index=index),
    >>>     rels=[ElementaryPredication(
    >>>         Pred.stringpred('_rain_v_1_rel'),
    >>>         label=rain_label,
    >>>         args=[Argument.mrs_argument('ARG0', index)]
    >>>         )
    >>>     ],
    >>>     hcons=[HandleConstraint(ltop, 'qeq', rain_label)]
    >>> )
    """
    if hook is None:
        hook = Hook()
    eps = sorted(rels or [])  # sorted to try and make nodeids predictable
    hcons = list(hcons or [])
    icons = list(icons or [])
    # first give eps a nodeid (this is propagated to args)
    next_nodeid = FIRST_NODEID
    for ep in eps:
        if ep.nodeid is not None and ep.nodeid >= next_nodeid:
            next_nodeid = ep.nodeid + 1
    for i, ep in enumerate(eps):
        if ep.nodeid is None:
            ep.nodeid = next_nodeid + i
    graph = build_graph(hook, eps, hcons, icons)
    return Xmrs(graph, hook, lnk, surface, identifier)


def Rmrs(hook=None, eps=None, args=None, hcons=None, icons=None,
         lnk=None, surface=None, identifier=None):
    """
    Construct an |Xmrs| from RMRS components.

    Robust Minimal Recursion Semantics (RMRS) are like MRS, but all
    |EPs| have a nodeid ("anchor"), and |Arguments| are not contained
    by the source |EPs|, but instead reference the nodeid of their |EP|.

    Args:
        hook: A |Hook| object
        eps: An iterable of |EP| objects
        args: An iterable of |Argument| objects
        hcons: An iterable of |HandleConstraint| objects
        icons: An iterable of |IndividualConstraint| objects
        lnk: A |Lnk| object
        surface: The surface string
        identifier: A discourse-utterance id
    Returns:
        An |Xmrs| object

    Example:

    >>> ltop = MrsVariable(vid=0, sort='h')
    >>> rain_label = MrsVariable(vid=1, sort='h')
    >>> index = MrsVariable(vid=2, sort='e')
    >>> m = Rmrs(
    >>>     hook=Hook(ltop=ltop, index=index),
    >>>     eps=[ElementaryPredication(
    >>>         Pred.stringpred('_rain_v_1_rel'),
    >>>         label=rain_label,
    >>>         nodeid=10000
    >>>         )
    >>>     ],
    >>>     args=[Argument.rmrs_argument(10000, 'ARG0', index)],
    >>>     hcons=[HandleConstraint(ltop, 'qeq', rain_label)]
    >>> )
    """
    if hook is None:
        hook = Hook()
    eps = list(eps or [])
    args = list(args or [])
    for arg in args:
        if arg.nodeid is None:
            raise XmrsStructureError("RMRS args must have a nodeid.")
    # make the EPs more MRS-like (with arguments)
    for ep in eps:
        if ep.nodeid is None:
            raise XmrsStructureError("RMRS EPs must have a nodeid.")
        argdict = OrderedDict((a.rargname, a) for a in args
                              if a.nodeid == ep.nodeid)
        ep.argdict = argdict
    hcons = list(hcons or [])
    icons = list(icons or [])
    graph = build_graph(hook, eps, hcons, icons)
    return Xmrs(graph, hook, lnk, surface, identifier)


def Dmrs(nodes=None, links=None,
         lnk=None, surface=None, identifier=None,
         **kwargs):
    """
    Construct an |Xmrs| using DMRS components.

    Dependency Minimal Recursion Semantics (DMRS) have a list of |Node|
    objects and a list of |Link| objects. There are no variables or
    handles, so these will need to be created in order to make an |Xmrs|
    object. A |Link| from the nodeid 0 (which does not have its own
    |Node|)

    Args:
        nodes: An iterable of |Node| objects
        links: An iterable of |Link| objects
        lnk: The |Lnk| object associating the MRS to the surface form
        surface: The surface string
        identifier: A discourse-utterance id
    Returns:
        An |Xmrs| object

    Example:

    >>> rain = Node(10000, Pred.stringpred('_rain_v_1_rel'),
    >>>             sortinfo={'cvarsort': 'e'})
    >>> ltop_link = Link(0, 10000, post='H')
    >>> d = Dmrs([rain], [ltop_link])
    """
    from .components import VarGenerator
    qeq = HandleConstraint.qeq
    vgen = VarGenerator(starting_vid=0)
    labels = _make_labels(nodes, links, vgen)
    ivs = _make_ivs(nodes, vgen)
    hook = Hook(ltop=labels[LTOP_NODEID])  # no index for now
    # initialize args with ARG0 for intrinsic variables
    args = {nid: [(nid, IVARG_ROLE, iv)] for nid, iv in ivs.items()}
    hcons = []
    for l in links:
        if l.start not in args:
            args[l.start] = []
        # FIXME: I don't have a clear answer about how LTOP links are
        # constructed, so I will assume that H_POST or NIL_POST
        # assumes a QEQ. Label equality would have been captured by
        # _make_labels() earlier.
        if l.start == LTOP_NODEID:
            if l.post == H_POST or l.post == NIL_POST:
                hcons += [qeq(labels[LTOP_NODEID], labels[l.end])]
        else:
            if not l.rargname or l.rargname.upper() == 'NIL':
                continue  # don't make an argument for bare EQ links
            if l.post == H_POST:
                hole = vgen.new(HANDLESORT)
                hcons += [qeq(hole, labels[l.end])]
                args[l.start].append((l.start, l.rargname, hole))
                # if the arg is RSTR, it's a quantifier, so we can
                # find its intrinsic variable now
                if l.rargname.upper() == RSTR_ROLE:
                    ivs[l.start] = ivs[l.end]
                    args[l.start].append(
                        (l.start, IVARG_ROLE, ivs[l.start])
                    )
            elif l.post == HEQ_POST:
                args[l.start].append(
                    (l.start, l.rargname, labels[l.end])
                )
            else:  # NEQ_POST or EQ_POST
                args[l.start].append(
                    (l.start, l.rargname, ivs[l.end])
                )
    eps = []
    for node in nodes:
        nid = node.nodeid
        if node.carg is not None:
            args[nid].append((nid, CONSTARG_ROLE, node.carg))
        ep = ElementaryPredication.from_node(
            labels[nid], node, (args.get(nid) or None)
        )
        eps.append(ep)

    icons = None  # future feature
    return Mrs(hook=hook, rels=eps,
               hcons=hcons, icons=icons,
               lnk=lnk, surface=surface, identifier=identifier)


def _make_labels(nodes, links, vgen):
    labels = {}
    labels[LTOP_NODEID] = vgen.new(HANDLESORT)  # reserve h0 for ltop
    for l in links:
        if l.post == EQ_POST:
            lbl = (labels.get(l.start) or
                   labels.get(l.end) or
                   vgen.new(HANDLESORT))
            labels[l.start] = labels[l.end] = lbl
    # create any remaining uninstantiated labels
    for n in nodes:
        if n.nodeid not in labels:
            labels[n.nodeid] = vgen.new(HANDLESORT)
    return labels


def _make_ivs(nodes, vgen):
    ivs = {}
    for node in nodes:
        # quantifiers share their IV with the quantifiee. It will be
        # selected later during argument construction
        if not node.is_quantifier():
            ivs[node.nodeid] = vgen.new(node.cvarsort,
                                        node.properties or None)
    return ivs


class Xmrs(LnkMixin):
    """
    Xmrs is a common class for Mrs, Rmrs, and Dmrs objects.
    """

    __slots__ = ('top', 'index', 'xarg', '_nodeids', '_eps', '_vars')
    # nodeids, preds, lnks, label, args, variables, surface, base,
    # hcons, icons, constants
# nodeid: (pred, label, args, lnk, surface, base)
    # vid: variable

    def __init__(self, top=None, index=None, xarg=None,
                 eps=None, hcons=None, icons=None, vars=None,
                 lnk=None, surface=None, identifier=None):
        """
        Xmrs can be instantiated directly, but it is meant to be created
        by the constructor methods :py:meth:`Mrs`, :py:meth:`Rmrs`, or
        :py:meth:`Dmrs`.

        Args:
            graph: a graph of the \*MRS structure
            hook: a |Hook| object to contain the ltop, xarg, and index
            lnk: the |Lnk| object associating the Xmrs to the surface form
            surface: the surface string
            identifier: a discourse-utterance id
        """
        self.top = top
        self.index = index
        self.xarg = xarg

        self._nodeids = []
        self._eps = {}
        self._vars = {var: {'props': props, 'refs': defaultdict(list)}
                      for var, props in vars.items()}
        if eps is not None:
            self.add_eps(eps)
        if hcons is not None:
            self.add_hcons(hcons)
        if icons is not None:
            self.add_icons(icons)

        # self._graph = graph or XmrsDiGraph()

        # Some members relate to the whole MRS
        #: The |Hook| object contains the LTOP, INDEX, and XARG
        #self.hook = hook or Hook()
        #: A |Lnk| object to associate the Xmrs to the surface form
        self.lnk = lnk  # Lnk object (MRS-level lnk spans the whole input)
        #: The surface string
        self.surface = surface  # The surface string
        #: A discourse-utterance id
        self.identifier = identifier  # Associates an utterance with the RMRS

    def add_eps(self, eps):
        # (nid, pred, label, args, lnk, surface, base)
        #CONST = Argument.CONSTANT_ARG  # assign locally to avoid global lookup
        _nodeids = self._nodeids
        _eps = self._eps
        _vars = self._vars
        for ep in eps:
            nodeid = ep[0]
            if nodeid in _eps:
                raise XmrsError(
                    'EP already exists in Xmrs: {} ({})'.format(nodeid, ep[1])
                )
            _nodeids.append(nodeid)
            _eps[nodeid] = ep
            lbl = ep[2]
            if lbl is not None:
                _vars[lbl]['refs']['LBL'].append(nodeid)
            for role, val in ep[3].items():
                if val in _vars:
                    vardict = _vars[val]
                    vardict['refs'][role].append(nodeid)
                    if role == IVARG_ROLE:
                        if ep[1].is_quantifier():
                            vardict['bv'] = nodeid
                        else:
                            vardict['iv'] = nodeid

    def add_hcons(self, hcons):
        # (hi, relation, lo)
        _vars = self._vars
        for hc in hcons:
            hi = hc[0]
            lo = hc[2]
            _vars[hi]['hcons'] = hc
            _vars[lo]['refs']['hcons'].append(hc)

    def add_icons(self, icons):
        _vars = self._vars
        for ic in icons:
            left = ic[0]
            right = ic[2]
            _vars[left]['icons'] = ic
            _vars[right]['refs']['icons'].append(ic)

    def __repr__(self):
        if self.surface is not None:
            stringform = '"{}"'.format(self.surface)
        else:
            stringform = ' '.join(ep.pred.lemma for ep in self.eps)
        return '<Xmrs object ({}) at {}>'.format(stringform, id(self))

    def __hash__(self):
        # isomorphic MRSs should hash to the same thing, but
        # calculating isomorphism is expensive. Approximate it.
        return hash(' '.join(
            sorted(
                '{}:{}'.format(ep.pred.short_form(), len(ep.argdict))
                for ep in self.eps
            )
        ))

    def __eq__(self, other):
        # actual equality is more than isomorphism, all variables and
        # things must have the same form, not just the same shape
        if not isinstance(other, Xmrs):
            return False
        if self.hook != other.hook:
            return False
        eps1 = self.eps
        eps2 = other.eps
        if len(eps1) != len(eps2):
            return False
        zipped_eps = zip(sorted(eps1), sorted(eps2))
        for ep1, ep2 in zipped_eps:
            if ep1 != ep2:
                return False
        return True

    # Interface layer to the internal representations (and part of the
    # public API)

    @property
    def ltop(self):
        return self.top

    @property
    def nodeids(self):
        return list(self._nodeids)

    def variables(self):
        return [MrsVariable(var, vdict['props'])
                for var, vdict in self._vars.items()]

    def introduced_variables(self):
        return [MrsVariable(var, vdict['props'])
                for var, vd in self._vars.items()
                if 'iv' in vd or 'LBL' in vd['refs'] or 'hcons' in vd]

    def intrinsic_variables(self):
        return [MrsVariable(var, vdict['props'])
                for var, vdict in self._vars.items()
                if 'iv' in vdict]

    #: A synonym for :py:attr:`~delphin.mrs.xmrs.Xmrs.intrinsic_variables`
    ivs = intrinsic_variables

    def bound_variables(self):
        return [MrsVariable(var, vdict['props'])
                for var, vdict in self._vars.items()
                if 'bv' in vdict]

    #: A synonym for :py:attr:`~delphin.mrs.xmrs.Xmrs.bound_variables`
    bvs = bound_variables

    def labels(self):
        return [MrsVariable(var, vdict['props'])
                for var, vdict in self._vars.items()
                if 'LBL' in vdict['refs']]

    # accessor functions
    def get_nodeid(self, iv, quantifier=False):
        """
        Retrieve the nodeid of an |EP| given an intrinsic variable.

        Args:
            iv: The intrinsic variable of the |EP|.
            quantifier: If True and `iv` is the bound variable of a
                quantifier, return the nodeid of the quantifier. False
                by default.
        Returns:
            An integer nodeid.
        """

        v = 'bv' if quantifier else 'iv'
        return self._vars[iv][v]

    def get_pred(self, nid): return self._eps[nid][1]
    def get_argdict(self, nid): return self._eps[nid][3]
    def get_iv(self, nid): return self._eps[nid][3].get(IVARG_ROLE, None)
    def get_varprops(self, var): return self._vars[var]['props']

    def labelset(self, label):
        """
        Return the set of nodeids for |EPs| that share a label.

        Args:
            label: The label that returned nodeids share.
        Returns:
            A set of nodeids, which may be an empty set.
        """
        return self._vars[label]['refs']['LBL']

    def in_labelset(self, nodeids, label=None):
        """
        Test if all nodeids share a label.

        Args:
            nodeids: An iterable of nodeids.
            label: If given, all nodeids must share this label.
        Returns:
            True if all nodeids share a label, otherwise False.
        """
        nodeids = set(nodeids)
        if label is None:
            label = self._eps[next(iter(nodeids))][2]
        return nodeids.issubset(self._vars[label]['refs']['LBL'])

    def labelset_heads(self, label):
        """
        Return the heads of the labelset selected by `label`.

        Args:
            label: The label from which to find head nodes/EPs.
            single: If False, find all possible heads, otherwise find
                the most "heady" one.
        Returns:
            A nodeid, if single is True, otherwise an iterable of
            nodeids.
        """
        _eps = self._eps
        _vars = self._vars
        nids = {nid: _eps[nid][3].get(IVARG_ROLE, None)
                for nid in _vars[label]['refs']['LBL']}
        if len(nids) <= 1:
            return list(nids.keys())

        ivs = {iv: nid for nid, iv in nids.items() if iv is not None}

        out = {n: len(list(filter(ivs.__contains__, _eps[n][3].values())))
               for n in nids}
        # out_deg is 1 for ARG0, but <= 1 because sometimes ARG0 is missing
        candidates = [n for n, out_deg in out.items() if out_deg <= 1]
        in_ = {}
        q = {}
        for n in candidates:
            iv = nids[n]
            if iv in _vars:
                in_[n] = sum(1 for slist in _vars[iv]['refs'].values()
                             for s in slist if s in nids)
            else:
                in_[n] = 0
            q[n] = 1 if _eps[n][1].is_quantifier() else 0

        return sorted(
            candidates,
            key=lambda n: (
                # prefer fewer outgoing args to eps in the labelset
                out[n],
                # prefer more incoming args from eps in the labelset
                -in_[n],
                # prefer quantifiers (if it has a labelset > 1, it's a
                # compound quantifier, like "nearly all")
                -q[n],
                # finally sort by the nodeid itself
                n
            )
        )

    def subgraph(self, nodeids):
        """
        Return an |Xmrs| object representing the subgraph containing
        only the specified nodeids. Necessary variables are also
        included. in order to connect any nodes that are connected in
        the original Xmrs.

        Args:
            nodeids: The nodeids of the nodes/EPs to include in the
                subgraph.
        Returns:
            An |Xmrs| object.
        """
        _eps = self._eps
        _vars = self._vars
        top = index = xarg = None
        eps = [_eps[nid] for nid in nodeids]
        lbls = set(ep[2] for ep in eps)
        hcons = []
        icons = []
        subvars = {}
        if self.top:
            top = self.top
            tophc = _vars[self.top].get('hcons', None)
            if self.top in lbls:
                subvars[self.top] = {}
            elif tophc is not None and tophc[2] in lbls:
                subvars[self.top] = {}
                hcons.append(_vars[self.top]['hcons'])
            else:
                top = None  # nevermind, set it back to None
        # do index after we know if it is an EPs intrinsic variable.
        # what about xarg? I'm not really sure.. just put it in
        if self.xarg:
            xarg = self.xarg
            subvars[self.xarg] = _vars[self.xarg]['props']
        subvars.update((lbl, {}) for lbl in lbls)
        subvars.update(
            (var, _vars[var]['props'])
            for ep in eps for var in ep[3].values()
            if var in _vars
        )
        if self.index in subvars:
            index = self.index
        # hcons and icons; only if the targets exist in the new subgraph
        for var in subvars:
            hc = _vars[var].get('hcons', None)
            if hc is not None and hc[2] in lbls:
                hcons.append(hc)
            ic = _vars[var].get('icons', None)
            if ic is not None and ic[0] in subvars and ic[2] in subvars:
                icons.append(ic)
        return Xmrs(
            top=top, index=index, xarg=xarg,
            eps=eps, hcons=hcons, icons=icons, vars=subvars,
            lnk=self.lnk, surface=self.surface, identifier=self.identifier
        )

    def is_connected(self):
        """
        Return True if the Xmrs represents a connected graph.
        Subgraphs can be connected through things like arguments,
        QEQs, and label equalities.
        """
        domain = set(self._nodeids)  # the nids to consider when traversing
        if not domain:
            raise XmrsError('Cannot compute connectedness of an empty Xmrs.')
        _eps = self._eps
        _vars = self._vars
        nids = set(self._nodeids)  # the nids left to find
        unseen = set(_vars.keys())  # untraversed vars
        agenda = [next(iter(nids))]
        nids.remove(agenda[0])  # skip some work by removing this early

        while nids and agenda:
            curnid = agenda.pop()
            ep = _eps[curnid]
            lbl = ep[2]
            conns = set()

            if lbl in unseen:
                unseen.remove(lbl)
                for role, ref in _vars[lbl]['refs'].items():
                    if role == 'hcons':
                        hi = ref[0]
                        if hi in unseen:
                            unseen.remove(hi)
                            refs = _vars[hi]['refs'].values()
                            conns.union(chain.from_iterable(refs))
                    elif role != 'icons':
                        conns.union(ref)

            for role, var in ep[3].items():
                if var in unseen:
                    unseen.remove(var)
                    vd = _vars[var]
                    if 'iv' in vd:
                        conns.add(vd['iv'])
                    if 'bv' in vd:
                        conns.add(vd['bv'])
                    if 'hcons' in vd:
                        lo = vd['hcons'][2]
                        if lo in unseen:
                            unseen.remove(lo)
                            conns.union(_vars[lo]['refs']['LBL'])
                    if role == IVARG_ROLE:
                        conns.union(chain.from_iterable(vd['refs'].values()))

            agenda.extend(list(nids & conns))
            nids.difference_update(conns)

        return len(unseen) == 0

    def is_well_formed(self):
        """
        Return True if the Xmrs is well-formed, False otherwise.

        A well-formed Xmrs has the following properties (note, `node`
        below refers to a node in the graph, but is more like an EP than
        a DMRS Node):
          * The graph of nodes form a net (i.e. are connected).
            Connectivity can be established with variable arguments,
            QEQs, or label-equality.
          * All nodes have a label
          * The lo-handle for each QEQ must exist as the label of a node
          * All nominal nodes have a quantifier
        """
        _eps = self._eps
        _vars = self._vars
        nodeids = self._nodeids
        hcons = [_vars[argval]['hcons']
                 for nid in nodeids
                 for argval in _eps[nid][3].values()
                 if 'hcons' in _vars.get(argval, {})]
        return (
            self.is_connected() and
            all(_eps[nid][2] in _vars for nid in nodeids) and
            all(lo in _vars and len(_vars[lo]['refs'].get('LBL', [])) > 0
                for _, _, lo in hcons)
        )
