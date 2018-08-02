
"""
Classes and functions for general \*MRS processing.
"""

from collections import (defaultdict, deque)
from itertools import chain

from delphin.exceptions import (XmrsError, XmrsStructureError)
from delphin.util import safe_int
from .components import (
    ElementaryPredication, HandleConstraint, IndividualConstraint,
    Lnk, _LnkMixin, var_re, var_sort, _VarGenerator,
    Pred, Node, nodes, Link, links
)
from .config import (
    HANDLESORT, UNKNOWNSORT, LTOP_NODEID, FIRST_NODEID,
    IVARG_ROLE, CONSTARG_ROLE, RSTR_ROLE, BARE_EQ_ROLE,
    EQ_POST, HEQ_POST, H_POST, NIL_POST, CVARSORT
)


class Xmrs(_LnkMixin):
    """
    Xmrs is a common class for Mrs, Rmrs, and Dmrs objects.

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

    Xmrs can be instantiated directly, but it may be more
    convenient to use the :func:`Mrs`, :func:`Rmrs`, or :func:`Dmrs`
    constructor functions.

    Variables are simply strings, but must be of the proper form
    in order to be recognized as variables and not constants. The
    form is basically a sequence of non-integers followed by a
    sequence of integers, but see :data:`delphin.mrs.components.var_re`
    for the regular expression used to determine a match.

    The *eps* argument is an iterable of tuples representing
    ElementaryPredications. These can be objects of the
    ElementaryPredication class itself, or an equivalent tuple.
    The same goes for *hcons* and *icons* with the
    HandleConstraint and IndividualConstraint classes,
    respectively.

    Attributes:
        top: the top (i.e. LTOP) handle
        index: the semantic index
        xarg: the external argument
        lnk (:class:`~delphin.mrs.components.Lnk`): surface alignment
        surface: the surface string
        identifier: a discourse-utterance ID (often unset)
    """

    def __init__(self, top=None, index=None, xarg=None,
                 eps=None, hcons=None, icons=None, vars=None,
                 lnk=None, surface=None, identifier=None):
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

        #: A Lnk object to associate the Xmrs to the surface form
        self.lnk = lnk  # Lnk object (MRS-level lnk spans the whole input)
        #: The surface string
        self.surface = surface  # The surface string
        #: A discourse-utterance id
        self.identifier = identifier  # Associates an utterance with the RMRS

    @classmethod
    def from_xmrs(cls, xmrs, **kwargs):
        """
        Facilitate conversion among subclasses.

        Args:
            xmrs (:class:`Xmrs`): instance to convert from; possibly
                an instance of a subclass, such as :class:`Mrs` or
                :class:`Dmrs`
            **kwargs: additional keyword arguments that may be used
                by a subclass's redefinition of :meth:`from_xmrs`.
        """
        x = cls()
        x.__dict__.update(xmrs.__dict__)
        return x

    def add_eps(self, eps):
        """
        Incorporate the list of EPs given by *eps*.
        """
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
            nodeid, lbl = ep.nodeid, ep.label
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
        """
        Incorporate the list of HandleConstraints given by *hcons*.
        """
        # (hi, relation, lo)
        _vars = self._vars
        _hcons = self._hcons
        for hc in hcons:
            try:
                if not isinstance(hc, HandleConstraint):
                    hc = HandleConstraint(*hc)
            except TypeError:
                raise XmrsError('Invalid HCONS data: {}'.format(repr(hc)))

            hi = hc.hi
            lo = hc.lo
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
        """
        Incorporate the individual constraints given by *icons*.
        """
        _vars, _icons = self._vars, self._icons
        for ic in icons:
            try:
                if not isinstance(ic, IndividualConstraint):
                    ic = IndividualConstraint(*ic)
            except TypeError:
                raise XmrsError('Invalid ICONS data: {}'.format(repr(ic)))
            left = ic.left
            right = ic.right
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
        return '<{} object ({}) at {}>'.format(
            self.__class__.__name__, stringform, id(self)
        )

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
        for v in self.variables():
            if self.properties(v) != other.properties(v):
                return False
        return True

    @property
    def ltop(self):
        """
        The top handle if specified; `None` otherwise.

        Note:
            Equivalent to :attr:`top`
        """
        return self.top

    # basic access to internal structures

    def nodeid(self, iv, quantifier=False):
        """
        Return the nodeid of the predication selected by *iv*.

        Args:
            iv: the intrinsic variable of the predication to select
            quantifier: if `True`, treat *iv* as a bound variable and
                find its quantifier; otherwise the non-quantifier will
                be returned
        """
        return next(iter(self.nodeids(ivs=[iv], quantifier=quantifier)), None)

    def nodeids(self, ivs=None, quantifier=None):
        """
        Return the list of nodeids given by *ivs*, or all nodeids.

        Args:
            ivs: the intrinsic variables of the predications to select;
                if `None`, return all nodeids (but see *quantifier*)
            quantifier: if `True`, only return nodeids of quantifiers;
                if `False`, only return non-quantifiers; if `None`
                (the default), return both
        """
        if ivs is None:
            nids = list(self._nodeids)
        else:
            _vars = self._vars
            nids = []
            for iv in ivs:
                if iv in _vars and IVARG_ROLE in _vars[iv]['refs']:
                    nids.extend(_vars[iv]['refs'][IVARG_ROLE])
                else:
                    raise KeyError(iv)
        if quantifier is not None:
            nids = [n for n in nids if self.ep(n).is_quantifier()==quantifier]
        return nids

    def ep(self, nodeid):
        """
        Return the ElementaryPredication with the given *nodeid*.
        """
        return self._eps[nodeid]

    def eps(self, nodeids=None):
        """
        Return the EPs with the given *nodeid*, or all EPs.

        Args:
            nodeids: an iterable of nodeids of EPs to return; if
                `None`, return all EPs
        """
        if nodeids is None: nodeids = self._nodeids
        _eps = self._eps
        return [_eps[nodeid] for nodeid in nodeids]

    def hcon(self, hi):
        """
        Return the HandleConstraint with high variable *hi*.
        """
        return self._hcons[hi]

    def hcons(self):
        """
        Return the list of HCONS.
        """
        return list(self._hcons.values())

    def icons(self, left=None):
        """
        Return the ICONS with left variable *left*, or all ICONS.

        Args:
            left: the left variable of the ICONS to return; if `None`,
                return all ICONS
        """
        if left is not None:
            return self._icons[left]
        else:
            return list(chain.from_iterable(self._icons.values()))

    def variables(self):
        """
        Return the list of all variables.
        """
        return list(self._vars)

    # access to internal sub-structures

    def properties(self, var_or_nodeid, as_list=False):
        """
        Return a dictionary of variable properties for *var_or_nodeid*.

        Args:
            var_or_nodeid: if a variable, return the properties
                associated with the variable; if a nodeid, return the
                properties associated with the intrinsic variable of the
                predication given by the nodeid
        """
        props = []
        if var_or_nodeid in self._vars:
            props = self._vars[var_or_nodeid]['props']
        elif var_or_nodeid in self._eps:
            var = self._eps[var_or_nodeid][3].get(IVARG_ROLE)
            props = self._vars.get(var, {}).get('props', [])
        else:
            raise KeyError(var_or_nodeid)
        if not as_list:
            props = dict(props)
        return props

    def pred(self, nodeid):
        """
        Return the Pred object for the predications given by *nodeid*.
        """
        return self._eps[nodeid][1]

    def preds(self, nodeids=None):
        """
        Return the Pred objects for *nodeids*, or all Preds.

        Args:
            nodeids: an iterable of nodeids of predications to return
                Preds from; if `None`, return all Preds
        """
        if nodeids is None: nodeids = self._nodeids
        _eps = self._eps
        return [_eps[nid][1] for nid in nodeids]

    def label(self, nodeid):
        """
        Return the label of the predication given by *nodeid*
        """
        return self._eps[nodeid][2]

    def labels(self, nodeids=None):
        """
        Return the list of labels for *nodeids*, or all labels.

        Args:
            nodeids: an iterable of nodeids for predications to get
                labels from; if `None`, return labels for all
                predications
        Note:
            This returns the label of each predication, even if it's
            shared by another predication. Thus,
            `zip(nodeids, xmrs.labels(nodeids))` will pair nodeids with
            their labels.
        Returns:
            A list of labels
        """
        if nodeids is None: nodeids = self._nodeids
        _eps = self._eps
        return [_eps[nid][2] for nid in nodeids]

    def args(self, nodeid):
        """
        Return the arguments for the predication given by *nodeid*.

        All arguments (including intrinsic and constant arguments) are
        included. MOD/EQ links are not considered
        arguments. If only arguments that target other predications are
        desired, see :meth:`outgoing_args`.

        Args:
            nodeid: the nodeid of the EP that is the arguments' source
        Returns:
            dict: `{role: tgt}`
        """
        return dict(self._eps[nodeid][3])

    # calculated sub-structures

    def outgoing_args(self, nodeid):
        """
        Return the arguments going from *nodeid* to other predications.

        Valid arguments include regular variable arguments and scopal
        (label-selecting or HCONS) arguments. MOD/EQ
        links, intrinsic arguments, and constant arguments are not
        included.

        Args:
            nodeid: the nodeid of the EP that is the arguments' source
        Returns:
            dict: `{role: tgt}`
        """
        _vars = self._vars
        _hcons = self._hcons
        args = self.args(nodeid)  # args is a copy; we can edit it
        for arg, val in list(args.items()):
            # don't include constant args or intrinsic args
            if arg == IVARG_ROLE or val not in _vars:
                del args[arg]
            else:
                refs = _vars[val]['refs']
                # don't include if not HCONS or pointing to other IV or LBL
                if not (val in _hcons or IVARG_ROLE in refs or 'LBL' in refs):
                    del args[arg]
        return args

    def incoming_args(self, nodeid):
        """
        Return the arguments that target *nodeid*.

        Valid arguments include regular variable arguments and scopal
        (label-selecting or HCONS) arguments. MOD/EQ
        links and intrinsic arguments are not included.

        Args:
            nodeid: the nodeid of the EP that is the arguments' target
        Returns:
            dict: `{source_nodeid: {rargname: value}}`
        """
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
        Return the set of nodeids for predications that share *label*.

        Args:
            label: the label that returned nodeids share.
        Returns:
            A set of nodeids, which may be an empty set.
        """
        return self._vars[label]['refs']['LBL']

    def labelset_heads(self, label):
        """
        Return the heads of the labelset selected by *label*.

        Args:
            label: the label from which to find head nodes/EPs.
        Returns:
            An iterable of nodeids.
        """
        _eps = self._eps
        _vars = self._vars
        _hcons = self._hcons
        nodeids = {nodeid: _eps[nodeid][3].get(IVARG_ROLE, None)
                for nodeid in _vars[label]['refs']['LBL']}
        if len(nodeids) <= 1:
            return list(nodeids)

        scope_sets = {}
        for nid in nodeids:
            scope_sets[nid] = _ivs_in_scope(nid, _eps, _vars, _hcons)

        out = {}
        for n in nodeids:
            out[n] = 0
            for role, val in _eps[n][3].items():
                if role == IVARG_ROLE or role == CONSTARG_ROLE:
                    continue
                elif any(val in s for n2, s in scope_sets.items() if n2 != n):
                    out[n] += 1

        candidates = [n for n, out_deg in out.items() if out_deg == 0]
        rank = {}
        for n in candidates:
            iv = nodeids[n]
            pred = _eps[n][1]
            if iv in _vars and self.nodeid(iv, quantifier=True) is not None:
                rank[n] = 0
            elif pred.is_quantifier():
                rank[n] = 0
            elif pred.type == Pred.ABSTRACT:
                rank[n] = 2
            else:
                rank[n] = 1

        return sorted(candidates, key=lambda n: rank[n])

    def subgraph(self, nodeids):
        """
        Return an Xmrs object with only the specified *nodeids*.

        Necessary variables and arguments are also included in order to
        connect any nodes that are connected in the original Xmrs.

        Args:
            nodeids: the nodeids of the nodes/EPs to include in the
                subgraph.
        Returns:
            An :class:`Xmrs` object.
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
        Return `True` if the Xmrs represents a connected graph.

        Subgraphs can be connected through things like arguments,
        QEQs, and label equalities.
        """
        nids = set(self._nodeids)  # the nids left to find
        if len(nids) == 0:
            raise XmrsError('Cannot compute connectedness of an empty Xmrs.')
        # build a basic dict graph of relations
        edges = []
        # label connections
        for lbl in self.labels():
            lblset = self.labelset(lbl)
            edges.extend((x, y) for x in lblset for y in lblset if x != y)
        # argument connections
        _vars = self._vars
        for nid in nids:
            for rarg, tgt in self.args(nid).items():
                if tgt not in _vars:
                    continue
                if IVARG_ROLE in _vars[tgt]['refs']:
                    tgtnids = list(_vars[tgt]['refs'][IVARG_ROLE])
                elif tgt in self._hcons:
                    tgtnids = list(self.labelset(self.hcon(tgt)[2]))
                elif 'LBL' in _vars[tgt]['refs']:
                    tgtnids = list(_vars[tgt]['refs']['LBL'])
                else:
                    tgtnids = []
                # connections are bidirectional
                edges.extend((nid, t) for t in tgtnids if nid != t)
                edges.extend((t, nid) for t in tgtnids if nid != t)
        g = {nid: set() for nid in nids}
        for x, y in edges:
            g[x].add(y)
        connected_nids = _bfs(g)
        if connected_nids == nids:
            return True
        elif connected_nids.difference(nids):
            raise XmrsError(
                'Possibly bogus nodeids: {}'
                .format(', '.join(connected_nids.difference(nids)))
            )
        return False

    def is_well_formed(self):
        """
        Return `True` if the Xmrs is well-formed, `False` otherwise.

        See :meth:`validate`
        """
        try:
            self.validate()
        except XmrsError:
            return False
        return True

    def validate(self):
        """
        Check that the Xmrs is well-formed.

        The Xmrs is analyzed and a list of problems is compiled. If
        any problems exist, an :exc:`XmrsError` is raised with the list
        joined as the error message. A well-formed Xmrs has the
        following properties:

        * All predications have an intrinsic variable
        * Every intrinsic variable belongs one predication and maybe
          one quantifier
        * Every predication has no more than one quantifier
        * All predications have a label
        * The graph of predications form a net (i.e. are connected).
          Connectivity can be established with variable arguments,
          QEQs, or label-equality.
        * The lo-handle for each QEQ must exist as the label of a
          predication
        """
        errors = []
        ivs, bvs = {}, {}
        _vars = self._vars
        _hcons = self._hcons
        labels = defaultdict(set)
        # ep_args = {}
        for ep in self.eps():
            nid, lbl, args, is_q = (
                ep.nodeid, ep.label, ep.args, ep.is_quantifier()
            )
            if lbl is None:
                errors.append('EP ({}) is missing a label.'.format(nid))
            labels[lbl].add(nid)
            iv = args.get(IVARG_ROLE)
            if iv is None:
                errors.append('EP {nid} is missing an intrinsic variable.'
                              .format(nid))
            if is_q:
                if iv in bvs:
                    errors.append('{} is the bound variable for more than '
                                  'one quantifier.'.format(iv))
                bvs[iv] = nid
            else:
                if iv in ivs:
                    errors.append('{} is the intrinsic variable for more '
                                  'than one EP.'.format(iv))
                ivs[iv] = nid
            # ep_args[nid] = args
        for hc in _hcons.values():
            if hc[2] not in labels:
                errors.append('Lo variable of HCONS ({} {} {}) is not the '
                              'label of any EP.'.format(*hc))
        if not self.is_connected():
            errors.append('Xmrs structure is not connected.')
        if errors:
            raise XmrsError('\n'.join(errors))


class Mrs(Xmrs):
    """
    Construct an :class:`Xmrs` using MRS components.

    Formally, Minimal Recursion Semantics (MRS) have a top handle, a
    bag of Elementary Predications, and a bag of Handle Constraints.
    All arguments, including intrinsic arguments and constant
    arguments, are expected to be contained by the EPs.

    Args:
        top: the TOP (or LTOP) variable
        index: the INDEX variable
        xarg: the XARG variable
        rels: an iterable of ElementaryPredications
        hcons: an iterable of HandleConstraints
        icons: an iterable of IndividualConstraints
        lnk: the Lnk object associating the MRS to the surface form
        surface: the surface string
        identifier: a discourse-utterance id
        vars: a mapping of variables to a list of (property, value) pairs

    Example:

    >>> m = Mrs(
    >>>     top='h0',
    >>>     index='e2',
    >>>     rels=[ElementaryPredication(
    >>>         Pred.surface('_rain_v_1_rel'),
    >>>         label='h1',
    >>>         args={'ARG0': 'e2'},
    >>>         vars={'e2': {'SF': 'prop-or-ques', 'TENSE': 'present'}}
    >>>     )],
    >>>     hcons=[HandleConstraint('h0', 'qeq', 'h1')]
    >>> )
    """
    def __init__(
            self,
            top=None, index=None, xarg=None,
            rels=None, hcons=None, icons=None,
            lnk=None, surface=None, identifier=None, vars=None):
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
        super(Mrs, self).__init__(
            top=top, index=index, xarg=xarg,
            eps=eps_, hcons=hcons, icons=icons, vars=vars,
            lnk=lnk, surface=surface, identifier=identifier
        )

    def to_dict(self, short_pred=True, properties=True):
        """
        Encode the Mrs as a dictionary suitable for JSON serialization.
        """
        def _lnk(obj): return {'from': obj.cfrom, 'to': obj.cto}
        def _ep(ep, short_pred=True):
            p = ep.pred.short_form() if short_pred else ep.pred.string
            d = dict(label=ep.label, predicate=p, arguments=ep.args)
            if ep.lnk is not None: d['lnk'] = _lnk(ep)
            return d
        def _hcons(hc): return {'relation':hc[1], 'high':hc[0], 'low':hc[2]}
        def _icons(ic): return {'relation':ic[1], 'left':ic[0], 'right':ic[2]}
        def _var(v):
            d = {'type': var_sort(v)}
            if properties and self.properties(v):
                d['properties'] = self.properties(v)
            return d

        d = dict(
            relations=[_ep(ep, short_pred=short_pred) for ep in self.eps()],
            constraints=([_hcons(hc) for hc in self.hcons()] +
                         [_icons(ic) for ic in self.icons()]),
            variables={v: _var(v) for v in self.variables()}
        )
        if self.top is not None: d['top'] = self.top
        if self.index is not None: d['index'] = self.index
        # if self.xarg is not None: d['xarg'] = self.xarg
        # if self.lnk is not None: d['lnk'] = self.lnk
        # if self.surface is not None: d['surface'] = self.surface
        # if self.identifier is not None: d['identifier'] = self.identifier
        return d

    @classmethod
    def from_dict(cls, d):
        """
        Decode a dictionary, as from :meth:`to_dict`, into an Mrs object.
        """
        def _lnk(o):
            return None if o is None else Lnk.charspan(o['from'], o['to'])
        def _ep(ep):
            return ElementaryPredication(
                nodeid=None,
                pred=Pred.surface_or_abstract(ep['predicate']),
                label=ep['label'],
                args=ep.get('arguments', {}),
                lnk=_lnk(ep.get('lnk')),
                surface=ep.get('surface'),
                base=ep.get('base')
            )
        eps = [_ep(rel) for rel in d.get('relations', [])]
        hcons = [(c['high'], c['relation'], c['low'])
                 for c in d.get('constraints', []) if 'high' in c]
        icons = [(c['high'], c['relation'], c['low'])
                 for c in d.get('constraints', []) if 'left' in c]
        variables = {var: list(data.get('properties', {}).items())
                     for var, data in d.get('variables', {}).items()}
        return cls(
            top=d.get('top'),
            index=d.get('index'),
            xarg=d.get('xarg'),
            rels=eps,
            hcons=hcons,
            icons=icons,
            lnk=_lnk(d.get('lnk')),
            surface=d.get('surface'),
            identifier=d.get('identifier'),
            vars=variables
        )


def Rmrs(top=None, index=None, xarg=None,
         eps=None, args=None, hcons=None, icons=None,
         lnk=None, surface=None, identifier=None, vars=None):
    """
    Construct an :class:`Xmrs` from RMRS components.

    Robust Minimal Recursion Semantics (RMRS) are like MRS, but all
    predications have a nodeid ("anchor"), and arguments are not
    contained by the source predications, but instead reference the
    nodeid of their predication.

    Args:
        top: the TOP (or maybe LTOP) variable
        index: the INDEX variable
        xarg: the XARG variable
        eps: an iterable of EPs
        args: a nested mapping of `{nodeid: {rargname: value}}`
        hcons: an iterable of HandleConstraint objects
        icons: an iterable of IndividualConstraint objects
        lnk: the Lnk object associating the MRS to the surface form
        surface: the surface string
        identifier: a discourse-utterance id
        vars: a mapping of variables to a list of `(property, value)`
            pairs

    Example:

    >>> m = Rmrs(
    >>>     top='h0',
    >>>     index='e2',
    >>>     eps=[ElementaryPredication(
    >>>         10000,
    >>>         Pred.surface('_rain_v_1_rel'),
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


class Dmrs(Xmrs):
    """
    Construct an :class:`Xmrs` using DMRS components.

    Dependency Minimal Recursion Semantics (DMRS) have a list of Node
    objects and a list of Link objects. There are no variables or
    handles, so these will need to be created in order to make an
    Xmrs object. The *top* node may be set directly via a parameter
    or may be implicitly set via a Link from the special nodeid 0. If
    both are given, the link is ignored. The *index* and *xarg* nodes
    may only be set via parameters.

    Args:
        nodes: an iterable of Node objects
        links: an iterable of Link objects
        top: the scopal top node
        index: the non-scopal top node
        xarg: the external argument node
        lnk: the Lnk object associating the MRS to the surface form
        surface: the surface string
        identifier: a discourse-utterance id

    Example:

    >>> rain = Node(10000, Pred.surface('_rain_v_1_rel'),
    >>>             sortinfo={'cvarsort': 'e'})
    >>> ltop_link = Link(0, 10000, post='H')
    >>> d = Dmrs([rain], [ltop_link])
    """
    def __init__(
            self,
            nodes=None, links=None,
            top=None, index=None, xarg=None,
            lnk=None, surface=None, identifier=None):
        if nodes is None: nodes = []
        if links is None: links = []
        qeq = HandleConstraint.qeq
        vgen = _VarGenerator()

        # check this here to streamline things later
        if top is not None:
            links = [Link(LTOP_NODEID, top, None, H_POST)] + list(links)
            top = None

        labels = _make_labels(nodes, links, vgen)
        qs = set(l.start for l in links
                 if (l.rargname or '').upper() == RSTR_ROLE)
        ivs = _make_ivs(nodes, vgen, qs)

        # initialize args with ARG0 for intrinsic variables
        args = {nid: {IVARG_ROLE: iv} for nid, iv in ivs.items()}
        hcons = []
        for l in links:
            if l.start not in args:
                args[l.start] = {}
            if safe_int(l.start) != LTOP_NODEID:
                if not l.rargname or l.rargname.upper() == BARE_EQ_ROLE:
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
            # ignore top link if top is already set
            elif top is None:
                # The most explicit value of post for a link that denotes a
                # TOP that is qeq to a label is H_POST, but I equally accept
                # NIL_POST for backward compatibility. HEQ_POST denotes a TOP
                # that selects a label directly (and this label equality would
                # have been captured earlier)
                top = labels[l.start]
                if l.post == H_POST or l.post == NIL_POST:
                    hcons += [qeq(top, labels[l.end])]
        eps = []
        for node in nodes:
            nid = node.nodeid
            if node.carg is not None:
                args[nid][CONSTARG_ROLE] = node.carg
            ep = (nid, node.pred, labels[nid], args[nid],
                  node.lnk, node.surface, node.base)
            eps.append(ep)

        icons = None  # future feature

        super(Dmrs, self).__init__(
            top=top, index=ivs.get(index), xarg=ivs.get(xarg),
            eps=eps, hcons=hcons, icons=icons, vars=vgen.store,
            lnk=lnk, surface=surface, identifier=identifier
        )

    def to_dict(self, short_pred=True, properties=True):
        """
        Encode the Dmrs as a dictionary suitable for JSON serialization.
        """
        qs = set(self.nodeids(quantifier=True))
        def _lnk(obj): return {'from': obj.cfrom, 'to': obj.cto}
        def _node(node, short_pred=True):
            p = node.pred.short_form() if short_pred else node.pred.string
            d = dict(nodeid=node.nodeid, predicate=p)
            if node.lnk is not None: d['lnk'] = _lnk(node)
            if properties and node.sortinfo:
                if node.nodeid not in qs:
                    d['sortinfo'] = node.sortinfo
            if node.surface is not None: d['surface'] = node.surface
            if node.base is not None: d['base'] = node.base
            if node.carg is not None: d['carg'] = node.carg
            return d
        def _link(link): return {
            'from': link.start, 'to': link.end,
            'rargname': link.rargname, 'post': link.post
        }

        d = dict(
            nodes=[_node(n) for n in nodes(self)],
            links=[_link(l) for l in links(self)]
        )
        # if self.top is not None: ... currently handled by links
        if self.index is not None:
            idx = self.nodeid(self.index)
            if idx is not None:
                d['index'] = idx
        if self.xarg is not None:
            xarg = self.nodeid(self.index)
            if xarg is not None:
                d['index'] = xarg
        if self.lnk is not None: d['lnk'] = _lnk(self)
        if self.surface is not None: d['surface'] = self.surface
        if self.identifier is not None: d['identifier'] = self.identifier
        return d

    @classmethod
    def from_dict(cls, d):
        """
        Decode a dictionary, as from :meth:`to_dict`, into a Dmrs object.
        """
        def _node(obj):
            return Node(
                obj.get('nodeid'),
                Pred.surface_or_abstract(obj.get('predicate')),
                sortinfo=obj.get('sortinfo'),
                lnk=_lnk(obj.get('lnk')),
                surface=obj.get('surface'),
                base=obj.get('base'),
                carg=obj.get('carg')
            )
        def _link(obj):
            return Link(obj.get('from'), obj.get('to'),
                        obj.get('rargname'), obj.get('post'))
        def _lnk(o):
            return None if o is None else Lnk.charspan(o['from'], o['to'])
        return cls(
            nodes=[_node(n) for n in d.get('nodes', [])],
            links=[_link(l) for l in d.get('links', [])],
            lnk=_lnk(d.get('lnk')),
            surface=d.get('surface'),
            identifier=d.get('identifier')
        )

    def to_triples(self, short_pred=True, properties=True):
        """
        Encode the Dmrs as triples suitable for PENMAN serialization.
        """
        ts = []
        qs = set(self.nodeids(quantifier=True))
        for n in nodes(self):
            pred = n.pred.short_form() if short_pred else n.pred.string
            ts.append((n.nodeid, 'predicate', pred))
            if n.lnk is not None:
                ts.append((n.nodeid, 'lnk', '"{}"'.format(str(n.lnk))))
            if n.carg is not None:
                ts.append((n.nodeid, 'carg', '"{}"'.format(n.carg)))
            if properties and n.nodeid not in qs:
                for key, value in n.sortinfo.items():
                    ts.append((n.nodeid, key.lower(), value))

        for l in links(self):
            if safe_int(l.start) == LTOP_NODEID:
                ts.append((l.start, 'top', l.end))
            else:
                relation = '{}-{}'.format(l.rargname.upper(), l.post)
                ts.append((l.start, relation, l.end))
        return ts

    @classmethod
    def from_triples(cls, triples, remap_nodeids=True):
        """
        Decode triples, as from :meth:`to_triples`, into a Dmrs object.
        """
        top_nid = str(LTOP_NODEID)
        top = lnk = surface = identifier = None
        nids, nd, edges = [], {}, []
        for src, rel, tgt in triples:
            src, tgt = str(src), str(tgt)  # hack for int-converted src/tgt
            if src == top_nid and rel == 'top':
                top = tgt
                continue
            elif src not in nd:
                if top is None:
                    top=src
                nids.append(src)
                nd[src] = {'pred': None, 'lnk': None, 'carg': None, 'si': []}
            if rel == 'predicate':
                nd[src]['pred'] = Pred.surface_or_abstract(tgt)
            elif rel == 'lnk':
                cfrom, cto = tgt.strip('"<>').split(':')
                nd[src]['lnk'] = Lnk.charspan(int(cfrom), int(cto))
            elif rel == 'carg':
                if (tgt[0], tgt[-1]) == ('"', '"'):
                    tgt = tgt[1:-1]
                nd[src]['carg'] = tgt
            elif rel.islower():
                nd[src]['si'].append((rel, tgt))
            else:
                rargname, post = rel.rsplit('-', 1)
                edges.append((src, tgt, rargname, post))
        if remap_nodeids:
            nidmap = dict((nid, FIRST_NODEID+i) for i, nid in enumerate(nids))
        else:
            nidmap = dict((nid, nid) for nid in nids)
        nodes = [
            Node(
                nodeid=nidmap[nid],
                pred=nd[nid]['pred'],
                sortinfo=nd[nid]['si'],
                lnk=nd[nid]['lnk'],
                carg=nd[nid]['carg']
            ) for i, nid in enumerate(nids)
        ]
        links = [Link(nidmap[s], nidmap[t], r, p) for s, t, r, p in edges]
        if top:
            links.append(Link(LTOP_NODEID, nidmap[top], None, H_POST))
        return cls(
            nodes=nodes,
            links=links,
            lnk=lnk,
            surface=surface,
            identifier=identifier
        )

def _make_labels(nodes, links, vgen):
    eq_edges = defaultdict(set)
    nids = [node.nodeid for node in nodes]
    for l in links:
        if safe_int(l.start) == LTOP_NODEID:
            vgen.vid = 0  # start at h0 for TOP
            nids = [l.start] + nids
        if l.post == EQ_POST:
            eq_edges[l.start].add(l.end)
            eq_edges[l.end].add(l.start)
    seen = set()
    labels = {}
    for nid in nids:
        if nid not in seen:
            lbl = vgen.new(HANDLESORT)[0]
            for conj_nid in _bfs(eq_edges, nid):
                labels[conj_nid] = lbl
                seen.add(conj_nid)
    return labels

def _make_ivs(nodes, vgen, qs):
    ivs = {}
    for node in nodes:
        # quantifiers share their IV with the quantifiee. It will be
        # selected later during argument construction
        if node.nodeid not in qs:
            props = dict((key, val) for key, val in node.sortinfo.items()
                         if key != CVARSORT)
            ivs[node.nodeid] = vgen.new(node.cvarsort, props)[0]
    return ivs

# inspired by NetworkX is_connected():
# https://networkx.github.io/documentation/latest/_modules/networkx/algorithms/components/connected.html#is_connected
def _bfs(g, start=None):
    if not g:
        return {start} if start is not None else set()
    seen = set()
    if start is None:
        start = next(iter(g))
    agenda = deque([start])
    while agenda:
        x = agenda.popleft()
        if x not in seen:
            seen.add(x)
            agenda.extend(y for y in g.get(x, []) if y not in seen)
    return seen

def _ivs_in_scope(nodeid, _eps, _vars, _hcons):
    ivs = set()
    args = _eps[nodeid][3]
    for role, val in args.items():
        if role == IVARG_ROLE:
            ivs.add(val)
        elif role == CONSTARG_ROLE:
            pass
        elif var_sort(val) == HANDLESORT:
            if val in _hcons:
                val = _hcons[val].lo
            for conj_nid in _vars[val]['refs']['LBL']:
                ivs.update(_ivs_in_scope(conj_nid, _eps, _vars, _hcons))
    return ivs
