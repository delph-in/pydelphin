
def contiguous_semantic_constituents(x):
    """
    Yield semantic constituents whose preds come from contiguous words
    in the source sentence (judged by the CFROM and CTO values).
    """
    from delphin.mrs.components import elementarypredications
    import delphin.mrs.path as mp
    epmap = {ep.nodeid: ep for ep in elementarypredications(x)}
    seen = set()
    for p in mp.explore(x, method='headed', flags=mp.DEFAULT|mp.UND|mp.B):
        pnids = tuple(sorted(mp.get_nodeids(p)))
        if 0 in pnids or pnids in seen:
            continue  # ignore paths with TOP or already yielded paths
        eps = [epmap[nid] for nid in pnids]
        cfrom = min(ep.cfrom for ep in eps)
        cto = max(ep.cto for ep in eps)
        span = sorted(
            (e for e in epmap.values() if e.cfrom >= cfrom and e.cto <= cto),
            key=lambda e: e.nodeid
        )
        if eps == span:
            seen.add(pnids)
            yield pnids
