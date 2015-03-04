import pdb
import re
from collections import deque, defaultdict
from itertools import product
from .components import Pred
from .util import powerset
from delphin._exceptions import XmrsError

TOP = 'TOP'

class XmrsPathError(XmrsError): pass

class XmrsPath(object):

    __slots__ = ('start', '_depth', '_distance', '_preds')

    def __init__(self, startnode):
        self.start = startnode
        self.calculate_metrics()

    def calculate_metrics(self):
        self._distance = {}
        self._depth = {}
        self._preds = {}
        self._calculate_metrics(self.start, 0, 0)

    def _calculate_metrics(self, curnode, depth, distance):
        if curnode is None:
            return
        # add pred index
        try:
            self._preds[curnode.pred].append(curnode)
        except KeyError:
            self._preds[curnode.pred] = []
            self._preds[curnode.pred].append(curnode)
        _id = id(curnode)
        # we may re-update if we're on a shorter path
        updated = False
        if _id not in self._distance or distance < self._distance[_id]:
            self._distance[_id] = distance
            updated = True
        if _id not in self._depth or abs(depth) < abs(self._depth[_id]):
            self._depth[_id] = depth
            updated = True
        if not updated:
            return
        for link in curnode.links:
            if link.endswith('>'):
                self._calculate_metrics(curnode[link], depth+1, distance+1)
            elif link.startswith('<'):
                self._calculate_metrics(curnode[link], depth-1, distance+1)
            else:
                self._calculate_metrics(curnode[link], depth, distance+1)

    def copy(self):
        return XmrsPath(self.start.copy())

    def distance(self, node=None):
        if node is None:
            return max(self._distance.values())
        else:
            return self._distance[id(node)]

    def depth(self, node=None, direction=max):
        if node is None:
            return direction(self._depth.values())
        return self._depth[id(node)]

    def select(self, pred):
        return self._preds.get(pred, [])

    def find(self, pred):
        if pred not in self._preds:
            return []
        return find(self.start, pred)

    def follow(self, connectors):
        node = self.start
        connectors = list(reversed(connectors))
        while connectors:
            node = node[connectors.pop()]
        return node

    def extend(self, extents):
        for connectors, extent in extents:
            # the final connector may be new information
            tgt = self.follow(connectors[:-1])
            if connectors:
                subtgt = tgt.links.get(connectors[-1])
                if subtgt is None:
                    tgt.links[connectors[-1]] = extent
                    continue
                else:
                    tgt = subtgt
            tgt.update(extent)
        self.calculate_metrics()


class XmrsPathNode(object):

    __slots__ = ('nodeid', 'pred', 'links')

    def __init__(self, nodeid, pred, links=None):
        self.nodeid = nodeid
        self.pred = pred
        self.links = dict(links or [])

    def __getitem__(self, key):
        return self.links[key]

    def __iter__(self):
        return iter(self.links.items())

    def copy(self):
        n = XmrsPathNode(self.nodeid, self.pred)
        for connector, tgt in self.links.items():
            n.links[connector] = tgt.copy() if tgt is not None else tgt
        return n

    def update(self, other):
        self.nodeid = other.nodeid or self.nodeid
        self.pred = other.pred or self.pred
        for connector, tgt in other.links.items():
            if not self.links.get(connector):
                self.links[connector] = tgt
            else:
                self[connector].update(tgt)


# HELPER FUNCTIONS ##########################################################

def get_nodeids(path):
    yield path.nodeid
    for link, path_node in path:
        if path_node is None:
            continue
        for nid in get_nodeids(path_node):
            yield nid


def get_preds(path):
    yield path.pred
    for link, path_node in path:
        if path_node is None:
            continue
        for pred in get_preds(path_node):
            yield pred


def link_is_directed(link):
    return bool(link.argname) or link.post != 'EQ'


def headed(connector):
    # quantifiers and X/EQ links are not the heads of their subgraphs
    if connector == '<RSTR/H:' or connector.endswith('/EQ:'):
        return True
    if (connector == ':RSTR/H>' or
            connector.endswith('/EQ>') or
            connector.startswith('<')):
        return False
    return True


def connector_sort(connector):
    return (
        not connector.endswith('>'),  # forward links first
        not connector.startswith('<'),  # then backward, then undirected
        not connector[1:].startswith('LBL'),  # LBL before other args
        connector[1:].startswith('BODY'),  # BODY last
        connector[1:]  # otherwise alphabetical
    )


# WRITING PATHS #############################################################

def format(node, sort_key=connector_sort, trailing_connectors='usually'):
    if isinstance(node, XmrsPath):
        node = node.start
    return _format(
        node, sort_key=sort_key, trailing_connectors=trailing_connectors
    )

def _format(node, sort_key=connector_sort, trailing_connectors='usually'):
    if node is None:
        return ''
    #if node.nodeid is not None:
    #    symbol = '#{}'.format(node.nodeid)
    if node.pred is not None:
        symbol = str(node.pred)
    else:
        symbol = '*'
    links = []
    connectors = node.links.keys()
    if sort_key:
        connectors = sorted(connectors, key=sort_key)
    for conn in connectors:
        tgt = node.links[conn]
        if (tgt or
            trailing_connectors == 'always' or
            (trailing_connectors == 'usually' and conn != ':/EQ:') or
            (trailing_connectors == 'forward' and conn.endswith('>')) or
            (trailing_connectors == 'backward' and conn.startswith('<'))):

            links.append(
                '{}{}'.format(
                    conn,
                    _format(
                        tgt,
                        sort_key=sort_key,
                        trailing_connectors=trailing_connectors
                    )
                )
            )
    if len(links) > 1:
        subpath = '({})'.format(' & '.join(links))
    else:
        subpath = ''.join(links)  # possibly just ''
    return '{}{}'.format(symbol, subpath)



# FINDING PATHS #############################################################

def walk(
        xmrs,
        startnode=None,
        method='top-down',
        allow_eq=False,
        max_distance=-1):
    if method not in ('top-down', 'bottom-up', 'headed'):
        raise XmrsPathError("Invalid path-finding method: {}".format(method))
    if startnode is None:
        startnode = 0  # TOP
    links = _build_linkdict(xmrs, allow_eq)
    agenda = deque()
    seen = {}




def _walk(xmrs, startnode, method, allow_eq, max_distance): pass

def find_paths(
        xmrs,
        nodeids=None,
        method='top-down',
        allow_eq=False,
        max_distance=-1):
    if method not in ('top-down', 'bottom-up', 'headed'):
        raise XmrsPathError("Invalid path-finding method: {}".format(method))
    if nodeids is None: nodeids = [0] + xmrs.nodeids  # 0 for TOP
    links = _build_linkdict(xmrs, allow_eq)

    paths = defaultdict(list)
    for nid in nodeids:
        if nid in paths: continue  # maybe already visited in _find_paths
        for path in _find_paths(
                xmrs, nid, links, set(), method=method,
                max_distance=max_distance):
            paths[path.nodeid].append(XmrsPath(path))

    for nid in nodeids:
        for path in sorted(paths.get(nid, []), key=lambda p: p.distance()):
            yield path

def _build_linkdict(xmrs, allow_eq):
    links = defaultdict(dict)
    for link in xmrs.links:
        connector = '{}/{}'.format(link.argname or '', link.post)
        if link_is_directed(link):
            links[link.start][':{}>'.format(connector)] = link.end
            links[link.end]['<{}:'.format(connector)] = link.start
        elif allow_eq:
            links[link.start][':{}:'.format(connector)] = link.end
            #links[link.end][':{}:'.format(connector)] = link.start
    return links

def _find_paths(
        xmrs,
        nodeid,
        links,
        seen,
        method='top-down',
        max_distance=-1):
    if method not in ('top-down', 'bottom-up', 'headed'):
        raise XmrsPathError("Invalid path-finding method: {}".format(method))
    #if nodeid in seen  # currently not working
    if max_distance == 0: return None
    seen.add(nodeid)

    symbol = TOP if nodeid == 0 else xmrs.get_pred(nodeid)
    local_links = links.get(nodeid, {})
    connectors = _get_connectors(method, local_links)
    # first just use the unfilled connectors if not TOP
    if nodeid != 0:
        yield XmrsPathNode(nodeid, symbol, links=connectors)

    if connectors:
        #pdb.set_trace()
        subpaths = {}
        for connector in connectors:
            tgtnid = local_links[connector]
            if tgtnid == 0:
                subpaths[connector] = [XmrsPathNode(tgtnid, TOP)]
            else:
                subpaths[connector] = list(
                    _find_paths(
                        xmrs, tgtnid, links, seen, method=method,
                        max_distance=max_distance-1,
                    )
                )
        # beware of magic below:
        #   links maps a connector (like ARG1/NEQ) to a list of subpaths.
        #   This gets the product of subpaths for all connectors, then remaps
        #   the connector to the appropriate subpaths. E.g. if links is like
        #   {':ARG1/NEQ>': [def], ':ARG2/NEQ>': [ghi, jkl]} then lds is like
        #   [{':ARG1/NEQ>': def, 'ARG2/NEQ>': ghi},
        #    {':ARG1/NEQ>': def, 'ARG2/NEQ>': jkl}]
        lds = map(
            lambda z: dict(zip(subpaths.keys(), z)),
            product(*subpaths.values())
        )
        for ld in lds:
            yield XmrsPathNode(nodeid, symbol, links=ld)

def _get_connectors(method, links):
    # top-down: :X/Y> or :X/Y: (the latter only if added)
    if method == 'top-down':
        return dict((c, None) for c in links if c.startswith(':'))
    elif method == 'bottom-up':
        return dict((c, None) for c in links if c.endswith(':'))
    elif method == 'headed':
        return dict((c, None) for c in links if headed(c))


# READING PATHS #############################################################

tokenizer = re.compile(
    r'(?P<dq_string>"[^"\\]*(?:\\.[^"\\]*)*")'  # quoted strings
    r"|(?P<sq_string>'[^ \\]*(?:\\.[^ \\]*)*)"  # single-quoted 'strings
    r'|(?P<fwd_connector>:[^/]*/(?:EQ|NEQ|HEQ|H)>)'  # :X/Y> connector
    r'|(?P<bak_connector><[^/]*/(?:EQ|NEQ|HEQ|H):)'  # <X/Y: connector
    r'|(?P<und_connector>:[^/]*/(?:EQ|NEQ|HEQ|H):)'  # :X/Y: connector
    r'|(?P<symbol>[^\s*:/><@()\[\]=&|]+)'  # non-breaking characters
    r'|(?P<punc>[*()&|])'  # meaningful punctuation
)

def read_path(path_string):
    toks = deque((mo.lastgroup, mo.group())
                 for mo in tokenizer.finditer(path_string))
    try:
        startnode = _read_node(toks)
    except IndexError:
        raise XmrsPathError('Unexpected termination for path: {}'
            .format(path_string))
    if startnode is None:
        raise XmrsPathError('Error reading path: {}'
            .format(path_string))
    elif toks:
        raise XmrsPathError('Unconsumed tokens: {}'
            .format(', '.join(tok[1] for tok in toks)))
    path = XmrsPath(startnode)
    return path

def _read_node(tokens):
    if not tokens: return None
    mtype, mtext = tokens.popleft()
    if mtype in ('dq_string', 'sq_string', 'symbol'):
        links = _read_links(tokens)
        return XmrsPathNode(
            None,
            Pred.stringpred(mtext),
            links
        )
    else:
        tokens.appendleft((mtype, mtext))  # put it back
    return None  # current position isn't a path node

def _read_links(tokens):
    if not tokens: return None
    mtype, mtext = tokens.popleft()
    if mtype in ('fwd_connector', 'bak_connector', 'und_connector'):
        return {mtext: _read_node(tokens)}
    elif mtext == '(':
        links = {}
        mtype, mtext = tokens.popleft()
        while mtext != ')':
            links[mtext] = _read_node(tokens)
            mtype, mtext = tokens.popleft()
            if mtext in ('&', '|'):
                mtype, mtext = tokens.popleft()
            elif mtext != ')':
                raise XmrsPathError('Unexpected token: {}'.format(mtext))
        return links
    else:
        tokens.appendleft((mtype, mtext))  # put it back
    return None  # not a link


# SEARCHING PATHS ###########################################################


def find(node, pred, connectors=[]):
    matches = []
    if node and node.pred == pred:
        matches.append((connectors, node))
    for connector, tgt in node.links.items():
        if not tgt:
            continue
        for match in find(tgt, pred, connectors + [connector]):
            matches.append(match)
    return matches


def find_extents(node1, node2):
    exts = []
    for (connectors, first_node) in find(node1, node2.pred):
        for (ext_connections, ext) in extents(first_node, node2):
            exts.append((connectors + ext_connections, ext))
    return exts


def extents(node1, node2):
    assert node1.pred == node2.pred
    exts = []
    # if a constraint is violated, raise XmrsPathError
    # if a constraint exists on node1 and node2, dive
    # if one is on node1 but not node2, ignore
    # if one is on node2 but not node1, return
    for connector, tgt2 in node2.links.items():
        if connector in node1.links:
            tgt1 = node1.links[connector]
            if tgt2 is None:
                continue
            elif tgt1 is None:
                exts.append(([connector], tgt2))
            elif tgt1.pred == tgt2.pred:
                for connectors, ext in extents(tgt1, tgt2):
                    exts.append(([connector] + connectors, ext))
            else:
                raise XmrsPathError('Incompatible paths.')
        else:
            exts.append(([connector], tgt2))
    return exts
