
"""
`delphin.mrs.xmrs` - Classes and functions for general *MRS

### known limitations (hopefully only good limitations):
  * Xmrs assumes each hole appears as an argument exactly once and as
    the hi variable of exactly one handle constraint
"""

from collections import (OrderedDict, defaultdict)
from itertools import chain

from delphin._exceptions import (XmrsError, XmrsStructureError)
from .components import (
    ElementaryPredication, HandleConstraint, LnkMixin, var_re
)
from .config import (
    HANDLESORT, IVARG_ROLE, CONSTARG_ROLE, LTOP_NODEID, FIRST_NODEID,
    RSTR_ROLE, EQ_POST, HEQ_POST, H_POST, NIL_POST, CVARSORT
)


class Xmrs(LnkMixin):
    """
    Xmrs is a common class for Mrs, Rmrs, and Dmrs objects.
    """

    def __init__(self, top=None, index=None, xarg=None,
                 eps=None, hcons=None, icons=None, vars=None,
                 lnk=None, surface=None, identifier=None):
        """
        Xmrs can be instantiated directly, but it may be more
        convenient to use the `Mrs()`, `Rmrs()`, or `Dmrs()`
        constructor functions.

        Variables are simply strings, but must be of the proper form
        in order to be recognized as variables and not constants. The
        form is basically a sequence of non-integers followed by a
        sequence of integers, but see `delphin.mrs.components.var_re`
        for the regular expression used to determine a match.

        The *eps* argument is an iterable of tuples representing
        ElementaryPredications. These can be objects of the
        ElementaryPredication class itself, or an equivalent tuple.
        The same goes for *hcons* and *icons* with the
        HandleConstraint and IndividualConstraint classes,
        respectively.

        Args:
            top: the TOP (or maybe LTOP) variable
            index: the INDEX variable
            xarg: the XARG variable
            eps: an iterable of EPs (see above)
            hcons: an iterable of HCONS (see above)
            icons: an iterable of ICONS (see above)
            vars: a mapping of variable to a list of property-value pairs
            lnk: the Lnk object associating the Xmrs to the surface form
            surface: the surface string
            identifier: a discourse-utterance id

        """
        self.top = top
        self.index = index
        self.xarg = xarg
        self._nodeids = []
        self._eps = {}
        self._hcons = {}
        self._icons = {}
        self._vars = defaultdict(
            lambda: {'props': [], 'refs': defaultdict(list)}
        )

        # just calling __getitem__ will instantiate them on _vars
        if top is not None: self._vars[top]
        if index is not None: self._vars[index]
        if xarg is not None: self._vars[xarg]

        if vars is not None:
            _vars = self._vars
            for var, props in vars.items():
                if hasattr(props, 'items'):
                    props = list(props.items())
                _vars[var]['props'] = props
        if eps is not None:
            self.add_eps(eps)
        if hcons is not None:
            self.add_hcons(hcons)
        if icons is not None:
            self.add_icons(icons)

        #: A |Lnk| object to associate the Xmrs to the surface form
        self.lnk = lnk  # Lnk object (MRS-level lnk spans the whole input)
        #: The surface string
        self.surface = surface  # The surface string
        #: A discourse-utterance id
        self.identifier = identifier  # Associates an utterance with the RMRS

    def add_eps(self, eps):
        # (nodeid, pred, label, args, lnk, surface, base)
        _nodeids, _eps, _vars = self._nodeids, self._eps, self._vars
        for ep in eps:
            try:
                if not isinstance(ep, ElementaryPredication):
                    ep = ElementaryPredication(*ep)
            except TypeError:
                raise XmrsError('Invalid EP data: {}'.format(repr(ep)))
            # eplen = len(ep)
            # if eplen < 3:
            #     raise XmrsError(
            #         'EPs must have length >= 3: (nodeid, pred, label, ...)'
            #     )
            nodeid, pred, lbl = ep.nodeid, ep.pred, ep.label
            if nodeid in _eps:
                raise XmrsError(
                    'EP already exists in Xmrs: {} ({})'
                    .format(nodeid, ep[1])
                )
            _nodeids.append(nodeid)
            _eps[nodeid] = ep
            if lbl is not None:
                _vars[lbl]['refs']['LBL'].append(nodeid)
            for role, val in ep.args.items():
                # if the val is not in _vars, it might still be a
                # variable; check with var_re
                if val in _vars or var_re.match(val):
                    vardict = _vars[val]
                    vardict['refs'][role].append(nodeid)
                    # if role == IVARG_ROLE:
                    #     if pred.is_quantifier():
                    #         vardict['bv'] = nodeid
                    #     else:
                    #         vardict['iv'] = nodeid

    def add_hcons(self, hcons):
        # (hi, relation, lo)
        _vars = self._vars
        _hcons = self._hcons
        for hc in hcons:
            if len(hc) < 3:
                raise XmrsError(
                    'Handle constraints must have length >= 3: '
                    '(hi, relation, lo)'
                )
            hi = hc[0]
            lo = hc[2]
            if hi in _hcons:
                raise XmrsError(
                    'Handle constraint already exists for hole %s.' % hi
                )
            _hcons[hi] = hc
            # the following should also ensure lo and hi are in _vars
            if 'hcrefs' not in _vars[lo]:
                _vars[lo]['hcrefs'] = []
            for role, refs in _vars[hi]['refs'].items():
                for nodeid in refs:
                    _vars[lo]['hcrefs'].append((nodeid, role, hi))

    def add_icons(self, icons):
        _vars, _icons = self._vars, self._icons
        for ic in icons:
            if len(ic) < 3:
                raise XmrsError(
                    'Individual constraints must have length >= 3: '
                    '(left, relation, right)'
                )
            left = ic[0]
            right = ic[2]
            if left not in _icons:
                _icons[left] = []
            _icons[left].append(ic)
            # the following should also ensure left and right are in _vars
            if 'icrefs' not in _vars[right]:
                _vars[right]['icrefs'] = []
            _vars[right]['icrefs'].append(ic)
            _vars[left]  # just to instantiate if not done yet

    def __repr__(self):
        if self.surface is not None:
            stringform = '"{}"'.format(self.surface)
        else:
            stringform = ' '.join(ep[1].lemma for ep in self.eps())
        return '<Xmrs object ({}) at {}>'.format(stringform, id(self))

    def __contains__(self, obj):
        return obj in self._eps or obj in self._vars

    def __eq__(self, other):
        # actual equality is more than isomorphism, all variables and
        # things must have the same form, not just the same shape
        if not isinstance(other, Xmrs):
            return NotImplemented
        if ((self.top, self.index, self.xarg) !=
                (other.top, other.index, other.xarg)):
            return False
        a, b = sorted(self.eps()), sorted(other.eps())
        if len(a) != len(b) or any(ep1 != ep2 for ep1, ep2 in zip(a, b)):
            return False
        a, b = sorted(self.hcons()), sorted(other.hcons())
        if len(a) != len(b) or any(hc1 != hc2 for hc1, hc2 in zip(a, b)):
            return False
        a, b = sorted(self.icons()), sorted(other.icons())
        if len(a) != len(b) or any(ic1 != ic2 for ic1, ic2 in zip(a, b)):
            return False
        return True

    @property
    def ltop(self):
        return self.top

    # basic access to internal structures

    def ep(self, nodeid): return self._eps[nodeid]

    def eps(self, nodeids=None):
        if nodeids is None: nodeids = self._nodeids
        _eps = self._eps
        return [_eps[nodeid] for nodeid in nodeids]

    def hcon(self, hi): return self._hcons[hi]

    def hcons(self): return list(self._hcons.values())

    def icons(self, left=None):
        if left is not None:
            return self._icons[left]
        else:
            return list(chain.from_iterable(self._icons.values()))

    def variables(self): return list(self._vars)

    # access to internal sub-structures

    def properties(self, var_or_nodeid):
        if var_or_nodeid in self._vars:
            return dict(self._vars[var_or_nodeid]['props'])
        elif var_or_nodeid in self._eps:
            var = self._eps[var_or_nodeid][3].get(IVARG_ROLE)
            return dict(self._vars.get(var, {}).get('props', []))
        else:
            raise KeyError(var_or_nodeid)

    def pred(self, nodeid): return self._eps[nodeid][1]

    def preds(self, nodeids=None):
        if nodeids is None: nodeids = self._nodeids
        _eps = self._eps
        return [_eps[nid][1] for nid in nodeids]

    def label(self, nodeid): return self._eps[nodeid][2]

    def labels(self, nodeids=None):
        if nodeids is None: nodeids = self._nodeids
        _eps = self._eps
        return [_eps[nid][2] for nid in nodeids]

    def args(self, nodeid): return dict(self._eps[nodeid][3])

    # calculated sub-structures

    def outgoing_args(self, nodeid):
        _vars = self._vars
        _hcons = self._hcons
        args = self.args(nodeid)  # args is a copy; we can edit it
        for arg, val in list(args.items()):
            # don't include constant args or intrinsic args
            if arg == IVARG_ROLE or val not in _vars:
                del args[arg]
            refs = _vars[val]['refs']
            # don't include if not HCONS or pointing to other IV or LBL
            if not (val in _hcons or IVARG_ROLE in refs or 'LBL' in refs):
                del args[arg]
        return args

    def incoming_args(self, nodeid):
        _vars = self._vars
        ep = self._eps[nodeid]
        lbl = ep[2]
        iv = ep[3].get(IVARG_ROLE)
        in_args_list = []
        # variable args
        if iv in _vars:
            for role, nids in _vars[iv]['refs'].items():
                # ignore intrinsic args, even if shared
                if role != IVARG_ROLE:
                    in_args_list.append((nids, role, iv))
        if lbl in _vars:
            for role, nids in _vars[lbl]['refs'].items():
                # basic label equality isn't "incoming"; ignore
                if role != 'LBL':
                    in_args_list.append((nids, role, lbl))
            for nid, role, hi in _vars[lbl].get('hcrefs', []):
                in_args_list.append(([nid], role, hi))
        in_args = {}
        for nids, role, tgt in in_args_list:
            for nid in nids:
                if nid not in in_args:
                    in_args[nid] = {}
                in_args[nid][role] = tgt
        return in_args

    def labelset(self, label):
        """
        Return the set of nodeids for |EPs| that share a label.

        Args:
            label: The label that returned nodeids share.
        Returns:
            A set of nodeids, which may be an empty set.
        """
        return self._vars[label]['refs']['LBL']

    def labelset_heads(self, label):
        """
        Return the heads of the labelset selected by `label`.

        Args:
            label: The label from which to find head nodes/EPs.
        Returns:
            An iterable of nodeids.
        """
        _eps = self._eps
        _vars = self._vars
        nodeids = {nodeid: _eps[nodeid][3].get(IVARG_ROLE, None)
                for nodeid in _vars[label]['refs']['LBL']}
        if len(nodeids) <= 1:
            return list(nodeids)

        ivs = {iv: nodeid for nodeid, iv in nodeids.items() if iv is not None}

        out = {n: len(list(filter(ivs.__contains__, _eps[n][3].values())))
               for n in nodeids}
        # out_deg is 1 for ARG0, but <= 1 because sometimes ARG0 is missing
        candidates = [n for n, out_deg in out.items() if out_deg <= 1]
        in_ = {}
        q = {}
        for n in candidates:
            iv = nodeids[n]
            if iv in _vars:
                in_[n] = sum(1 for slist in _vars[iv]['refs'].values()
                             for s in slist if s in nodeids)
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
        _eps, _vars = self._eps, self._vars
        _hcons, _icons = self._hcons, self._icons
        top = index = xarg = None
        eps = [_eps[nid] for nid in nodeids]
        lbls = set(ep[2] for ep in eps)
        hcons = []
        icons = []
        subvars = {}
        if self.top:
            top = self.top
            tophc = _hcons.get(top, None)
            if tophc is not None and tophc[2] in lbls:
                subvars[top] = {}
            elif top not in lbls:
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
            hc = _hcons.get(var, None)
            if hc is not None and hc[2] in lbls:
                hcons.append(hc)
            for ic in _icons.get(var, []):
                if ic[0] in subvars and ic[2] in subvars:
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
        nids = set(self._nodeids)  # the nids left to find
        nidlen = len(nids)
        if nidlen == 0:
            raise XmrsError('Cannot compute connectedness of an empty Xmrs.')
        _eps, _hcons, _vars = self._eps, self._hcons, self._vars
        explored = set()
        seen = set()
        agenda = [next(iter(nids))]

        while agenda:
            curnid = agenda.pop()
            ep = _eps[curnid]
            lbl = ep[2]
            conns = set()

            # labels can be shared, targets of HCONS, or targets of args
            if lbl in _vars:  # every EP should have a LBL
                for refrole, ref in _vars[lbl]['refs'].items():
                    if refrole == 'hcons':
                        for hc in ref:
                            if hc[0] in _vars:
                                refnids = _vars[hc[0]]['refs'].values()
                                conns.update(chain.from_iterable(refnids))
                    elif refrole != 'icons':
                        conns.update(ref)

            for role, var in ep[3].items():
                if var not in _vars:
                    continue
                vd = _vars[var]
                if IVARG_ROLE in vd['refs']:
                    conns.update(chain.from_iterable(vd['refs'].values()))
                # if 'iv' in vd:
                #     conns.add(vd['iv'])
                # if 'bv' in vd:
                #     conns.add(vd['bv'])
                if var in _hcons:
                    lo = _hcons[var][2]
                    if lo in _vars:
                        conns.update(_vars[lo]['refs']['LBL'])
                if 'LBL' in vd['refs']:
                    conns.update(vd['refs']['LBL'])

            explored.add(curnid)
            for conn in conns:
                if conn not in explored:
                    agenda.append(conn)
            seen.update(conns)
            # len(seen) is a quicker check
            if len(seen) == nidlen and len(nids.difference(seen)) == 0:
                break

        return len(nids.difference(seen)) == 0

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


def Mrs(top=None, index=None, xarg=None, rels=None, hcons=None, icons=None,
        lnk=None, surface=None, identifier=None, vars=None):
    """
    Construct an |Xmrs| using MRS components.

    Formally, Minimal Recursion Semantics (MRS) have a top handle, a
    bag of |ElementaryPredications|, and a bag of |HandleConstraints|.
    All |Arguments|, including intrinsic arguments and constant
    arguments, are expected to be contained by the |EPs|.

    Args:
        top: the TOP (or maybe LTOP) variable
        index: the INDEX variable
        xarg: the XARG variable
        rels: an iterable of ElementaryPredications
        hcons: an iterable of HandleConstraints
        icons: an iterable of IndividualConstraints
        lnk: the Lnk object associating the MRS to the surface form
        surface: the surface string
        identifier: a discourse-utterance id
        vars: a mapping of variables to a list of (property, value) pairs
    Returns:
        An Xmrs object

    Example:

    >>> m = Mrs(
    >>>     top='h0',
    >>>     index='e2',
    >>>     rels=[ElementaryPredication(
    >>>         Pred.stringpred('_rain_v_1_rel'),
    >>>         label='h1',
    >>>         args={'ARG0': 'e2'},
    >>>         vars={'e2': {'SF': 'prop-or-ques', 'TENSE': 'present'}}
    >>>     )],
    >>>     hcons=[HandleConstraint('h0', 'qeq', 'h1')]
    >>> )
    """
    eps = list(rels or [])
    hcons = list(hcons or [])
    icons = list(icons or [])
    if vars is None: vars = {}
    # first give eps a nodeid (this is propagated to args)
    next_nodeid = FIRST_NODEID
    for ep in eps:
        if ep.nodeid is not None and ep.nodeid >= next_nodeid:
            next_nodeid = ep.nodeid + 1
    eps_ = []
    for i, ep in enumerate(eps):
        if ep.nodeid is None:
            eps_.append(tuple([next_nodeid + i] + list(ep[1:])))
        else:
            eps_.append(ep)
    return Xmrs(top=top, index=index, xarg=xarg,
                eps=eps_, hcons=hcons, icons=icons, vars=vars,
                lnk=lnk, surface=surface, identifier=identifier)


def Rmrs(top=None, index=None, xarg=None,
         eps=None, args=None, hcons=None, icons=None,
         lnk=None, surface=None, identifier=None, vars=None):
    """
    Construct an |Xmrs| from RMRS components.

    Robust Minimal Recursion Semantics (RMRS) are like MRS, but all
    |EPs| have a nodeid ("anchor"), and |Arguments| are not contained
    by the source |EPs|, but instead reference the nodeid of their |EP|.

    Args:
        top: the TOP (or maybe LTOP) variable
        index: the INDEX variable
        xarg: the XARG variable
        eps: an iterable of EPs
        args: a nested mapping of {nodeid: {rargname: value}}
        hcons: an iterable of HandleConstraint objects
        icons: an iterable of IndividualConstraint objects
        lnk: the Lnk object associating the MRS to the surface form
        surface: the surface string
        identifier: a discourse-utterance id
        vars: a mapping of variables to a list of (property, value) pairs
    Returns:
        An Xmrs object

    Example:

    >>> m = Rmrs(
    >>>     top='h0',
    >>>     index='e2',
    >>>     eps=[ElementaryPredication(
    >>>         10000,
    >>>         Pred.stringpred('_rain_v_1_rel'),
    >>>         'h1'
    >>>     )],
    >>>     args={10000: {'ARG0': 'e2'}},
    >>>     hcons=[HandleConstraint('h0', 'qeq', 'h1'),
    >>>     vars={'e2': {'SF': 'prop-or-ques', 'TENSE': 'present'}}
    >>> )
    """
    eps = list(eps or [])
    args = list(args or [])
    if vars is None: vars = {}
    for arg in args:
        if arg.nodeid is None:
            raise XmrsStructureError("RMRS args must have a nodeid.")
    # make the EPs more MRS-like (with arguments)
    for ep in eps:
        if ep.nodeid is None:
            raise XmrsStructureError("RMRS EPs must have a nodeid.")
        epargs = ep.args
        for rargname, value in args.get(ep.nodeid, {}).items():
            epargs[rargname] = value
    hcons = list(hcons or [])
    icons = list(icons or [])
    return Xmrs(top=top, index=index, xarg=xarg,
                eps=eps, hcons=hcons, icons=icons, vars=vars,
                lnk=lnk, surface=surface, identifier=identifier)


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
        nodes: an iterable of Node objects
        links: an iterable of Link objects
        lnk: the Lnk object associating the MRS to the surface form
        surface: the surface string
        identifier: a discourse-utterance id
    Returns:
        An Xmrs object

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
    top=labels[LTOP_NODEID]
    index = xarg = None  # for now; maybe get them from kwargs?
    # initialize args with ARG0 for intrinsic variables
    args = {nid: {IVARG_ROLE: iv} for nid, iv in ivs.items()}
    hcons = []
    for l in links:
        if l.start not in args:
            args[l.start] = {}
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
                hole = vgen.new(HANDLESORT)[0]
                hcons += [qeq(hole, labels[l.end])]
                args[l.start][l.rargname] = hole
                # if the arg is RSTR, it's a quantifier, so we can
                # find its intrinsic variable now
                if l.rargname.upper() == RSTR_ROLE:
                    ivs[l.start] = ivs[l.end]
                    args[l.start][IVARG_ROLE] = ivs[l.start]
            elif l.post == HEQ_POST:
                args[l.start][l.rargname] = labels[l.end]
            else:  # NEQ_POST or EQ_POST
                args[l.start][l.rargname] = ivs[l.end]
    eps = []
    for node in nodes:
        nid = node.nodeid
        if node.carg is not None:
            args[nid][CONSTARG_ROLE] = node.carg
        ep = (nid, node.pred, labels[nid], args[nid],
              node.lnk, node.surface, node.base)
        eps.append(ep)

    icons = None  # future feature

    return Xmrs(
        top=top, index=index, xarg=xarg,
        eps=eps, hcons=hcons, icons=icons, vars=vgen.store,
        lnk=lnk, surface=surface, identifier=identifier
    )

def _make_labels(nodes, links, vgen):
    eq_edges = defaultdict(set)
    for l in links:
        if l.post == EQ_POST:
            eq_edges[l.start].add(l.end)
            eq_edges[l.end].add(l.start)
    # thanks: http://stackoverflow.com/a/13837045/1441112
    seen = set()
    def conjunction(nodeid):
        nids = {nodeid}
        while nids:
            nid = nids.pop()
            seen.add(nid)
            nids |= eq_edges[nid] - seen
            yield nid
    labels = {}
    # be sure to do LTOP_NODEID first so it gets h0
    for nid in chain([LTOP_NODEID], (node.nodeid for node in nodes)):
        if nid not in seen:
            lbl = vgen.new(HANDLESORT)[0]
            for conj_nid in conjunction(nid):
                labels[conj_nid] = lbl
    return labels

def _make_ivs(nodes, vgen):
    ivs = {}
    for node in nodes:
        # quantifiers share their IV with the quantifiee. It will be
        # selected later during argument construction
        if not node.is_quantifier():
            props = dict((key, val) for key, val in node.sortinfo.items()
                         if key != CVARSORT)
            ivs[node.nodeid] = vgen.new(node.cvarsort, props)[0]
    return ivs
