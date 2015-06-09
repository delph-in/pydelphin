
from collections import defaultdict
from itertools import permutations


def isomorphic2(a, b, check_varprops=True):
    """
    Two Xmrs objects are isomorphic if they have the same structure as
    determined by variable linkages between preds.
    """
    # first some quick checks
    if len(a.nodeids()) != len(b.nodeids()):
        return False
    if len(a.variables()) != len(b.variables()):
        return False

    # pre-populate varmap; first top variables
    varmap = {}
    for pair in [(a.top, b.top), (a.index, b.index), (a.xarg, b.xarg)]:
        if pair != (None, None):
            v1, v2 = pair
            if None in pair: return False
            if check_varprops and a.get_varprops(v1) != b.get_varprops(v2):
                return False
            varmap[v1] = v2

    # now go through preds in order: (#preds, #incoming-links)
    # this way, unique preds and ones with unique positions come first

    # But first we need to build a way to count preds
    a_preds = defaultdict(list)
    for ep in a.predications(): a_preds[ep[1].string].append(ep[0])
    b_preds = defaultdict(list)
    for ep in b.predications(): b_preds[ep[1].string].append(ep[0])

    # Pair up sets of nids with the same pred (fail early if counts differ)
    nidset_pairs = []
    for pred, a_nids in sorted(a_preds.items(), key=lambda x: len(x[1])):
        b_nids = b_preds[pred]
        if len(a_nids) != len(b_nids): return False
        nidset_pairs.append((a_nids, b_nids))

    print(nidset_pairs)
    try:
        varmaps = _isomorphic(a, b, nidset_pairs, varmap, check_varprops)
    except (KeyError, IndexError):
        return False

    return bool(varmaps)  # the existence of map means a mapping was found

        # if len(a_nids) == 1:
        #     a_ep = a_eps[a_nids[0]]; b_ep = b_eps[b_nids[0]]
        #     # labels
        #     a_lbl = a_ep[2]; b_lbl = b_ep[2]
        #     if a_lbl not in varmap or varmap[a_lbl] == b_lbl:
        #         varmap[a_lbl] = b_lbl
        #     # args
        #     b_args = b_ep[3]
        #     for rargname, a_val in a_ep[3].items():
        #         b_val = b_args.get(rargname)
        #         if a_val in a_vars and b_val in b_vars:
        #             if check_varprops and a_vars[a_val]['props'] !=
        #         elif a_val not in a_vars and b_val not in b_vars:
        #             if a_val != b_val: return False  # constants must be equal
        #         else:
        #             return False


def isomorphic(a, b, check_varprops=True):
    """
    Two Xmrs objects are isomorphic if they have the same structure as
    determined by variable linkages between preds.
    """
    # first some quick checks
    if len(a.nodeids()) != len(b.nodeids()):
        return False

    if len(a.variables()) != len(b.variables()):
        return False

    # pre-populate varmap; first top variables
    varmap = {}
    for pair in [(a.top, b.top), (a.index, b.index), (a.xarg, b.xarg)]:
        if pair != (None, None):
            v1, v2 = pair
            if None in pair: return False
            if check_varprops and a.get_varprops(v1) != b.get_varprops(v2):
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
    for var, vd in b._vars.items():
        if var not in tgtmapped:
            var_sig = _isomorphic_var_signature(vd, b, check_varprops)
            b_sigs[var_sig].append(var)


    # But first we need to build a way to count preds
    a_preds = defaultdict(list)
    for ep in a.predications(): a_preds[ep[1].string].append(ep[0])
    b_preds = defaultdict(list)
    for ep in b.predications(): b_preds[ep[1].string].append(ep[0])

    # Pair up sets of nids with the same pred (fail early if counts differ)
    nidset_pairs = []
    for pred, a_nids in sorted(a_preds.items(), key=lambda x: len(x[1])):
        b_nids = b_preds[pred]
        if len(a_nids) != len(b_nids): return False
        nidset_pairs.append((a_nids, b_nids))

    print(nidset_pairs)
    try:
        varmaps = _isomorphic(a, b, nidset_pairs, varmap, check_varprops)
    except (KeyError, IndexError):
        return False

    return bool(varmaps)  # the existence of map means a mapping was found

        # if len(a_nids) == 1:
        #     a_ep = a_eps[a_nids[0]]; b_ep = b_eps[b_nids[0]]
        #     # labels
        #     a_lbl = a_ep[2]; b_lbl = b_ep[2]
        #     if a_lbl not in varmap or varmap[a_lbl] == b_lbl:
        #         varmap[a_lbl] = b_lbl
        #     # args
        #     b_args = b_ep[3]
        #     for rargname, a_val in a_ep[3].items():
        #         b_val = b_args.get(rargname)
        #         if a_val in a_vars and b_val in b_vars:
        #             if check_varprops and a_vars[a_val]['props'] !=
        #         elif a_val not in a_vars and b_val not in b_vars:
        #             if a_val != b_val: return False  # constants must be equal
        #         else:
        #             return False


def _isomorphic(a, b, nidset_pairs, varmap, check_varprops):
    a_eps, a_vars = a._eps, a._vars
    b_eps, b_vars = b._eps, b._vars
    # for each nidset pair, find suitable matches; if more than one, try each
    a_nids, b_nids = nidset_pairs[0]
    nidset_pairs = nidset_pairs[1:]
    a_epmap = {nid: a_eps[nid] for nid in a_nids}
    b_epmap = {nid: b_eps[nid] for nid in b_nids}
    perms = [list(zip(a_perm, b_nids)) for a_perm in permutations(a_nids)]

    varmaps = []
    for perm in perms:
        for a_nid, b_nid in perm:
            a_ep, b_ep = a_epmap[a_nid], b_epmap[b_nid]
            a_lbl b_lbl = a_ep[2], b_ep[2]
            if

    # tgtmapped = set()
    # a_sigs = defaultdict(list)
    # for var, vd in a_vars.items():
    #     if var not in varmap:
    #         var_sig = _isomorphic_var_signature(vd, a, check_varprops, semi)
    #         a_sigs[var_sig].append(var)
    # b_sigs = defaultdict(list)
    # for var, vd in b_vars.items():
    #     if var not in tgtmapped:
    #         var_sig = _isomorphic_var_signature(vd, b, check_varprops, semi)
    #         b_sigs[var_sig].append(var)
    # print(varmap)
    # for sig, var in a_sigs.items():
    #     print(sig, var)
    # candidates = []
    # for sig, a_varlist in a_sigs.items():
    #     b_varlist = b_sigs[sig]
    #     a_varlist_len = len(a_varlist)
    #     if a_varlist_len != len(b_varlist):
    #         return False
    #     # if only one with signature; map it if no conflict
    #     if a_varlist_len == 1:
    #         a_var = a_varlist[0]; b_var = b_varlist[0]
    #         if a_var not in varmap or varmap[a_var] == b_var:
    #             varmap[a_var] = b_var
    #     else:
    #         candidates.append((a_varlist, b_ varlist))

    # print(candidates)
    # # now do a recursive search
    # varmaps = _isomorphic_recurse(a, b, varmap, candidates)
    # for vmap in varmaps:
    #     print([(x, y) for x, y in vmap.items() if x != y])
    # return varmaps


# def _isomorphic_map_vars(varmap, a_var, b_var, a_vars, b_vars):



def _isomorphic_var_signature(vd, xmrs, check_varprops):
    sig = []
    if check_varprops:
        props = vd['props']
        sig.extend('%s=%s' % (k, v) for k, v in props.items())

    if 'hcons' in vd: sig.append('%s>' % vd['hcons'][1])
    if 'icons' in vd: sig.append('%s>' % vd['icons'][1])

    for role, refval in vd['refs'].items():
        if role in ('hcons', 'icons'):
            for c in refval:
                sig.append('<%s' % c[1])  # *cons relation only
        else:
            for nid in refval:
                pred = xmrs.get_pred(nid)
                sig.append('%s:%s' % (pred.string, role))

    return ' '.join(sorted(sig))


def _isomorphic_recurse(a, b, varmap, candidates):
    if not candidates:
        return [varmap]
    a_candidates, b_candidates = candidates.pop()

    varmaps = []
    for a_perms in permutations(a_candidates):
        newmap = varmap.copy()
        newmap.update(zip(a_perms, b_candidates))
        varmaps.extend(_isomorphic_recurse(a, b, newmap, candidates))
    return varmaps


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
