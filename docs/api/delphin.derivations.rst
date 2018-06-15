
delphin.derivation
==================

.. automodule:: delphin.derivation

  Loading Derivation Data
  -----------------------

  .. autoclass:: Derivation
    :show-inheritance:
    :members:

  UDF/UDX Node Types
  ------------------

  .. autoclass:: UdfNode
    :members:

    .. py:attribute:: id

       the unique node identifier

    .. py:attribute:: entity

       the grammar entity represented by the node

    .. py:attribute:: score

       the probability or weight of to the node; for many processors,
       this will be the unnormalized MaxEnt score assigned to the whole
       subtree rooted by this node

    .. py:attribute:: start

       the start position (in inter-word, or chart, indices) of the
       substring encompassed by this node and its daughters

    .. py:attribute:: end

       the end position (in inter-word, or chart, indices) of the
       substring encompassed by this node and its daughters

    .. py:attribute:: type

       the lexical type (available on preterminal UDX nodes)

    .. automethod:: is_root
    .. automethod:: to_udf
    .. automethod:: to_udx
    .. automethod:: to_dict

  .. autoclass:: UdfTerminal
    :members:

    .. py:attribute:: form

       the surface form of the terminal

    .. py:attribute:: tokens

       the list of tokens

    .. automethod:: is_root
    .. automethod:: to_udf
    .. automethod:: to_udx
    .. automethod:: to_dict

  .. autoclass:: UdfToken
    :members:

    .. py:attribute:: id

       the token identifier

    .. py:attribute:: form

       the feature structure for the token
