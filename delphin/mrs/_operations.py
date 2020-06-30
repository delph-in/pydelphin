
"""
Operations on MRS structures
"""

from typing import Iterable, Dict, Set, Optional

from delphin import variable
from delphin import predicate
from delphin.sembase import Identifier, property_priority
from delphin import scope
from delphin import mrs
from delphin import util


def is_connected(m: mrs.MRS) -> bool:
    """
    Return `True` if *m* is a fully-connected MRS.

    A connected MRS is one where, when viewed as a graph, all EPs are
    connected to each other via regular (non-scopal) arguments, scopal
    arguments (including qeqs), or label equalities.
    """
    ids = {ep.id for ep in m.rels}
    g: Dict[Identifier, Set[Identifier]] = {id: set() for id in ids}
    # first establish links from labels and intrinsic variables to EPs
    for ep in m.rels:
        id, lbl, iv = ep.id, ep.label, ep.iv
        g[id].update((lbl, iv))
        g.setdefault(lbl, set()).add(id)
        if iv:
            g.setdefault(iv, set()).add(id)
    # arguments may link EPs with IVs or labels (or qeq) as targets
    hcmap = {hc.hi: hc.lo for hc in m.hcons}
    for id, roleargs in m.arguments().items():
        for role, value in roleargs:
            value = hcmap.get(value, value)  # resolve qeq if any
            if value in g:
                g[id].add(value)
                g[value].add(id)
    return ids.issubset(util._bfs(g))


def has_intrinsic_variable_property(m: mrs.MRS) -> bool:
    """
    Return `True` if *m* satisfies the intrinsic variable property.

    An MRS has the intrinsic variable property when it passes the
    following:

    - :func:`has_complete_intrinsic_variables`
    - :func:`has_unique_intrinsic_variables`

    Note that for quantifier EPs, `ARG0` is overloaded to mean "bound
    variable". Each quantifier should have an `ARG0` that is the
    intrinsic variable of exactly one non-quantifier EP, but this
    function does not check for that.
    """
    return (has_complete_intrinsic_variables(m)
            and has_unique_intrinsic_variables(m))


def has_complete_intrinsic_variables(m: mrs.MRS) -> bool:
    """
    Return `True` if all non-quantifier EPs have intrinsic variables.
    """
    return all(ep.iv is not None
               for ep in m.rels
               if not ep.is_quantifier())


def has_unique_intrinsic_variables(m: mrs.MRS) -> bool:
    """
    Return `True` if all intrinsic variables are unique to their EPs.
    """
    ivs = [ep.iv for ep in m.rels
           if not ep.is_quantifier() and ep.iv is not None]
    return len(set(ivs)) == len(ivs)


def is_well_formed(m: mrs.MRS) -> bool:
    """
    Return `True` if MRS *m* is well-formed.

    A well-formed MRS meets the following criteria:

    - :func:`is_connected`
    - :func:`has_intrinsic_variable_property`
    - :func:`plausibly_scopes`

    The final criterion is a heuristic for determining if the MRS
    scopes by checking if handle constraints and scopal arguments have
    any immediate violations (e.g., a scopal argument selecting the
    label of its EP).
    """
    return (is_connected(m)
            and has_intrinsic_variable_property(m)
            and plausibly_scopes(m))


def plausibly_scopes(m: mrs.MRS) -> bool:
    """
    Quickly test if MRS *m* can plausibly resolve a scopal reading.

    This tests a number of things:

        - Is the MRS's top qeq to a label
        - Do any EPs scope over themselves
        - Do multiple EPs use the handle constraint
        - Is the lo handle of a qeq not actually a label
        - Are any qeqs not selected by an EP

    It does not test for transitive scopal plausibility.
    """
    scope_labels = set(ep.label for ep in m.rels)
    hcmap = {hc.hi: hc.lo for hc in m.hcons}
    if m.top not in hcmap:
        return False
    seen = set([m.top])
    for id, roleargs in m.arguments(types='h').items():
        for _, handle in roleargs:
            if handle == m[id].label:
                return False
            elif handle in hcmap:
                if handle in seen:
                    return False
                if hcmap[handle] not in scope_labels:
                    return False
                seen.add(hcmap[handle])
            elif handle in scope_labels and handle in seen:
                return False
            seen.add(handle)
    for hi, lo in hcmap.items():
        if hi not in seen or lo not in scope_labels:
            return False
    return True


def is_isomorphic(m1: mrs.MRS,
                  m2: mrs.MRS,
                  properties: bool = True) -> bool:
    """
    Return `True` if *m1* and *m2* are isomorphic MRSs.

    Isomorphicity compares the predicates of a semantic structure, the
    morphosemantic properties of their predications (if
    `properties=True`), constant arguments, and the argument structure
    between predications. Non-semantic properties like identifiers and
    surface alignments are ignored.

    Args:
        m1: the left MRS to compare
        m2: the right MRS to compare
        properties: if `True`, ensure variable properties are
            equal for mapped predications
    """
    # simple tests
    if (len(m1.rels) != len(m2.rels)
            or len(m1.hcons) != len(m2.hcons)
            or len(m1.icons) != len(m2.icons)
            or len(m1.variables) != len(m2.variables)):
        return False

    g1 = _make_mrs_isograph(m1, properties)
    g2 = _make_mrs_isograph(m2, properties)

    iso = util._vf2(g1, g2)
    return set(iso) == set(g1)


def _make_mrs_isograph(x, properties):
    g: Dict[Identifier, Dict[Optional[Identifier], str]] = {}
    g.update((v, {}) for v in x.variables)
    g.update((ep.id, {}) for ep in x.rels)

    for ep in x.rels:
        # optimization: retrieve early to avoid successive lookup
        lbl = ep.label
        id = ep.id
        props = x.variables.get(ep.iv)
        args = ep.args
        carg = ep.carg
        # scope labels (may be targets of arguments or hcons)
        g[lbl][id] = 'eq-scope'
        # predicate-argument structure
        s = predicate.normalize(ep.predicate)
        if carg is not None:
            s += f'({carg})'
        elif properties and props:
            proplist = []
            for prop in sorted(props, key=property_priority):
                val = props[prop]
                proplist.append(f'{prop.upper()}={val.lower()}')
            s += '{' + '|'.join(proplist) + '}'
        g[id][None] = s
        for role in args:
            if role != mrs.CONSTANT_ROLE:
                # there may be multiple roles (e.g., L-INDEX, L-HNDL, etc.)
                roles = g[id].get(args[role], '').split() + [role]
                g[id][args[role]] = ' '.join(sorted(roles))

    # hcons
    for hc in x.hcons:
        g[hc.hi][hc.lo] = hc.relation

    # icons
    for ic in x.icons:
        g[ic.left][ic.right] = ic.relation

    return g


def compare_bags(testbag: Iterable[mrs.MRS],
                 goldbag: Iterable[mrs.MRS],
                 properties: bool = True,
                 count_only: bool = True):
    """
    Compare two bags of MRS objects, returning a triple of
    (unique-in-test, shared, unique-in-gold).

    Args:
        testbag: An iterable of MRS objects to test
        goldbag: An iterable of MRS objects to compare against
        properties: if `True`, ensure variable properties are
            equal for mapped predications
        count_only: If `True`, the returned triple will only have the
            counts of each; if `False`, a list of MRS objects will be
            returned for each (using the ones from *testbag* for the
            shared set)
    Returns:
        A triple of (unique-in-test, shared, unique-in-gold), where
        each of the three items is an integer count if the
        *count_only* parameter is `True`, or a list of MRS objects
        otherwise.
    """
    gold_remaining = list(goldbag)
    test_unique = []
    shared = []
    for test in testbag:
        gold_match = None
        for gold in gold_remaining:
            if is_isomorphic(test, gold, properties=properties):
                gold_match = gold
                break
        if gold_match is not None:
            gold_remaining.remove(gold_match)
            shared.append(test)
        else:
            test_unique.append(test)
    if count_only:
        return (len(test_unique), len(shared), len(gold_remaining))
    else:
        return (test_unique, shared, gold_remaining)


def from_dmrs(d):
    """
    Create an MRS by converting from DMRS *d*.

    Args:
        d: the input DMRS
    Returns:
        MRS
    Raises:
        MRSError when conversion fails.
    """
    H = variable.HANDLE
    qeq = mrs.HCons.qeq
    vfac = variable.VariableFactory(starting_vid=0)
    top = vfac.new(H) if d.top is not None else None

    # do d.scopes() once to avoid potential errors if label generation
    # is ever non-deterministic
    _top, scopes = d.scopes()
    ns_args = d.arguments(types='xeipu')
    sc_args = d.scopal_arguments(scopes=scopes)

    id_to_lbl, id_to_iv = _dmrs_build_maps(d, scopes, vfac)
    # for index see https://github.com/delph-in/pydelphin/issues/214
    index = None if not d.index else id_to_iv[d.index]

    hcons = []
    if top is not None:
        hcons.append(qeq(top, _top))

    icons = None  # see https://github.com/delph-in/pydelphin/issues/220

    rels = []
    for node in d.nodes:
        id = node.id
        label = id_to_lbl[id]
        args = {mrs.INTRINSIC_ROLE: id_to_iv[id]}

        for role, tgt in ns_args[id]:
            args[role] = id_to_iv[tgt]

        for role, relation, tgt_label in sc_args[id]:
            if relation == scope.LHEQ:
                args[role] = tgt_label
            elif relation == scope.QEQ:
                hole = vfac.new(H)
                args[role] = hole
                hcons.append(qeq(hole, tgt_label))
            else:
                raise mrs.MRSError('DMRS-to-MRS: invalid scope constraint')

        if node.carg is not None:
            args[mrs.CONSTANT_ROLE] = node.carg

        if d.is_quantifier(id) and mrs.BODY_ROLE not in args:
            args[mrs.BODY_ROLE] = vfac.new(H)

        rels.append(
            mrs.EP(node.predicate,
                   label,
                   args=args,
                   lnk=node.lnk,
                   surface=node.surface,
                   base=node.base))

    return mrs.MRS(
        top=top,
        index=index,
        rels=rels,
        hcons=hcons,
        icons=icons,
        variables=vfac.store,
        lnk=d.lnk,
        surface=d.surface,
        identifier=d.identifier)


def _dmrs_build_maps(d, scopes, vfac):
    id_to_lbl = {}
    for label, nodes in scopes.items():
        vfac.index[variable.id(label)] = label  # prevent vid reuse
        id_to_lbl.update((node.id, label) for node in nodes)

    id_to_iv = {}
    for node, q in d.quantification_pairs():
        if node is not None:
            iv = vfac.new(node.type, node.properties)
            id_to_iv[node.id] = iv
            if q is not None:
                id_to_iv[q.id] = iv
        else:
            pass  # ignore unpaired quantifiers (ill-formed)

    return id_to_lbl, id_to_iv
