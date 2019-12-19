
delphin.derivation
==================

.. automodule:: delphin.derivation

   Derivation trees represent a unique analysis of an input using an
   implemented grammar. They are a kind of syntax tree, but as they
   use the actual grammar entities (e.g., rules or lexical entries) as
   node labels, they are more specific than trees using general
   category labels (e.g., "N" or "VP"). As such, they are more likely
   to change across grammar versions.

   .. seealso::
      More information about derivation trees is found at
      http://moin.delph-in.net/ItsdbDerivations

   For the following Japanese example...

   ::

     遠く    に  銃声    が  聞こえ た 。
     tooku   ni  juusei  ga  kikoe-ta
     distant LOC gunshot NOM can.hear-PFV
     "Shots were heard in the distance."

   ... here is the derivation tree of a parse from `Jacy
   <http://moin.delph-in.net/JacyTop>`_ in the Unified Derivation
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
   "UDX", which adds lexical type information and indicates which
   daughter node is the head, and a dictionary representation, which
   is useful for JSON serialization. All three are supported by
   PyDelphin.

   Derivation trees have 3 types of nodes:

   * **root nodes**, with only an entity name and a single child

   * **normal nodes**, with 5 fields (below) and a list of children

     - *id* -- an integer id given by the producer of the derivation
     - *entity* -- rule or type name
     - *score* -- a (MaxEnt) score for the current node's subtree
     - *start* -- the character index of the left-most side of the tree
     - *end* -- the character index of the right-most side of the tree

   * **terminal/left/lexical nodes**, which contain the input tokens
     processed by that subtree

   This module uses the :class:`UDFNode` class for capturing root and
   normal nodes. Root nodes are expressed as a :class:`UDFNode` whose
   `id` is `None`. For root nodes, all fields except `entity` and the
   list of daughters are expected to be `None`. Leaf nodes are simply
   an iterable of token information.

   Loading Derivation Data
   -----------------------

   There are two functions for loading derivations from either the
   UDF/UDX string representation or the dictionary representation:
   :func:`from_string` and :func:`from_dict`.

   >>> from delphin import derivation
   >>> d1 = derivation.from_string(
   ...     '(1 entity-name 1 0 1 ("token"))')
   ... 
   >>> d2 = derivation.from_dict(
   ...     {'id': 1, 'entity': 'entity-name', 'score': 1,
   ...      'start': 0, 'end': 1, 'form': 'token'}]})
   ... 
   >>> d1 == d2
   True

   .. autofunction:: from_string
   .. autofunction:: from_dict

   UDF/UDX Classes
   ---------------

   There are four classes for representing derivation trees. The
   :class:`Derivation` class is used to contain the entire tree, while
   :class:`UDFNode`, :class:`UDFTerminal`, and :class:`UDFToken`
   represent individual nodes.

   .. autoclass:: Derivation
      :show-inheritance:
      :members:

   .. autoclass:: UDFNode(id, entity, score=None, start=None, end=None, daughters=None, head=None, type=None, parent=None)

      .. py:attribute:: id

         The unique node identifier.

      .. py:attribute:: entity

         The grammar entity represented by the node.

      .. py:attribute:: score

         The probability or weight of to the node; for many
         processors, this will be the unnormalized MaxEnt score
         assigned to the whole subtree rooted by this node.

      .. py:attribute:: start

         The start position (in inter-word, or chart, indices) of the
         substring encompassed by this node and its daughters.

      .. py:attribute:: end

         The end position (in inter-word, or chart, indices) of the
         substring encompassed by this node and its daughters.

      .. py:attribute:: type

         The lexical type (available on preterminal UDX nodes).

      .. py:attribute:: parent

	 The parent node in the tree, or ``None`` for the root. Note
	 that this is not a regular UDF/UDX attribute but is added for
	 convenience in traversing the tree.

      .. automethod:: is_head
      .. automethod:: is_root
      .. automethod:: internals
      .. automethod:: preterminals
      .. automethod:: terminals
      .. automethod:: to_udf
      .. automethod:: to_udx
      .. automethod:: to_dict

   .. autoclass:: UDFTerminal(form, tokens=None, parent=None)

      .. py:attribute:: form

         The surface form of the terminal.

      .. py:attribute:: tokens

         The list of tokens.

      .. py:attribute:: parent

	 The parent node in the tree. Note that this is not a regular
	 UDF/UDX attribute but is added for convenience in traversing
	 the tree.

      .. automethod:: is_root
      .. automethod:: to_udf
      .. automethod:: to_udx
      .. automethod:: to_dict

   .. autoclass:: UDFToken(id, tfs)
      :members:

      .. py:attribute:: id

         The token identifier.

      .. py:attribute:: form

         The feature structure for the token.


   Exceptions
   ----------

   .. autoexception:: DerivationSyntaxError
      :show-inheritance:
