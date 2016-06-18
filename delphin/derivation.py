# coding: utf-8

"""
Classes and functions related to Derivation trees.
see here: http://moin.delph-in.net/ItsdbDerivations

For the following example from Jacy:

    遠く    に  銃声    が  聞こえ た 。
    tooku   ni  juusei  ga  kikoe-ta
    distant LOC gunshot NOM can.hear-PFV
    "Shots were heard in the distance."

Here is the derivation tree of a parse:

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

Derivation trees have 3 types of nodes:
  * root nodes, with only an entity name and a single child
  * normal nodes, with 5 fields (below) and a list of children
    - *id* (an integer id given by the processor that produced the derivation)
    - *entity* (e.g. rule or type name)
    - *score* (a (MaxEnt) score for the subtree rooted at the current node)
    - *start* (the character index of the left-most side of the tree)
    - *end* (the character index of the right-most side of the tree)
  * terminal/left/lexical nodes, which contain the input tokens processed
    by that subtree

This module has a class UdfNode for capturing root and normal nodes.
Root nodes are expressed as a UdfNode whose *id* is `None`. For root
nodes, all fields except entity and the list of daughters are expected
to be `None`. Leaf nodes are simply an iterable of token information.

The Derivation class---itself a UdfNode---, has some tree-level
operations defined, in particular the `from_string()` method, which is
used to read the serialized derivation into a Python object.

"""


import re
from collections import namedtuple

_terminal_fields = ('form', 'tokens')
_token_fields = ('id', 'tfs')
_nonterminal_fields = ('id', 'entity', 'score', 'start', 'end', 'daughters')
_all_fields = tuple(set(_terminal_fields).union(_nonterminal_fields))

class _UdfNodeBase(object):
    """
    Base class for UdfNodes and UdfTerminals.
    """
    def __str__(self):
        return self.to_udf(indent=None)

    # for some reason != is not the opposite of __eq__ by default...
    def __ne__(self, other):
        ne = self.__eq__(other)
        if ne is NotImplemented: return ne  # pass this one along
        return not ne

    def is_root(self):
        """
        Return True if the node is a root node. Note that this is a
        specific type of node, and not just the top node. By convention,
        a node is root if its *id* is `None`.
        """
        return isinstance(self, UdfNode) and self.id is None

    # serialization

    def to_udf(self, indent=1):
        """
        Encode the node and its descendants in the UDF format.
        """
        return _to_udf(self, indent, 1)

    def to_dict(self, fields=_all_fields):
        """
        Encode the node as a dictionary suitable for JSON serialization.
        """
        fields = set(fields)
        diff = fields.difference(_all_fields)
        if diff:
            raise ValueError(
                'Invalid field(s): {}'.format(', '.join(diff))
            )
        return _to_dict(self, fields)


def _to_udf(obj, indent, level):
    delim = ' ' if indent is None else '\n' + ' ' * indent * level
    if isinstance(obj, UdfNode):
        dtrs = [_to_udf(dtr, indent, level+1) for dtr in obj.daughters]
        dtrs = delim.join([''] + dtrs)  # empty first item to force indent
        if obj.id is None:
            return '({}{})'.format(obj.entity, dtrs)
        else:
            # :g for score makes -1.0 look like -1
            return '({} {} {:g} {} {}{})'.format(
                obj.id,
                obj.entity,
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


def _to_dict(obj, fields):
    d = {}
    if isinstance(obj, UdfNode):
        if 'entity' in fields: d['entity'] = obj.entity
        if obj.id is not None:
            if 'id' in fields: d['id'] = obj.id
            if 'score' in fields: d['score'] = obj.score
            if 'start' in fields: d['start'] = obj.start
            if 'end' in fields: d['end'] = obj.end
        dtrs = obj.daughters
        if dtrs:
            # terminals should always be single daughters
            if len(dtrs) == 1 and isinstance(dtrs[0], UdfTerminal):
                # merge terminal daughter info into current node
                d.update(_to_dict(dtrs[0], fields))
            else:
                d['daughters'] = [_to_dict(dtr, fields) for dtr in dtrs]
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
    Token data are not formally nodes, but do have an *id*. Most
    [UdfTerminal] nodes will only have one [UdfToken], but multiword
    entities (e.g. "ad hoc") will have more than one.
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


class UdfTerminal(namedtuple('UdfTerminal', _terminal_fields), _UdfNodeBase):
    """
    Terminal nodes in the Unified Derivation Format. The *form*
    field is always set, but *tokens* may be `None`.
    See: http://moin.delph-in.net/ItsdbDerivations
    """

    def __new__(cls, form, tokens=None):
        if tokens is None:
            tokens = []
        return super(UdfTerminal, cls).__new__(cls, form, tokens)

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


class UdfNode(namedtuple('UdfNode', _nonterminal_fields), _UdfNodeBase):
    """
    Normal (non-leaf) nodes in the Unified Derivation Format. Root nodes
    are just UdfNodes whose *id*, by convention, is `None`. The
    *daughters* list can composed of either UdfNodes or other objects
    (generally it should be uniformly one or the other). In the latter
    case, the UdfNode is a preterminal, and the daughters are terminal
    nodes.
    See: http://moin.delph-in.net/ItsdbDerivations
    """

    def __new__(cls, id, entity,
                score=None, start=None, end=None, daughters=None):
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
        return super(UdfNode, cls).__new__(
            cls, id, entity, score, start, end, daughters
        )

    def __repr__(self):
        return '<UdfNode object ({}) at {}>'.format(self.entity, id(self))

    def __eq__(self, other):
        """
        Two derivations are equal if their entities, tokenization, and
        daughters are the same. IDs and scores are irrelevant.
        """
        if not isinstance(other, UdfNode):
            return NotImplemented
        # Check attributes
        if self.entity != other.entity:
            return False
        if self.start != other.start or self.end != other.end:
            return False
        if len(self.daughters) != len(other.daughters):
            return False
        if any(a != b for a, b in zip(self.daughters, other.daughters)):
            return False
        # Return true if they're the same!
        return True

    # UDX extensions

    def is_head(self):
        """
        Return True if the node is a head, otherwise False. If the
        derivation is in the export (UDX) format, head entities will be
        prefixed with a caret (`^`). Note that in regular UDF, this
        function is meaningless.
        """
        return self.entity.startswith('^')

    def basic_entity(self):
        """
        Return the entity without the lexical type information. In the
        export (UDX) format, lexical types follow entities of
        preterminal nodes, joined by an at-sign (`@`). In regular UDF or
        non-preterminal nodes, this will just return the entity string.
        """
        return self.entity.split('@', 1)[0]

    def lexical_type(self):
        """
        Return the lexical type of a preterminal node. In export (UDX)
        format, lexical types follow entities of preterminal nodes,
        joined by an at-sign (`@`). In regular UDF or non-preterminal
        nodes, this will return None.
        """
        toks = self.entity.split('@', 1)
        if len(toks) == 2:
            return toks[-1]
        return None

class Derivation(UdfNode):
    """
    A class for reading, writing, and storing derivation trees. Objects
    of this class are UDF nodes.
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
                 score=None, start=None, end=None, daughters=None):
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
        Instantiate a Derivation from a standard string representation.
        See here for details: http://moin.delph-in.net/ItsdbDerivations

        This method accommodates both the normal UDF format and the
        UDX export format.
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
                        tokens=_udf_tokens(gd.get('tokens'))
                    )
                    stack[-1].daughters.append(term)
                elif match.group('id'):
                    gd = match.groupdict()
                    udf = UdfNode(gd['id'], gd['entity'], gd['score'],
                                  gd['start'], gd['end'])
                    stack.append(udf)
                elif match.group('root'):
                    udf = UdfNode(None, match.group('root'))
                    stack.append(udf)
        except (ValueError, AttributeError):
            raise ValueError('Invalid derivation: %s' % s)
        if stack or deriv is None:
            raise ValueError('Invalid derivation; possibly unbalanced '
                             'parentheses: %s' % s)
        return cls(*deriv)

    @classmethod
    def from_dict(cls, d):
        """
        Decode from a dictionary as from UdfNode.to_dict().
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

def _from_dict(d):
    if 'daughters' in d:
        return UdfNode(
            d.get('id'),
            d['entity'],
            score=d.get('score'),
            start=d.get('start'),
            end=d.get('end'),
            daughters=[_from_dict(dtr) for dtr in d['daughters']]
        )
    elif 'form' in d:
        return UdfNode(
            d.get('id'),
            d['entity'],
            score=d.get('score'),
            start=d.get('start'),
            end=d.get('end'),
            daughters=[UdfTerminal(
                form=d['form'],
                tokens=[UdfToken(t['id'], t['tfs'])
                        for t in d.get('tokens', [])]
            )]
        )
