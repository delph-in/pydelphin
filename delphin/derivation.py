# coding: utf-8

"""
Classes and functions related to derivation trees.
"""

import re
from collections import namedtuple, Sequence

# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401
from delphin.exceptions import PyDelphinSyntaxError


class DerivationSyntaxError(PyDelphinSyntaxError):
    """Raised when parsing an invalid UDF string."""


_all_fields = (
    'form',
    'tokens',
    'id',
    'entity',
    'score',
    'start',
    'end',
    'daughters',
    'head',
    'type',
)


def from_string(s):
    """
    Instantiate a Derivation from a UDF or UDX string representation.

    The UDF/UDX representations are as output by a processor like the
    `LKB <http://moin.delph-in.net/LkbTop>`_ or
    `ACE <http://sweaglesw.org/linguistics/ace/>`_, or from the
    :meth:`UDFNode.to_udf` or :meth:`UDFNode.to_udx` methods.

    Args:
        s (str): UDF or UDX serialization
    """
    udfnode = _from_string(s)
    return Derivation(*udfnode, head=udfnode._head, type=udfnode.type)


def from_dict(d):
    """
    Instantiate a Derivation from a dictionary representation.

    The dictionary representation may come from the HTTP interface
    (see the `ErgApi <http://moin.delph-in.net/ErgApi>`_ wiki) or
    from the :meth:`UDFNode.to_dict` method. Note that in the
    former case, the JSON response should have already been decoded
    into a Python dictionary.

    Args:
        d (dict): dictionary representation of a derivation
    """
    return Derivation(*_from_dict(d))


class _UDFNodeBase(object):
    """
    Base class for :class:`UDFNode` and :class:`UDFTerminal`.
    """
    def __str__(self):
        return self.to_udf(indent=None)

    # cannot rely on default __ne__ while namedtuple is a shared base class
    def __ne__(self, other):
        if not isinstance(other, _UDFNodeBase):
            return NotImplemented
        return not (self == other)

    @property
    def parent(self):
        return self._parent

    # serialization

    def to_udf(self, indent=1):
        """
        Encode the node and its descendants in the UDF format.

        Args:
            indent (int): the number of spaces to indent at each level
        Returns:
            str: the UDF-serialized string
        """
        return _to_udf(self, indent, 1)

    def to_udx(self, indent=1):
        """
        Encode the node and its descendants in the UDF export format.

        Args:
            indent (int): the number of spaces to indent at each level
        Returns:
            str: the UDX-serialized string
        """
        return _to_udf(self, indent, 1, udx=True)

    def to_dict(self, fields=_all_fields, labels=None):
        """
        Encode the node as a dictionary suitable for JSON serialization.

        Args:
            fields: if given, this is a whitelist of fields to include
                on nodes (`daughters` and `form` are always shown)
            labels: optional label annotations to embed in the
                derivation dict; the value is a list of lists matching
                the structure of the derivation (e.g.,
                `["S" ["NP" ["NNS" ["Dogs"]]] ["VP" ["VBZ" ["bark"]]]]`)
        Returns:
            dict: the dictionary representation of the structure
        """
        return _to_dict(self, fields, labels)


class UDFToken(namedtuple('UDFToken', 'id tfs')):
    """
    A token represenatation in derivations.

    Token data are not formally nodes, but do have an `id`. Most
    :class:`UDFTerminal` nodes will only have one UDFToken, but
    multi-word entities (e.g. "ad hoc") will have more than one.

    Args:
        id (int): token identifier
        tfs (str): the feature structure for the token
    """
    def __new__(cls, id, tfs):
        if id is not None:
            id = int(id)
        return super(UDFToken, cls).__new__(cls, id, tfs)

    def __repr__(self):
        return f'<UDFToken object ({self.id} {self.tfs!r}) at {id(self)}>'

    def __eq__(self, other):
        """
        Token data are the same if they have the same feature structure.
        """
        if not isinstance(other, UDFToken):
            return NotImplemented
        return self.tfs == other.tfs


class UDFTerminal(_UDFNodeBase, namedtuple('UDFTerminal', 'form tokens')):
    """
    Terminal nodes in the Unified Derivation Format.

    The *form* field is always set, but *tokens* may be `None`.

    See: http://moin.delph-in.net/ItsdbDerivations

    Args:
        form (str): surface form of the terminal
        tokens (list, optional): iterable of tokens
        parent (UDFNode, optional): parent node in derivation
    """

    def __new__(cls, form, tokens=None, parent=None):
        if tokens is None:
            tokens = []
        t = super(UDFTerminal, cls).__new__(cls, form, tokens)
        # internal bookkeeping
        t._parent = parent
        return t

    def __repr__(self):
        return f'<UDFTerminal object ({self.form}) at {id(self)}>'

    def __eq__(self, other):
        """
        Terminal nodes are the same if they have the same form and
        token data.
        """
        if not isinstance(other, UDFTerminal):
            return NotImplemented
        if self.form != other.form:
            return False
        if self.tokens != other.tokens:
            return False
        return True

    def is_root(self):
        """
        Return `False` (as a `UDFTerminal` is never a root).

        This function is provided for convenience, so one does not need
        to check if `isinstance(n, UDFNode)` before testing if the node
        is a root.
        """
        return False


class UDFNode(_UDFNodeBase,
              namedtuple('UDFNode', 'id entity score start end daughters')):
    """
    Normal (non-leaf) nodes in the Unified Derivation Format.

    Root nodes are just UDFNodes whose `id`, by convention, is
    `None`. The `daughters` list can composed of either UDFNodes or
    other objects (generally it should be uniformly one or the other).
    In the latter case, the `UDFNode` is a preterminal, and the
    daughters are terminal nodes.

    Args:
        id (int): unique node identifier
        entity (str): grammar entity represented by the node
        score (float, optional): probability or weight of the node
        start (int, optional): start position of tokens encompassed by
            the node
        end (int, optional): end position of tokens encompassed by the
            node
        daughters (list, optional): iterable of daughter nodes
        head (bool, optional): `True` if the node is a syntactic head
            node
        type (str, optional): grammar type name
        parent (UDFNode, optional): parent node in derivation
    """

    def __new__(cls, id, entity,
                score=None, start=None, end=None, daughters=None,
                head=None, type=None, parent=None):
        # numeric fields can be underspecified as -1 if not a root
        if id is not None:
            id = int(id)
            score = -1.0 if score is None else float(score)
            start = -1 if start is None else int(start)
            end = -1 if end is None else int(end)
        # for convenience make sure daughters is a list if None
        if daughters is None:
            daughters = []
        # make sure daughters are not roots (is this check unnecessary?)
        if any(dtr.is_root() for dtr in daughters):
            raise ValueError('Daughter nodes cannot be roots.')
        node = super(UDFNode, cls).__new__(
            cls, id, entity, score, start, end, daughters
        )
        # internal bookkeeping
        node._parent = parent
        node._head = head
        node.type = type
        return node

    def __repr__(self):
        return '<UDFNode object ({}, {}, {}, {}, {}) at {}>'.format(
            self.id, self.entity, self.score, self.start, self.end, id(self)
        )

    def __eq__(self, other):
        """
        Two derivations are equal if their entities, tokenization, and
        daughters are the same. IDs and scores are irrelevant.
        """
        if not isinstance(other, UDFNode):
            return NotImplemented
        # Check attributes
        if self.entity.lower() != other.entity.lower():
            return False
        if self.type != other.type:
            return False
        if self.is_head() != other.is_head():
            return False
        if self.start != other.start or self.end != other.end:
            return False
        if len(self.daughters) != len(other.daughters):
            return False
        if any(a != b for a, b in zip(self.daughters, other.daughters)):
            return False
        # Return true if they're the same!
        return True

    def is_root(self):
        """
        Return `True` if the node is a root node.

        Note:
            This is not simply the top node; by convention, a node is
            a root if its `id` is `None`.
        """
        return self.id is None

    # UDX extensions

    def is_head(self):
        """
        Return `True` if the node is a head.

        A node is a head if it is marked as a head in the UDX format or
        it has no siblings. `False` is returned if the node is known
        to not be a head (has a sibling that is a head). Otherwise it
        is indeterminate whether the node is a head, and `None` is
        returned.

        """
        if (self._head or self.is_root()
                or len(getattr(self._parent, 'daughters', [None])) == 1):
            return True
        elif any(dtr._head for dtr in self._parent.daughters):
            return False
        return None

    # Convenience methods

    def preterminals(self):
        """
        Return the list of preterminals (i.e. lexical grammar-entities).
        """
        nodes = []
        for dtr in self.daughters:
            if isinstance(dtr, UDFTerminal):
                nodes.append(self)
            else:
                nodes.extend(dtr.preterminals())
        return nodes

    def terminals(self):
        """
        Return the list of terminals (i.e. lexical units).
        """
        nodes = []
        for dtr in self.daughters:
            if isinstance(dtr, UDFTerminal):
                nodes.append(dtr)
            else:
                nodes.extend(dtr.terminals())
        return nodes

    def internals(self):
        """
        Return the list of internal nodes.

        Internal nodes are nodes above preterminals. In other words,
        the union of internals and preterminals is the set of
        nonterminal nodes.
        """
        if any(isinstance(dtr, UDFTerminal) for dtr in self.daughters):
            return []
        nodes = [self]
        for dtr in self.daughters:
            nodes.extend(dtr.internals())
        return nodes


class Derivation(UDFNode):
    """
    A [incr tsdb()] derivation.

    A Derivation object is simply a :class:`UDFNode` but as it is
    intended to represent an entire derivation tree it performs
    additional checks on instantiation if the top node is a root node,
    namely that the top node only has the *entity* attribute set, and
    that it has only one node on its *daughters* list.
    """

    def __init__(self, id, entity,
                 score=None, start=None, end=None, daughters=None,
                 head=None, type=None, parent=None):
        # Note: Attribute assignment is done in UDFNode.__new__(), so
        #       this only checks the arguments.
        # If id is None, it is a root, and score, start, and end must
        # all be None, and daughters must be a list with one UDFNode
        if id is None:
            if score is not None or start is not None or end is not None:
                raise TypeError(
                    'Root nodes (with id=None) of Derivation objects '
                    'must have *score*, *start*, and *end* set to None.'
                )
            if (daughters is None or len(daughters) != 1
                    or not isinstance(daughters[0], UDFNode)):
                raise ValueError(
                    'Root nodes (with id=None) of Derivation objects '
                    'must have a single daughter node.'
                )


###############################################################################
# Deserialization

# note that this regex doesn't have the initial open-parenthesis
# (see _from_string())
_udf_re = re.compile(
    # regular node
    r'\s*(?P<id>{token})\s+(?P<entity>{string}|{token})'
    r'\s+(?P<score>{token})\s+(?P<start>{token})'
    r'\s+(?P<end>{token})\s*\('
    # branch end
    r'|\s*(?P<done>\))'
    # terminal node (lexical token info; unbound list)
    r'|\s*(?P<form>{string})'
    # anything after form is optional
    r'('
    # LKB-style start/end (e.g. ("word" 1 2) )
    r'\s+(?P<lkb_start>\d+)\s+(?P<lkb_end>\d+)'
    # Token TFSs (e.g. ("word" 1 "token [ ... ]" 2 "token [... ]") )
    # usually there's only one, though
    r'|(?P<tokens>(?:\s+{token}\s+{string})*)'
    r')?'
    r'\s*\)'  # end terminal node
    # root symbol
    r'|\s*(?P<root>{token})\s*\(?'
    .format(token=r'[^\s()]+', string=r'"[^"\\]*(?:\\.[^"\\]*)*"')
)


def _from_string(s):
    if not (s.startswith('(') and s.endswith(')')):
        raise DerivationSyntaxError(
            'missing opening or closing parentheses', text=s)
    s_ = s[1:]  # get rid of initial open-parenthesis
    stack = []
    deriv = None
    matches = _udf_re.finditer(s_)
    for match in matches:
        if match.group('done'):
            node = stack.pop()
            if len(stack) == 0:
                deriv = node
                break
            else:
                stack[-1].daughters.append(node)
        elif match.group('form'):
            gd = match.groupdict()
            # ignore LKB-style start/end data if it exists on gd
            term = UDFTerminal(
                _unquote(gd['form']),
                tokens=_udf_tokens(gd.get('tokens')),
                parent=stack[-1] if stack else None
            )
            stack[-1].daughters.append(term)
        elif match.group('id'):
            gd = match.groupdict()
            head = None
            entity, _, type = gd['entity'].partition('@')
            if entity[0] == '^':
                entity = entity[1:]
                head = True
            if type == '':
                type = None
            udf = UDFNode(gd['id'], entity, gd['score'],
                          gd['start'], gd['end'],
                          head=head, type=type,
                          parent=stack[-1] if stack else None)
            stack.append(udf)
        elif match.group('root'):
            udf = UDFNode(None, match.group('root'))
            stack.append(udf)
    if deriv is None:
        raise DerivationSyntaxError(text=s)
    elif stack:
        raise DerivationSyntaxError(
            'possibly unbalanced parentheses', text=s)
    return deriv


def _unquote(s):
    if s is not None:
        return re.sub(r'^"(.*)"$', r'\1', s)
    return None


def _udf_tokens(tokenstring):
    tokens = []
    if tokenstring:
        toks = re.findall(
            r'\s*({id})\s+({tfs})'
            .format(id=r'\d+', tfs=r'"[^"\\]*(?:\\.[^"\\]*)*"'),
            tokenstring
        )
        for tid, tfs in toks:
            tokens.append(UDFToken(tid, _unquote(tfs)))
    return tokens


def _from_dict(d, parent=None):
    if 'daughters' in d:
        n = UDFNode(
            d.get('id'),
            d['entity'],
            score=d.get('score'),
            start=d.get('start'),
            end=d.get('end'),
            head=d.get('head'),
            type=d.get('type'),
            parent=parent
        )
        n.daughters.extend(
            _from_dict(dtr, parent=n) for dtr in d['daughters']
        )
        return n
    elif 'form' in d:
        n = UDFNode(
            d.get('id'),
            d['entity'],
            score=d.get('score'),
            start=d.get('start'),
            end=d.get('end'),
            head=d.get('head'),
            type=d.get('type'),
            parent=parent
        )
        n.daughters.append(
            UDFTerminal(
                form=d['form'],
                tokens=[UDFToken(t['id'], t['tfs'])
                        for t in d.get('tokens', [])],
                parent=n
            )
        )
        return n


###############################################################################
# Serialization

def _to_udf(obj, indent, level, udx=False):
    delim = ' ' if indent is None else '\n' + ' ' * indent * level
    if isinstance(obj, UDFNode):
        entity = obj.entity
        if udx:
            if obj._head:
                entity = '^' + entity
            if obj.type:
                entity = f'{entity}@{obj.type}'
        dtrs = [_to_udf(dtr, indent, (level + 1), udx)
                for dtr in obj.daughters]
        dtrs = delim.join([''] + dtrs)  # empty first item to force indent
        if obj.id is None:
            return f'({entity}{dtrs})'
        else:
            # :g for score makes -1.0 look like -1
            return '({} {} {:g} {} {}{})'.format(
                obj.id,
                entity,
                obj.score,
                obj.start,
                obj.end,
                dtrs
            )
    elif isinstance(obj, UDFTerminal):
        form = f'"{obj.form}"'
        tokens = [f'{t.id} "{t.tfs}"' for t in obj.tokens]
        return '({})'.format(delim.join([form] + tokens))
    else:
        raise TypeError(f'Invalid node: {obj!s}')


def _to_dict(obj, fields, labels):
    fields = set(fields)
    diff = fields.difference(_all_fields)
    if isinstance(labels, Sequence):
        labels = _map_labels(obj, labels)
    elif labels is None:
        labels = {}
    if diff:
        raise ValueError(
            'Invalid field(s): {}'.format(', '.join(diff))
        )
    return _to_dict_recursive(obj, fields, labels)


def _map_labels(drv, labels):
    m = {}
    if not labels:
        return m
    if labels[0]:
        m[drv.id] = labels[0]
    subds = getattr(drv, 'daughters', getattr(drv, 'tokens', []))
    sublbls = labels[1:]
    if (sublbls and len(subds) != len(sublbls)):
        raise ValueError('Labels do not match derivation structure.')
    for d, lbls in zip(subds, sublbls):
        if hasattr(d, 'id'):
            m.update(_map_labels(d, lbls))
    return m


def _to_dict_recursive(obj, fields, labels):
    d = {}
    if isinstance(obj, UDFNode):
        if 'entity' in fields:
            d['entity'] = obj.entity
        if obj.id is not None:
            if 'id' in fields:
                d['id'] = obj.id
            if 'score' in fields:
                d['score'] = obj.score
            if 'start' in fields:
                d['start'] = obj.start
            if 'end' in fields:
                d['end'] = obj.end
            if 'type' in fields and obj.type:
                d['type'] = obj.type
            if 'head' in fields and obj._head:
                d['head'] = obj._head
        dtrs = obj.daughters
        if dtrs:
            # terminals should always be single daughters
            if len(dtrs) == 1 and isinstance(dtrs[0], UDFTerminal):
                # merge terminal daughter info into current node
                d.update(_to_dict_recursive(dtrs[0], fields, labels))
            else:
                d['daughters'] = [
                    _to_dict_recursive(dtr, fields, labels) for dtr in dtrs
                ]
        if obj.id in labels:
            d['label'] = labels[obj.id]
    elif isinstance(obj, UDFTerminal):
        d['form'] = obj.form
        # d['from'] = min(t.tfs['+FROM'] for t in obj.tokens)
        # d['to'] = max(t.tfs['+TO'] for t in obj.tokens)
        if obj.tokens and 'tokens' in fields:
            tokens = []
            for tok in obj.tokens:
                td = {'id': tok.id}
                # td['from'] = tok.tfs['+FROM']
                # td['to'] = tok.tfs['+TO']
                td['tfs'] = tok.tfs
                tokens.append(td)
            d['tokens'] = tokens
    # else:
    #     raies TypeError()
    return d
