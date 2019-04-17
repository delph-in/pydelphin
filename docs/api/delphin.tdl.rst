
delphin.tdl
===========

.. sidebar:: Contents

  .. contents::
    :local:
    :depth: 2


.. automodule:: delphin.tdl

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

  Exceptions and Warnings
  -----------------------

  .. autoexception:: TDLError
     :show-inheritance:

  .. autoexception:: TDLSyntaxError
     :show-inheritance:

  .. autoexception:: TDLWarning
     :show-inheritance:
