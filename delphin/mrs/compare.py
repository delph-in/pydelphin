
import networkx as nx


def xmrs_node_match(ndata1, ndata2):
    carg1 = carg2 = None
    if isinstance(ndata1['node_label'], str):
        carg1 = ndata1['node_label']
    if isinstance(ndata2['node_label'], str):
        carg2 = ndata2['node_label']
    matching = True
    if 'pred' in ndata1 and 'pred' in ndata2:
        matching = (
            ndata1['pred'] == ndata2['pred'] and
            getattr(ndata1['iv'], 'properties', None) ==
            getattr(ndata2['iv'], 'properties', None)
        )
    elif 'hcons' in ndata1 and 'hcons' in ndata2:
        matching = ndata1['hcons'].relation == ndata2['hcons'].relation
    elif 'icons' in ndata2 and 'icons' in ndata2:
        matching = ndata1['icons'].relation == ndata2['icons'].relation
    else:
        matching = set(ndata1.keys()) == set(ndata2.keys())
    return matching


def xmrs_edge_match(edata1, edata2):
    matching = False if (
        edata1.get('iv') != edata2.get('iv') or
        edata1.get('bv') != edata2.get('bv') or
        edata1.get('rargname') != edata2.get('rargname') or
        edata1.get('relation') != edata2.get('relation')
        ) else True
    return matching


def isomorphic(xmrs1, xmrs2):
    g1 = nx.convert_node_labels_to_integers(
        xmrs1._graph, label_attribute='node_label'
    )
    g2 = nx.convert_node_labels_to_integers(
        xmrs2._graph, label_attribute='node_label'
    )
    return nx.is_isomorphic(
        g1,
        g2,
        node_match=xmrs_node_match,
        edge_match=xmrs_edge_match
    )


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
