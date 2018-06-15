# coding: utf-8

"""
Classes and functions related to derivation trees.

Derivation trees represent a unique analysis of an input using an
implemented grammar. They are a kind of syntax tree, but as they use
the actual grammar entities (e.g., rules or lexical entries) as node
labels, they are more specific than trees using general category labels
(e.g., "N" or "VP"). As such, they are more likely to change across
grammar versions.

.. seealso::
  More information about derivation trees is found at
  http://moin.delph-in.net/ItsdbDerivations

For the following Japanese example...

::

    遠く    に  銃声    が  聞こえ た 。
    tooku   ni  juusei  ga  kikoe-ta
    distant LOC gunshot NOM can.hear-PFV
    "Shots were heard in the distance."

... here is the derivation tree of a parse from
`Jacy <http://moin.delph-in.net/JacyTop>`_ in the Unified Derivation
Format (UDF)::

    (utterance-root
     (564 utterance_rule-decl-finite 1.02132 0 6
      (563 hf-adj-i-rule 1.04014 0 6
       (557 hf-complement-rule -0.27164 0 2
        (556 quantify-n-rule 0.311511 0 1
         (23 tooku_1 0.152496 0 1
          ("遠く" 0 1)))
        (42 ni-narg 0.478407 1 2
         ("に" 1 2)))
       (562 head_subj_rule 1.512 2 6
        (559 hf-complement-rule -0.378462 2 4
         (558 quantify-n-rule 0.159015 2 3
          (55 juusei_1 0 2 3
           ("銃声" 2 3)))
         (56 ga 0.462257 3 4
          ("が" 3 4)))
        (561 vstem-vend-rule 1.34202 4 6
         (560 i-lexeme-v-stem-infl-rule 0.365568 4 5
          (65 kikoeru-stem 0 4 5
           ("聞こえ" 4 5)))
         (81 ta-end 0.0227589 5 6
          ("た" 5 6)))))))

In addition to the UDF format, there is also the UDF export format
"UDX", which adds lexical type information and indicates which daughter
node is the head, and a dictionary representation, which is useful for
JSON serialization. All three are supported by PyDelphin.

Derivation trees have 3 types of nodes:

  * root nodes, with only an entity name and a single child

  * normal nodes, with 5 fields (below) and a list of children

    - *id* -- an integer id given by the producer of the derivation
    - *entity* -- rule or type name
    - *score* -- a (MaxEnt) score for the current node's subtree
    - *start* -- the character index of the left-most side of the tree
    - *end* -- the character index of the right-most side of the tree

  * terminal/left/lexical nodes, which contain the input tokens
    processed by that subtree

This module uses the :class:`UdfNode` class for capturing root and
normal nodes. Root nodes are expressed as a :class:`UdfNode` whose
`id` is `None`. For root nodes, all fields except `entity` and
the list of daughters are expected to be `None`. Leaf nodes are
simply an iterable of token information.

The :class:`Derivation` class---itself a :class:`UdfNode`---, has some
tree-level operations defined, in particular the
:meth:`Derivation.from_string` method, which is used to read the
serialized derivation into a Python object.

"""

import re
from collections import namedtuple, Sequence

from delphin.util import deprecated

_terminal_fields = ('form', 'tokens')
_token_fields = ('id', 'tfs')
_nonterminal_fields = ('id', 'entity', 'score', 'start', 'end', 'daughters')
_udx_fields = ('head', 'type')
_all_fields = tuple(
    set(_terminal_fields)
    .union(_nonterminal_fields)
    .union(_udx_fields)
)

class _UdfNodeBase(object):
    """
    Base class for :class:`UdfNode` and :class:`UdfTerminal`.
    """
    def __str__(self):
        return self.to_udf(indent=None)

    # for some reason != is not the opposite of __eq__ by default...
    def __ne__(self, other):
        eq = self.__eq__(other)
        if eq is NotImplemented: return eq  # pass this one along
        return not eq

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
        fields = set(fields)
        diff = fields.difference(_all_fields)
        if isinstance(labels, Sequence):
            labels = _map_labels(self, labels)
        elif labels is None:
            labels = {}
        if diff:
            raise ValueError(
                'Invalid field(s): {}'.format(', '.join(diff))
            )
        return _to_dict(self, fields, labels)


def _to_udf(obj, indent, level, udx=False):
    delim = ' ' if indent is None else '\n' + ' ' * indent * level
    if isinstance(obj, UdfNode):
        entity = obj.entity
        if udx:
            if obj._head:
                entity = '^' + entity
            if obj.type:
                entity = '{}@{}'.format(entity, obj.type)
        dtrs = [_to_udf(dtr, indent, level+1, udx) for dtr in obj.daughters]
        dtrs = delim.join([''] + dtrs)  # empty first item to force indent
        if obj.id is None:
            return '({}{})'.format(entity, dtrs)
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
    elif isinstance(obj, UdfTerminal):
        form = '"{}"'.format(obj.form)
        tokens = ['{} "{}"'.format(t.id, t.tfs) for t in obj.tokens]
        return '({})'.format(delim.join([form] + tokens))
    else:
        raise TypeError('Invalid node: {}'.format(str(obj)))


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


def _to_dict(obj, fields, labels):
    d = {}
    if isinstance(obj, UdfNode):
        if 'entity' in fields: d['entity'] = obj.entity
        if obj.id is not None:
            if 'id' in fields: d['id'] = obj.id
            if 'score' in fields: d['score'] = obj.score
            if 'start' in fields: d['start'] = obj.start
            if 'end' in fields: d['end'] = obj.end
            if 'type' in fields and obj.type: d['type'] = obj.type
            if 'head' in fields and obj._head: d['head'] = obj._head
        dtrs = obj.daughters
        if dtrs:
            # terminals should always be single daughters
            if len(dtrs) == 1 and isinstance(dtrs[0], UdfTerminal):
                # merge terminal daughter info into current node
                d.update(_to_dict(dtrs[0], fields, labels))
            else:
                d['daughters'] = [
                    _to_dict(dtr, fields, labels) for dtr in dtrs
                ]
        if obj.id in labels: d['label'] = labels[obj.id]
    elif isinstance(obj, UdfTerminal):
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


class UdfToken(namedtuple('UdfToken', _token_fields)):
    """
    A token represenatation in derivations.

    Token data are not formally nodes, but do have an `id`. Most
    :class:`UdfTerminal` nodes will only have one UdfToken, but
    multi-word entities (e.g. "ad hoc") will have more than one.

    Args:
        id (int): token identifier
        tfs (str): the feature structure for the token
    """
    def __new__(cls, id, tfs):
        if id is not None:
            id = int(id)
        return super(UdfToken, cls).__new__(cls, id, tfs)

    def __repr__(self):
        return '<UdfToken object ({} {!r}) at {}>'.format(
            self.id, self.tfs, id(self)
        )

    def __eq__(self, other):
        """
        Token data are the same if they have the same feature structure.
        """
        if not isinstance(other, UdfToken):
            return NotImplemented
        return self.tfs == other.tfs


class UdfTerminal(_UdfNodeBase, namedtuple('UdfTerminal', _terminal_fields)):
    """
    Terminal nodes in the Unified Derivation Format.

    The *form* field is always set, but *tokens* may be `None`.

    See: http://moin.delph-in.net/ItsdbDerivations

    Args:
        form (str): surface form of the terminal
        tokens (list, optional): iterable of tokens
        parent (UdfNode, optional): parent node in derivation
    """

    def __new__(cls, form, tokens=None, parent=None):
        if tokens is None:
            tokens = []
        t = super(UdfTerminal, cls).__new__(cls, form, tokens)
        # internal bookkeeping
        t._parent = parent
        return t

    def __repr__(self):
        return '<UdfTerminal object ({}) at {}>'.format(self.form, id(self))

    def __eq__(self, other):
        """
        Terminal nodes are the same if they have the same form and
        token data.
        """
        if not isinstance(other, UdfTerminal):
            return NotImplemented
        if self.form != other.form:
            return False
        if self.tokens != other.tokens:
            return False
        return True

    def is_root(self):
        """
        Return `False` (as a `UdfTerminal` is never a root).

        This function is provided for convenience, so one does not need
        to check if `isinstance(n, UdfNode)` before testing if the node
        is a root.
        """
        return False


class UdfNode(_UdfNodeBase, namedtuple('UdfNode', _nonterminal_fields)):
    """
    Normal (non-leaf) nodes in the Unified Derivation Format.

    Root nodes are just UdfNodes whose `id`, by convention, is
    `None`. The `daughters` list can composed of either UdfNodes or
    other objects (generally it should be uniformly one or the other).
    In the latter case, the `UdfNode` is a preterminal, and the
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
        parent (UdfNode, optional): parent node in derivation
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
        if daughters is None: daughters = []
        # make sure daughters are not roots (is this check unnecessary?)
        if any(dtr.is_root() for dtr in daughters):
            raise ValueError('Daughter nodes cannot be roots.')
        node = super(UdfNode, cls).__new__(
            cls, id, entity, score, start, end, daughters
        )
        # internal bookkeeping
        node._parent = parent
        node._head = head
        node.type = type
        return node

    def __repr__(self):
        return '<UdfNode object ({}, {}, {}, {}, {}) at {}>'.format(
            self.id, self.entity, self.score, self.start, self.end, id(self)
        )

    def __eq__(self, other):
        """
        Two derivations are equal if their entities, tokenization, and
        daughters are the same. IDs and scores are irrelevant.
        """
        if not isinstance(other, UdfNode):
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
        if (self._head or self.is_root() or
                len(getattr(self._parent, 'daughters', [None])) == 1):
            return True
        elif any(dtr._head for dtr in self._parent.daughters):
            return False
        return None

    @deprecated(final_version='1.0.0', alternative='UdfNode.entity')
    def basic_entity(self):
        """
        Return the entity without the lexical type information.

        In the export (UDX) format, lexical types follow entities of
        preterminal nodes, joined by an at-sign (`@`). In regular UDF
        or non-preterminal nodes, this will just return the entity
        string.

        .. deprecated:: 0.5.1
           Use :attr:`entity`
        """
        return self.entity

    @deprecated(final_version='1.0.0', alternative='UdfNode.type')
    def lexical_type(self):
        """
        Return the lexical type of a preterminal node.

        In export (UDX) format, lexical types follow entities of
        preterminal nodes, joined by an at-sign (`@`). In regular UDF
        or non-preterminal nodes, this will return None.

        .. deprecated:: 0.5.1
           Use :attr:`type`
        """
        return self.type

    # Convenience methods

    def preterminals(self):
        """
        Return the list of preterminals (i.e. lexical grammar-entities).
        """
        nodes = []
        for dtr in self.daughters:
            if isinstance(dtr, UdfTerminal):
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
            if isinstance(dtr, UdfTerminal):
                nodes.append(dtr)
            else:
                nodes.extend(dtr.terminals())
        return nodes

class Derivation(UdfNode):
    """
    A [incr tsdb()] derivation.

    This class exists to facilitate the reading of UDF string
    serializations and dictionary representations (e.g., decoded from
    JSON). The resulting structure is otherwise equivalent to a
    :class:`UdfNode`, and inherits all its methods.
    """

    # note that this regex doesn't have the initial open-parenthesis
    # (see from_string())
    udf_re = re.compile(
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

    def __init__(self, id, entity,
                 score=None, start=None, end=None, daughters=None,
                 head=None, type=None, parent=None):
        # Note: Attribute assignment is done in UdfNode.__new__(), so
        #       this only checks the arguments.
        # If id is None, it is a root, and score, start, and end must
        # all be None, and daughters must be a list with one UdfNode
        if id is None:
            if score is not None or start is not None or end is not None:
                raise TypeError(
                    'Root nodes (with id=None) of Derivation objects '
                    'must have *score*, *start*, and *end* set to None.'
                )
            if (daughters is None or len(daughters) != 1
                    or not isinstance(daughters[0], UdfNode)):
                raise ValueError(
                    'Root nodes (with id=None) of Derivation objects '
                    'must have a single daughter node.'
                )

    @classmethod
    def from_string(cls, s):
        """
        Instantiate a `Derivation` from a UDF or UDX string representation.

        The UDF/UDX representations are as output by a processor like the
        `LKB <http://moin.delph-in.net/LkbTop>`_ or
        `ACE <http://sweaglesw.org/linguistics/ace/>`_, or from the
        :meth:`UdfNode.to_udf` or :meth:`UdfNode.to_udx` methods.

        Args:
            s (str): UDF or UDX serialization
        """
        if not (s.startswith('(') and s.endswith(')')):
            raise ValueError(
                'Derivations must begin and end with parentheses: ( )'
            )
        s_ = s[1:]  # get rid of initial open-parenthesis
        stack = []
        deriv = None
        try:
            matches = cls.udf_re.finditer(s_)
            for match in matches:
                if match.group('done'):
                    node = stack.pop()
                    if len(stack) == 0:
                        deriv = node
                        break
                    else:
                        stack[-1].daughters.append(node)
                elif match.group('form'):
                    if len(stack) == 0:
                        raise ValueError('Possible leaf node with no parent.')
                    gd = match.groupdict()
                    # ignore LKB-style start/end data if it exists on gd
                    term = UdfTerminal(
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
                    udf = UdfNode(gd['id'], entity, gd['score'],
                                  gd['start'], gd['end'],
                                  head=head, type=type,
                                  parent=stack[-1] if stack else None)
                    stack.append(udf)
                elif match.group('root'):
                    udf = UdfNode(None, match.group('root'))
                    stack.append(udf)
        except (ValueError, AttributeError):
            raise ValueError('Invalid derivation: %s' % s)
        if stack or deriv is None:
            raise ValueError('Invalid derivation; possibly unbalanced '
                             'parentheses: %s' % s)
        return cls(*deriv, head=deriv._head, type=deriv.type)

    @classmethod
    def from_dict(cls, d):
        """
        Instantiate a `Derivation` from a dictionary representation.

        The dictionary representation may come from the HTTP interface
        (see the `ErgApi <http://moin.delph-in.net/ErgApi>`_ wiki) or
        from the :meth:`UdfNode.to_dict` method. Note that in the
        former case, the JSON response should have already been decoded
        into a Python dictionary.

        Args:
            d (dict): dictionary representation of a derivation
        """
        return cls(*_from_dict(d))

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
            tokens.append(UdfToken(tid, _unquote(tfs)))
    return tokens

def _from_dict(d, parent=None):
    if 'daughters' in d:
        n = UdfNode(
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
        n = UdfNode(
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
            UdfTerminal(
                form=d['form'],
                tokens=[UdfToken(t['id'], t['tfs'])
                        for t in d.get('tokens', [])],
                parent=n
            )
        )
        return n
