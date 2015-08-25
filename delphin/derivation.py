# coding: utf-8

"""
Classes and functions related to Derivation trees.
see here: http://moin.delph-in.net/ItsdbDerivations

Here's an example from Jacy for:

    遠く    に  銃声    が  聞こえ た 。
    tooku   ni  juusei  ga  kikoe-ta
    distant LOC gunshot NOM can.hear-PFV
    "Shots were heard in the distance."

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
    by that subtree; the content of leaf nodes is open-ended

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


class UdfNode(
    namedtuple('UdfNode',
               ('id', 'entity', 'score', 'start', 'end', 'daughters'))):
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
        for dtr in daughters:
            if isinstance(dtr, UdfNode) and dtr.id is None:
                raise ValueError(
                    'Daughter nodes cannot be roots (with id=None).'
                )
        return super(UdfNode, cls).__new__(
            cls, id, entity, score, start, end, daughters
        )

    def __repr__(self):
        return '<UdfNode object ({}) at {}>'.format(self.entity, id(self))

    def __str__(self):
        dtrs = []
        for dtr in self.daughters:
            if isinstance(dtr, UdfNode):
                dtrs.append(str(dtr))
            else:
                # terminal (i.e. token) node
                dtrs.append('({})'.format(' '.join(str(x) for x in dtr)))
        dtrs = ' '.join(dtrs)
        if self.id is None:
            return '({} {})'.format(self.entity, dtrs)
        else:
            # :g for score makes -1.0 look like -1
            return '({} {} {:g} {} {} {})'.format(
                self.id,
                self.entity,
                self.score,
                self.start,
                self.end,
                dtrs
            )

    def __eq__(self, other):
        """
        Two derivations are equal if their entities, tokenization, and
        daughters are the same. IDs and scores are irrelevant. Note that
        edge IDs appearing in leaf nodes are considered, because the
        formatting of leaf nodes is fairly open.
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
        return self.id is None

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
            # root symbol
            r'\s*(?P<root>{token})\s*\('
            # regular node
            r'|\s*(?P<id>{token})\s+(?P<entity>{string}|{token})'
            r'\s+(?P<score>{token})\s+(?P<start>{token})'
            r'\s+(?P<end>{token})\s*\('
            # branch end
            r'|\s*(?P<done>\))'
            # terminal node (lexical token info; unbound list)
            r'|\s*(?P<tokens>(?:{string}|{token}|\s+)*)\s*\)'
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
                elif match.group('tokens'):
                    if len(stack) == 0:
                        raise ValueError('Possible leaf node with no parent.')
                    tokens = tuple(re.findall(
                        r'{string}|{token}'
                        .format(string=r'"[^"\\]*(?:\\.[^"\\]*)*"',
                                token=r'[^\s()]+'),
                        match.group('tokens')
                    ))
                    stack[-1].daughters.append(tokens)
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
        return deriv
