
delphin.derivation
==================

.. automodule:: delphin.derivation

  Loading Derivation Data
  -----------------------

  For loading a full derivation structure from either the UDF/UDX
  string representations or the dictionary representation, the
  :class:`Derivation` class provides class methods to help with the
  decoding.

  >>> from delphin import derivation
  >>> d1 = derivation.Derivation.from_string(
  ...     '(1 entity-name 1 0 1 ("token"))')
  ... 
  >>> d2 = derivation.Derivation.from_dict(
  ...     {'id': 1, 'entity': 'entity-name', 'score': 1,
  ...      'start': 0, 'end': 1, 'form': 'token'}]})
  ... 
  >>> d1 == d2
  True

  .. autoclass:: Derivation
    :show-inheritance:
    :members:

  UDF/UDX Node Types
  ------------------

  There are three different node Types

  .. autoclass:: UDFNode(id, entity, score=None, start=None, end=None, daughters=None, head=None, type=None, parent=None)
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

  .. autoclass:: UDFTerminal(form, tokens=None, parent=None)
    :members:

    .. py:attribute:: form

       the surface form of the terminal

    .. py:attribute:: tokens

       the list of tokens

    .. automethod:: is_root
    .. automethod:: to_udf
    .. automethod:: to_udx
    .. automethod:: to_dict

  .. autoclass:: UDFToken(id, tfs)
    :members:

    .. py:attribute:: id

       the token identifier

    .. py:attribute:: form

       the feature structure for the token
