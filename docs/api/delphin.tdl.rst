
delphin.tdl
===========

.. sidebar:: Contents

  .. contents::
    :local:
    :depth: 2


.. automodule:: delphin.tdl

Type Description Language (TDL) is a declarative language for
describing type systems, mainly for the creation of DELPH-IN HPSG
grammars. TDL was originally described in Krieger and Schäfer, 1994
[KS1994]_, but it describes many features not in use by the DELPH-IN
variant, such as disjunction. Copestake, 2002 [COP2002]_ better
describes the subset in use by DELPH-IN, but this publication has
become outdated to the current usage of TDL in DELPH-IN grammars and
its TDL syntax description is inaccurate in places. It is, however,
still a great resource for understanding the interpretation of TDL
grammar descriptions. The TdlRfc_ page of the `DELPH-IN Wiki`_
contains the most up-to-date description of the TDL syntax used by
DELPH-IN grammars, including features such as documentation strings
and regular expressions.

Below is an example of a basic type from the English Resource Grammar
(`ERG`_):

.. code:: tdl

   basic_word := word_or_infl_rule & word_or_punct_rule &
     [ SYNSEM [ PHON.ONSET.--TL #tl,
                LKEYS.KEYREL [ CFROM #from,
                               CTO #to ] ],
       ORTH [ CLASS #class, FROM #from, TO #to, FORM #form ],
       TOKENS [ +LIST #tl & < [ +CLASS #class, +FROM #from, +FORM #form ], ... >,
                +LAST.+TO #to ] ].

The `delphin.tdl` module makes it easy to inspect what is written on
definitions in Type Description Language (TDL), but it doesn't
interpret type hierarchies (such as by performing unification,
subsumption calculations, or creating GLB types). That is, while it
wouldn't be useful for creating a parser, it is useful if you want to
statically inspect the types in a grammar and the constraints they
apply.

.. [KS1994] Hans-Ulrich Krieger and Ulrich Schäfer.  TDL: a type
  description language for constraint-based grammars. In Proceedings
  of the 15th conference on Computational linguistics, volume 2, pages
  893–899. Association for Computational Linguistics, 1994.

.. [COP2002] Ann Copestake. Implementing typed feature structure
  grammars, volume 110. CSLI publications Stanford, 2002.

.. _TdlRfc: http://moin.delph-in.net/TdlRfc
.. _`DELPH-IN Wiki`: http://moin.delph-in.net/
.. _ERG: http://www.delph-in.net/erg/


Module Parameters
-----------------

Some aspects of TDL parsing can be customized per grammar, and the
following module variables may be reassigned to accommodate those
differences. For instance, in the ERG_, the type used for list
feature structures is `*list*`, while for Matrix_\ -based grammars
it is `list`. PyDelphin defaults to the values used by the ERG.

.. _ERG: http://www.delph-in.net/erg/
.. _Matrix: http://matrix.ling.washington.edu/

.. autodata:: LIST_TYPE
.. autodata:: EMPTY_LIST_TYPE
.. autodata:: LIST_HEAD
.. autodata:: LIST_TAIL
.. autodata:: DIFF_LIST_LIST
.. autodata:: DIFF_LIST_LAST


Functions
---------

.. autofunction:: iterparse
.. autofunction:: format


Classes
-------

The TDL entity classes are the objects returned by
:func:`iterparse`, but they may also be used directly to build TDL
structures, e.g., for serialization.


Terms
'''''

.. autoclass:: Term
.. autoclass:: TypeTerm
  :show-inheritance:
.. autoclass:: TypeIdentifier
  :show-inheritance:
  :members:
.. autoclass:: String
  :show-inheritance:
  :members:
.. autoclass:: Regex
  :show-inheritance:
  :members:
.. autoclass:: AVM
  :show-inheritance:
  :members:
.. autoclass:: ConsList
  :show-inheritance:
  :members:
.. autoclass:: DiffList
  :show-inheritance:
  :members:
.. autoclass:: Coreference
  :show-inheritance:
  :members:


Conjunctions
''''''''''''

.. autoclass:: Conjunction
  :members:


Type and Instance Definitions
'''''''''''''''''''''''''''''

.. autoclass:: TypeDefinition
  :members:
.. autoclass:: TypeAddendum
  :show-inheritance:
  :members:
.. autoclass:: LexicalRuleDefinition
  :show-inheritance:
  :members:


Morphological Patterns
''''''''''''''''''''''

.. autoclass:: LetterSet
  :members:

.. autoclass:: WildCard
  :members:


Environments and File Inclusion
'''''''''''''''''''''''''''''''

.. autoclass:: TypeEnvironment
   :members:

.. autoclass:: InstanceEnvironment
   :members:

.. autoclass:: FileInclude
   :members:


Exceptions and Warnings
-----------------------

.. autoexception:: TDLError
   :show-inheritance:

.. autoexception:: TDLSyntaxError
   :show-inheritance:

.. autoexception:: TDLWarning
   :show-inheritance:
