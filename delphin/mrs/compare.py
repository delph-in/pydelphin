
from collections import defaultdict
from itertools import permutations, groupby, chain
from functools import partial

import networkx as nx

from delphin.mrs.components import var_id, var_sort
from delphin.mrs.config import CONSTARG_ROLE, IVARG_ROLE

# NOTES:
#  the somewhat naive implementations in _node_isomorphic and
#  _var_isomorphic have terrible runtimes for the pathological case,
#  and I didn't finish the Turbo_ISO implementation before I had to
#  move on, so I'm conceding defeat for the time being and using
#  networkx just for isomorphism (so I build a nx DiGraph here, then
#  throw it away when i'm done).

def isomorphic(q, g, check_varprops=True):
    """
    Return `True` if Xmrs objects *q* and *g* are isomorphic.

    Isomorphicity compares the predicates of an Xmrs, the variable
    properties of their predications (if `check_varprops=True`),
    constant arguments, and the argument structure between
    predications. Node IDs and Lnk values are ignored.

    Args:
        q: the left Xmrs to compare
        g: the right Xmrs to compare
        check_varprops: if `True`, make sure variable properties are
            equal for mapped predications
    """

    qdg = _make_digraph(q, check_varprops)
    gdg = _make_digraph(g, check_varprops)
    def nem(qd, gd):  # node-edge-match
        return qd.get('sig') == gd.get('sig')
    return nx.is_isomorphic(qdg, gdg, node_match=nem, edge_match=nem)

def _make_digraph(x, check_varprops):
    dg = nx.DiGraph()
    for ep in x.eps():
        nid, pred, args = ep[0], ep[1], ep[3]
        if CONSTARG_ROLE in args:
            s = '{}({})'.format(pred.short_form(), args[CONSTARG_ROLE])
        else:
            s = pred.short_form()
        dg.add_node(nid, sig=s)
        dg.add_edges_from((nid, var_id(val)) for role, val in args.items()
                          if role != CONSTARG_ROLE)
    for var, vd in x._vars.items():
        aspects = []
        if check_varprops:
            aspects.extend('%s=%s' % (p,v) for p,v in vd['props'])
        aspects.extend('%s:%s' % (dg.node[tgt]['sig'], ref)
                       for ref, tgts in vd['refs'].items()
                       for tgt in tgts if tgt in x._eps)
        s = '{}|{}'.format(var_sort(var), '|'.join(sorted(aspects)))
        dg.add_node(var_id(var), sig=s)
    dg.add_edges_from((var_id(hi), var_id(lo), {'sig':reln})
                      for hi, reln, lo in x.hcons())
    return dg

def _turbo_isomorphic(q, g, check_varprops=True):
    """
    Query Xmrs q is isomorphic to given Xmrs g if there exists an
    isomorphism (bijection of eps and vars) from q to g.
    """
    # first some quick checks
    if len(q.eps()) != len(g.eps()): return False
    if len(q.variables()) != len(g.variables()): return False
    #if len(a.hcons()) != len(b.hcons()): return False
    try:
        next(_isomorphisms(q, g, check_varprops=check_varprops))
        return True
    except StopIteration:
        return False


def _isomorphisms(q, g, check_varprops=True):
    """
    Inspired by Turbo_ISO: http://dl.acm.org/citation.cfm?id=2465300
    """
    # convert MRSs to be more graph-like, and add some indices
    qig = _IsoGraph(q, varprops=check_varprops)  # qig = q isograph
    gig = _IsoGraph(g, varprops=check_varprops)  # gig = q isograph
    # qsigs, qsigidx = _isomorphism_sigs(q, check_varprops)
    # gsigs, gsigidx = _isomorphism_sigs(g, check_varprops)
    # (it would be nice to not have to do this... maybe later)
    # qadj = _isomorphism_adj(q, qsigidx)
    # gadj = _isomorphism_adj(g, gsigidx)
    # the degree of each node is useful (but can it be combined with adj?)
    # qdeg = _isomorphism_deg(qadj)
    # gdeg = _isomorphism_deg(gadj)

    u_s = _isomorphism_choose_start_q_vertex(qig, gig, subgraph=False)
    q_ = _isomorphism_rewrite_to_NECtree(u_s, qig)
    for v_s in gsigs.get(qsigidx[u_s], []):
        cr = _isomorphism_explore_CR(q_, {v_s}, qig, gig)
        if cr is None:
            continue
        order = _isomorphism_determine_matching_order(q_, cr)
        update_state(M,F,{u_s}, {v_s})
        subraph_search(q, q_, g, order, 1)  # 1="the first query vertex to match"
        restore_state(M, F, {u_s}, {v_s})


class _IsoGraph(object):
    def __init__(self, x, varprops=True):
        self.sig = sig = defaultdict(list)
        self.sigidx = sigidx = {}
        self.adj = adj = defaultdict(lambda: defaultdict(list))
        self.deg = deg = {}

        # generate signatures (node labels)
        for ep in x.eps():
            # ep_sig = 'pred|{CARG}'
            nid, args = ep[0], ep[3]
            if CONSTARG_ROLE in args:
                s = '{}({})'.format(ep[1].string, args[CONSTARG_ROLE])
            else:
                s = ep[1].string
            sig[s].append(nid)
            sigidx[nid] = s
        for var, vd in x._vars.items():
            # var_sig = 'varsort|{VARPROPS_AND_REFERENCES}'
            aspects = ['%s=%s' % (p,v) for p,v in vd['props']] if varprops else []
            aspects.extend(['%s:%s' % (sigidx[tgt], ref)
                            for ref, tgts in vd['refs'].items()
                            for tgt in tgts if tgt in x._eps])
            s = '{}|{}'.format(var_sort(var), '|'.join(sorted(aspects)))
            sig[s].append(var)
            sigidx[var] = s

        # generate adjacency dicts (slightly optimized)
        for ep in x.eps():
            nid, lbl, args, s = ep[0], ep[2], ep[3], sigidx[nid]
            adj[nid][sigidx[lbl]].append((lbl, 'LBL', 1))
            adj[lbl][s].append((nid, 'LBL', 1))
            for role, val in args.items():
                if role == CONSTARG_ROLE: continue
                adj[nid][sigidx[val]].append((val, role, 1))
                adj[val][s].append((nid, role, 1 if role == IVARG_ROLE else 0))
        for hc in x._hcons.values():
            hi, reln, lo = hc
            adj[hi][sigidx[lo]].append((lo, reln, 1))
            adj[lo][sigidx[hi]].append((hi, reln, 0))

        # generate a degree mapping for each node
        for id_, ad in adj.items():  # ad = adj dict mapping sig to adjacents
            # al = adjacent list; d is direction (forward=1, backward=0)
            deg[id_] = sum(d for al in ad.values() for _, _, d in al)


def _isomorphism_choose_start_q_vertex(qig, gig, subgraph):
    k = 3  # max candidate start nodes; according to Turbo_ISO paper
    qsigidx, qadj, qdeg = q.sigidx, q.adj, q.deg
    gsig, gadj, gdeg = g.sig, g.adj, g.deg
    # rank query vertices by freq(g, L(u)) / deg(u)
    rank = {u: float(len(gsig[s]))/qdeg[u] for u, s in qsigidx.items()}
    q_s, q_s_num_candidates = None, 0
    for u, rank in sorted(rank.items(), key=lambda x: x[1])[:k]:
        usig, udeg = qsigidx[u], qdeg[u]
        ulf = [(sig_, len(adjs)) for sig_, adjs in qadj.get(u, {}).items()]
        # cdf is the candidate degree filter
        # nlf is the neighborhood label (signature) frequency filter
        if subgraph:
            cdf = lambda v: udeg <= gdeg.get(v, 0)
            nlf = lambda v: all(n <= len(gadj[v].get(s, [])) for s, n in ulf)
            vs = list(filter(nlf, filter(cdf, gsig.get(usig, []))))
        else:
            cdf = lambda v: udeg == gdeg.get(v, 0)
            nlf = lambda v: all(n == len(gadj[v].get(s, [])) for s, n in ulf)
            vs = list(filter(nlf, filter(cdf, gsig.get(usig, []))))
        # find q_s with minimum number of candidate regions
        if q_s is None or len(vs) < q_s_num_candidates:
            q_s = u
            q_s_num_candidates = len(vs)
    return q_s


def _isomorphism_rewrite_to_NECtree(q_s, qgraph):
    """
    Neighborhood Equivalence Class tree (see Turbo_ISO paper)
    """
    qadj = qgraph.adj
    adjsets = lambda x: set(chain.from_iterable(qadj[x].values()))
    t = ([q_s], [])  # (NEC_set, children)
    visited = {q_s}
    vcur, vnext = [t], []
    while vcur:
        for (nec, children) in vcur:
            c = defaultdict(list)
            for u in nec:
                for sig, adjlist in qadj[u].items():
                    c[sig].extend(x for x, _, _ in adjlist if x not in visited)
            for sig, c_adjlist in c.items():
                visited.update(c_adjlist)
                # these are already grouped by label; now group by adjacents
                for key, grp in groupby(c_adjlist, key=adjsets):
                    grp = list(grp)
                    if len(grp) > 1:
                        children.append((list(grp), []))
                    else:
                        # NOTE: the paper says to look for mergeable things,
                        # but I don't know what else to merge by.
                        children.append((list(grp), []))
            vnext.extend(children)
        vcur, vnext = vnext, []
    return t


def _isomorphism_explore_CR(q_, v_m, qig, gig):
    nec, children = q_
    gadj, gdeg = gig.adj, gig.deg
    u = q_[0][0]  # q_[0][0] is q_.NEC[1] (1-based index)
    ulf = [(s, len(adjs)) for s, adjs in qig.adj.get(u, {}).items()]
    nlf = lambda v: all(n <= len(gadj[v].get(s, [])) for s, n in ulf)
    for v in v_m:
        if q_deg > gig.deg[v] or not nlf(v):
            continue


def _node_isomorphic(a, b, check_varprops=True):
    """
    Two Xmrs objects are isomorphic if they have the same structure as
    determined by variable linkages between preds.
    """
    # first some quick checks
    a_var_refs = sorted(len(vd['refs']) for vd in a._vars.values())
    b_var_refs = sorted(len(vd['refs']) for vd in b._vars.values())
    if a_var_refs != b_var_refs:
        return False
    print()

    # these signature: [node] indices are meant to avoid unnecessary
    # comparisons; they also take care of "semantic feasibility"
    # constraints (comparing node values and properties). All that's
    # left is the "syntactic feasibility", or node-edge shapes.
    # nodedicts are {sig: [(id, edges), ...], ...}
    a_nd = _node_isomorphic_build_nodedict(a, check_varprops)
    #print('a', a_nd)
    b_nd = _node_isomorphic_build_nodedict(b, check_varprops)
    #print('b', b_nd)
    #return

    a_sigs = {}  # for node -> sig mapping
    # don't recurse when things are unique
    agenda = []
    isomap = {}
    for sig, a_pairs in sorted(a_nd.items(), key=lambda x: len(x[1])):
        b_pairs = b_nd.get(sig, [])
        if len(a_pairs) != len(b_pairs):
            return False
        if len(a_pairs) == 1:
            a_, a_edges = a_pairs[0]
            b_, b_edges = b_pairs[0]
            if len(a_edges) != len(b_edges):
                return False
            a_sigs[a_] = sig
            isomap[a_] = b_
            for edge, a_tgt in a_edges.items():
                if edge not in b_edges:
                    return False
                isomap[a_tgt] = b_edges[edge]
        else:
            for a_, ed in a_pairs:
                a_sigs[a_] = sig
                agenda.append((a_, sig, ed))
    #print(agenda)
    #return
    isomaps = _node_isomorphic(agenda, a_sigs, b_nd, isomap, {})
    # for sig, a_candidates in sorted(a_nodes.items(), key=lambda x: len(x[1])):
    #     b_candidates = b_nodes.get(sig, [])
    #     if len(a_candidates) != len(b_candidates): return False
    #     candidates.append((a_candidates, b_candidates))
    #
    # nodemaps = _isomorphic(a, b, candidates, {})
    try:
        next(isomaps)
        return True
    except StopIteration:
        return False

def _node_isomorphic_build_nodedict(x, varprops):
    # nodes are eps and vars:
    #   preds: {ep_sig: (nid, {arg_or_lbl: tgt})}
    #       ep_sig = 'pred|{CARG}'
    #   vars: {var_sig: (var, {ref_name: tgt})}
    #       var_sig = 'varsort|{VARPROPS}'
    nd = defaultdict(list)
    for ep in x.eps():
        ep_sig = '{}|{}'.format(ep[1].string, ep[3].get(CONSTARG_ROLE))
        ep_out = {'LBL': ep[2]}
        for rargname, val in ep[3].items():
            if rargname == CONSTARG_ROLE: continue
            ep_out[rargname] = val
        nd[ep_sig].append((ep[0], ep_out))
    for var, vd in x._vars.items():
        if varprops:
            vps = '|'.join('%s=%s' % (p, v) for p, v in vd['props'])
        else:
            vps = ''
        refs = '|'.join(
            '%s:%s' % (x._eps[tgt][1].string, ref)
            for ref, tgts in vd['refs'].items()
            for tgt in tgts if tgt in x._eps
        )
        var_sig = '{}|{}|{}'.format(var_sort(var), vps, refs)
        var_tgts = {}
        if var in x._hcons:
            hc = x._hcons[var]
            var_tgts[hc[1]] = hc[2]
        nd[var_sig].append((var, var_tgts))
    return nd

def _node_isomorphic(agenda, a_sigs, b_nd, isomap, failed):
    agendum = None
    for i, agendum in enumerate(agenda):
        # agendum is (node, signature, edgedict)
        if agendum[0] not in isomap or agendum[2]:
            break
        else:
            agendum = None
    if agendum is None:  # nothing left to do; success
        yield isomap
        return
    a, sig, a_edges = agendum
    agenda = agenda[i+1:]  # remove all skipped agenda
    # print('agenda', agenda)
    # print('isomap', isomap)
    # print('failed', failed)
    # print('a_sigs', a_sigs)
    # print('\t', a)

    b_mapped = set(isomap.values())
    bs = [b for b in b_nd[sig] if b[0] not in b_mapped]
    if any(failed.get((a, b[0])) for b in bs):
        return
    # print('bs', bs)
    for b, b_edges in bs:
        if len(a_edges) != len(b_edges):
            failed[(a, b)] = True; continue
        newmaps = [(a, b)]
        for edge, a_ in a_edges.items():
            if a_ in isomap:
                continue
            a_sig = a_sigs[a_]
            b_avail = set(b_data[0] for b_data in b_nd[a_sig])
            b_ = b_edges.get(edge)
            if b_ is None or b_ not in b_avail:
                failed[(a, b)] = True; newmaps = None; break
            newmaps.append((a_, b_))
        if newmaps:
            iso = isomap.copy()
            iso.update(newmaps)
            for iso_ in _isomorphic(agenda, a_sigs, b_nd, iso, failed):
                yield iso_


def _var_isomorphic(a, b, check_varprops=True):
    """
    Two Xmrs objects are isomorphic if they have the same structure as
    determined by variable linkages between preds.
    """
    # first some quick checks
    if len(a.eps()) != len(b.eps()): return False
    if len(a.variables()) != len(b.variables()): return False
    #if len(a.hcons()) != len(b.hcons()): return False

    # pre-populate varmap; first top variables
    varmap = {}
    for pair in [(a.top, b.top), (a.index, b.index), (a.xarg, b.xarg)]:
        if pair != (None, None):
            v1, v2 = pair
            if None in pair:
                return False
            if check_varprops and a.properties(v1) != b.properties(v2):
                return False
            varmap[v1] = v2

    # find permutations of variables, grouped by those that share the
    # same signature.

    a_sigs = defaultdict(list)
    for var, vd in a._vars.items():
        if var not in varmap:
            var_sig = _isomorphic_var_signature(vd, a, check_varprops)
            a_sigs[var_sig].append(var)
    b_sigs = defaultdict(list)
    tgtmapped = set(varmap.values())
    for var, vd in b._vars.items():
        if var not in tgtmapped:
            var_sig = _isomorphic_var_signature(vd, b, check_varprops)
            b_sigs[var_sig].append(var)

    candidates = []
    for sig, a_vars in sorted(a_sigs.items(), key=lambda x: len(x[1])):
        b_vars = b_sigs.get(sig, [])
        if len(a_vars) != len(b_vars):
            return False
        print(sig, a_vars, b_vars)
        candidates.append((a_vars, b_vars))

    varmaps = _var_isomorphic(a, b, candidates, varmap)

    # double check HCONS (it's hard to do with var signatures)
    for vm in varmaps:
        if all(vm[lo] == b._hcons.get(vm[hi], (None, None, None))[2]
               for hi, _, lo in a.hcons()):
            return True
    return False


def _var_isomorphic(a, b, candidates, varmap):
    if not candidates:
        yield varmap
        return
    a_vars, b_vars = candidates[0]
    candidates = candidates[1:]  # don't pop() because it changes the original
    perms = [list(zip(a_perm, b_vars)) for a_perm in permutations(a_vars)]
    for perm in perms:
        vm = varmap.copy()
        mv = dict((v, k) for k, v in varmap.items())  # mv is vm reversed
        for a_var, b_var in perm:
            if vm.get(a_var) != mv.get(b_var):
                vm = None; break
            else:
                vm[a_var] = b_var
        if not vm:
            continue
        for vm_ in _var_isomorphic(a, b, candidates, vm):
            yield vm_


def _isomorphic_var_signature(vd, xmrs, check_varprops):
    sig = []
    if check_varprops:
        props = vd['props']
        sig.extend('%s=%s' % (k, v) for k, v in props)

    if 'hcons' in vd: sig.append('%s>' % vd['hcons'][1])
    if 'icons' in vd: sig.append('%s>' % vd['icons'][1])

    for role, refval in vd['refs'].items():
        if role in ('hcons', 'icons'):
            for c in refval:
                sig.append('<%s' % c[1])  # *cons relation only
        else:
            for nid in refval:
                pred = xmrs.pred(nid)
                sig.append('%s:%s' % (pred.short_form(), role))

    return ' '.join(sorted(sig))


def compare_bags(testbag, goldbag, count_only=True):
    """
    Compare two bags of Xmrs objects, returning a triple of
    (unique in test, shared, unique in gold).

    Args:
        testbag: An iterable of Xmrs objects to test.
        goldbag: An iterable of Xmrs objects to compare against.
        count_only: If True, the returned triple will only have the
            counts of each; if False, a list of Xmrs objects will be
            returned for each (using the ones from testbag for the
            shared set)
    Returns:
        A triple of (unique in test, shared, unique in gold), where
        each of the three items is an integer count if the count_only
        parameter is True, or a list of Xmrs objects otherwise.
    """
    gold_remaining = list(goldbag)
    test_unique = []
    shared = []
    for test in testbag:
        gold_match = None
        for gold in gold_remaining:
            if isomorphic(test, gold):
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
