
from __future__ import print_function

from itertools import count

from delphin.util import stringtypes
from delphin.mrs.xmrs import Xmrs, _bfs
from delphin.mrs.components import (
    var_sort,
    Lnk,
    Pred,
    Node,
    nodes as make_nodes
)
from delphin.mrs.query import find_argument_target
from delphin.mrs.util import rargname_sortkey
from delphin.mrs.config import CVARSORT
from delphin.lib.pegre import (
    literal as lit,
    regex,
    nonterminal as nt,
    sequence as seq,
    zero_or_more,
    optional as opt,
    delimited,
    bounded,
    Ignore,
    Peg,
    Spacing,
    Integer,
    DQString
)

class Eds(object):
    def __init__(self, top=None, nodes=None, edges=None):
        if nodes is None: nodes = []
        if edges is None: edges = []

        self.top = top
        self._nodeids = [node.nodeid for node in nodes]
        self._nodes = {node.nodeid: node for node in nodes}
        self._edges = {node.nodeid: {} for node in nodes}
        for start, rargname, end in edges:
            self._edges[start][rargname] = end

    @classmethod
    def from_xmrs(cls, xmrs):
        eps = xmrs.eps()
        deps = _find_dependencies(xmrs, eps)
        ids = _unique_ids(eps, deps)
        root = _find_root(xmrs)
        if root is not None:
            root = ids[root]
        nodes = [Node(ids[n.nodeid], *n[1:]) for n in make_nodes(xmrs)]
        edges = [(ids[a], rarg, ids[b]) for a, deplist in deps.items()
                                        for rarg, b in deplist]
        return cls(top=root, nodes=nodes, edges=edges)

    def __eq__(self, other):
        if not isinstance(other, Eds):
            return False
        return (
            self.top == other.top and
            all(a == b for a, b in zip(self.nodes(), other.nodes())) and
            self._edges == other._edges
        )

    def nodeids(self):
        return list(self._nodeids)

    def node(self, nodeid):
        return self._nodes[nodeid]

    def nodes(self):
        getnode = self._nodes.__getitem__
        return [getnode(nid) for nid in self._nodeids]

    def edges(self, nodeid):
        return dict(self._edges.get(nodeid, []))

    def to_dict(self, properties=True):
        nodes = {}
        for node in self.nodes():
            nd = {
                'label': node.pred.short_form(),
                'edges': self.edges(node.nodeid)
            }
            if node.lnk is not None:
                nd['lnk'] = {'from': node.cfrom, 'to': node.cto}
            if properties:
                if node.cvarsort is not None:
                    nd['type'] = node.cvarsort
                props = node.properties
                if props:
                    nd['properties'] = props
            if node.carg is not None:
                nd['carg'] = node.carg
            nodes[node.nodeid] = nd
        return {'top': self.top, 'nodes': nodes}

    @classmethod
    def from_dict(cls, d):
        makepred, charspan = Pred.string_or_grammar_pred, Lnk.charspan
        top = d.get('top')
        nodes, edges = [], []
        for nid, node in d.get('nodes', {}).items():
            props = node.get('properties', {})
            if 'type' in node:
                props[CVARSORT] = node['type']
            if not props:
                props = None
            lnk = None
            if 'lnk' in node:
                lnk = charspan(node['lnk']['from'], node['lnk']['to'])
            nodes.append(
                Node(
                    nodeid=nid,
                    pred=makepred(node['label']),
                    sortinfo=props,
                    lnk=lnk,
                    carg=node.get('carg')
                )
            )
            edges.extend(
                (nid, rargname, tgtnid)
                for rargname, tgtnid in node.get('edges', {}).items()
            )
        nodes.sort(key=lambda n: (n.cfrom, -n.cto))
        return cls(top, nodes=nodes, edges=edges)

    def to_triples(self, short_pred=True, properties=True):
        node_triples, edge_triples = [], []
        # sort nodeids just so top var is first
        nodes = sorted(self.nodes(), key=lambda n: n.nodeid != self.top)
        for node in nodes:
            nid = node.nodeid
            pred = node.pred.short_form() if short_pred else node.pred.string
            node_triples.append((nid, 'predicate', pred))
            if node.lnk:
                node_triples.append((nid, 'lnk', '"{}"'.format(str(node.lnk))))
            if node.carg:
                node_triples.append((nid, 'carg', '"{}"'.format(node.carg)))
            if properties:
                if node.cvarsort is not None:
                    node_triples.append((nid, 'type', node.cvarsort))
                props = node.properties
                node_triples.extend((nid, p, v) for p, v in props.items())
            edge_triples.extend(
                (nid, rargname, tgt)
                for rargname, tgt in sorted(
                    self.edges(nid).items(),
                    key=lambda x: rargname_sortkey(x[0])
                )
            )
        return node_triples + edge_triples

    @classmethod
    def from_triples(cls, triples):
        lnk, surface, identifier = None, None, None
        nids, nd, edges = [], {}, []
        for src, rel, tgt in triples:
            if src not in nd:
                nids.append(src)
                nd[src] = {'pred': None, 'lnk': None, 'carg': None, 'si': []}
            if rel == 'predicate':
                nd[src]['pred'] = Pred.string_or_grammar_pred(tgt)
            elif rel == 'lnk':
                cfrom, cto = tgt.strip('"<>').split(':')
                nd[src]['lnk'] = Lnk.charspan(int(cfrom), int(cto))
            elif rel == 'carg':
                if (tgt[0], tgt[-1]) == ('"', '"'):
                    tgt = tgt[1:-1]
                nd[src]['carg'] = tgt
            elif rel == 'type':
                nd[src]['si'].append((CVARSORT, tgt))
            elif rel.islower():
                nd[src]['si'].append((rel, tgt))
            else:
                edges.append((src, rel, tgt))
        nodes = [
            Node(
                nodeid=nid,
                pred=nd[nid]['pred'],
                sortinfo=nd[nid]['si'],
                lnk=nd[nid]['lnk'],
                carg=nd[nid]['carg']
            ) for nid in nids
        ]
        top = nids[0] if nids else None
        return cls(top=top, nodes=nodes, edges=edges)


def _find_dependencies(m, eps):
    deps = {}
    for ep in eps:
        nid = ep.nodeid
        if ep.is_quantifier():
            deps[nid] = [('BV', m.nodeid(ep.intrinsic_variable))]
        else:
            epdeps = []
            args = m.outgoing_args(nid)
            for rargname, val in args.items():
                tgtnid = find_argument_target(m, nid, rargname)
                epdeps.append((rargname, tgtnid))
            deps[nid] = epdeps
    return deps

def _unique_ids(eps, deps):
    # deps can be used to single out ep from set sharing ARG0s
    new_ids = ('_{}'.format(i) for i in count(start=1))
    ids = {}
    used = {}
    for ep in eps:
        nid = ep.nodeid
        iv = ep.intrinsic_variable
        if iv is None or ep.is_quantifier():
            iv = next(new_ids)
        ids[nid] = iv
        used.setdefault(iv, set()).add(nid)
    # give new ids when there's duplicates (use deps to select winner)
    for _id, nids in used.items():
        if len(nids) > 1:
            nids = sorted(
                nids,
                key=lambda n: any(d in nids for _, d in deps.get(n, []))
            )
            for nid in nids[1:]:
                ids[nid] = next(new_ids)
    return ids

def _find_root(m):
    try:
        top_hcons = m.hcon(m.top)
        return m.labelset_heads(top_hcons.lo)[0]
    except (KeyError, StopIteration):
        # try to find top?
        return None


## Serialization

def load(fh, single=False):
    if isinstance(fh, stringtypes):
        s = open(fh, 'r').read()
    else:
        s = fh.read()
    return loads(s, single=single)

def loads(s, single=False):
    es = deserialize(s)
    if single:
        return next(es)
    return es

def dump(fh, ms, single=False, properties=False, pretty_print=True, **kwargs):
    print(dumps(ms,
                single=single,
                properties=properties,
                pretty_print=pretty_print,
                **kwargs),
          file=fh)

def dumps(ms, single=False, properties=False, pretty_print=True, **kwargs):
    if not pretty_print and kwargs.get('indent'):
        pretty_print = True
    if single:
        ms = [ms]
    return serialize(
        ms,
        properties=properties,
        pretty_print=pretty_print,
        **kwargs
    )

def load_one(fh, **kwargs): return load(fh, single=True, **kwargs)
def loads_one(s, **kwargs): return loads(s, single=True, **kwargs)
def dump_one(fh, m, **kwargs): dump(fh, m, single=True, **kwargs)
def dumps_one(m, **kwargs): return dumps(m, single=True, **kwargs)


def _make_eds(d):
    top, data = d
    nodes, edges = [], []
    for node, _edges in data:
        nodes.append(node)
        edges.extend(_edges)
    return Eds(top=top, nodes=nodes, edges=edges)

def _make_nodedata(d):
    nid = d[0]
    node = Node(nid, pred=d[1], sortinfo=d[4], lnk=d[2], carg=d[3])
    edges = [(nid, rarg, tgt) for rarg, tgt in d[5]]
    return (node, edges)

_COLON   = regex(r'\s*:\s*', value=Ignore)
_COMMA   = regex(r',\s*')
_SPACES  = regex(r'\s+', value=Ignore)
_SYMBOL  = regex(r'[-+\w]+')
_PRED    = regex(r'((?!<-?\d|\("|\{|\[)\w)+',
                 value=Pred.string_or_grammar_pred)
_EDS     = nt('EDS', value=_make_eds)
_TOP     = opt(nt('TOP'), default=None)
_TOPID   = opt(_SYMBOL, default=None)
_FLAG    = opt(regex(r'\s*\(fragmented\)', value=Ignore))
_NODE    = nt('NODE', value=_make_nodedata)
_DSCN    = opt(lit('|', value=Ignore))
_LNK     = opt(nt('LNK', value=lambda d: Lnk.charspan(*d)), default=None)
_CARG    = opt(nt('CARG'), default=None)
_PROPS   = opt(nt('PROPS', value=lambda d: d[0] + d[1]), default=None)
_EDGES   = nt('EDGES')
_TYPE    = opt(_SYMBOL, value=lambda i: [(CVARSORT, i)], default=[])
_AVLIST  = nt('AVLIST')
_ATTRVAL = nt('ATTRVAL')

_eds_parser = Peg(
    grammar=dict(
        start=delimited(_EDS, Spacing),
        EDS=bounded(regex(r'\{\s*'), seq(_TOP, nt('NODES')), regex(r'\s*\}')),
        TOP=seq(_TOPID, _COLON, _FLAG, Spacing, value=lambda d: d[0]),
        NODES=delimited(_NODE, Spacing),
        NODE=seq(_DSCN, _SYMBOL, _COLON, _PRED, _LNK, _CARG, _PROPS, _EDGES),
        LNK=bounded(lit('<'), seq(Integer, _COLON, Integer), lit('>')),
        CARG=bounded(lit('('), DQString, lit(')')),
        PROPS=bounded(lit('{'), seq(_TYPE, _SPACES, _AVLIST), lit('}')),
        EDGES=bounded(lit('['), _AVLIST, lit(']')),
        AVLIST=delimited(_ATTRVAL, _COMMA),
        ATTRVAL=seq(_SYMBOL, _SPACES, _SYMBOL)
    )
)

def deserialize(s):
    for e in _eds_parser.parse(s).data:
        yield e

eds = '{{{top}{flag}{delim}{ed_list}{enddelim}}}'
ed =  '{membership}{id}:{pred}{lnk}{carg}{props}[{dep_list}]'
carg = '("{constant}")'
proplist = '{{{varsort}{proplist}}}'
dep = '{argname} {value}'

def serialize(ms, properties=False, pretty_print=True, **kwargs):
    delim = '\n' if pretty_print else ' '
    return delim.join(
        _serialize_eds(
            m,
            properties=properties,
            pretty_print=pretty_print,
            **kwargs
        )
        for m in ms
    )

def _serialize_eds(e, properties=False, pretty_print=True, **kwargs):
    if not isinstance(e, Eds):
        e = Eds.from_xmrs(e)
    # do something predictable for empty EDS
    if len(e.nodeids()) == 0:
        return '{:\n}' if pretty_print else '{:}'

    # determine if graph is connected
    g = {n: set() for n in e.nodeids()}
    for n in e.nodeids():
        for rargname, tgt in e.edges(n).items():
            g[n].add(tgt)
            g[tgt].add(n)
    nidgrp = _bfs(g, start=e.top)

    delim = '\n' if pretty_print else ' '
    connected = ' ' if pretty_print else ''

    return eds.format(
        top=e.top + ':' if e.top is not None else ':',
        flag='' if nidgrp == set(e.nodeids()) else ' (fragmented)',
        delim=delim,
        ed_list=delim.join(
            ed.format(
                membership=connected if n.nodeid in nidgrp else '|',
                id=n.nodeid,
                pred=n.pred.short_form(),
                lnk=str(n.lnk) if n.lnk else '',
                carg=carg.format(constant=n.carg) if n.carg else '',
                props=proplist.format(
                    varsort=n.cvarsort + ' ' if n.cvarsort else '',
                    proplist=', '.join(
                        '{} {}'.format(k, v)
                        for k, v in sorted(n.properties.items())
                    )
                ) if properties and n.sortinfo else '',
                dep_list=(', '.join(
                    '{} {}'.format(rargname, tgt)
                    for rargname, tgt in sorted(
                        e.edges(n.nodeid).items(),
                        key=lambda x: rargname_sortkey(x[0])
                    )
                )),
            )
            for n in e.nodes()
        ),
        enddelim='\n' if pretty_print else ''
    )
