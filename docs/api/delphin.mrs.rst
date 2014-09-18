delphin.mrs package
===================

.. automodule:: delphin.mrs

Xmrs Objects
------------

.. autoclass:: delphin.mrs.xmrs.Xmrs
    :show-inheritance:
    :members:

\*MRS Component Classes
-----------------------

MrsVariable
^^^^^^^^^^^

.. autoclass:: delphin.mrs.components.MrsVariable
    :members:

AnchorMixin
^^^^^^^^^^^

.. autoclass:: delphin.mrs.components.AnchorMixin
    :members:

Lnk
^^^

.. autoclass:: delphin.mrs.components.Lnk
    :members:

LnkMixin
^^^^^^^^

.. autoclass:: delphin.mrs.components.LnkMixin
    :members:

Hook
^^^^

.. autoclass:: delphin.mrs.components.Hook
    :members:

Argument
^^^^^^^^

.. autoclass:: delphin.mrs.components.Argument
    :members:
    :show-inheritance:

Link
^^^^

.. autoclass:: delphin.mrs.components.Link
    :members:

HandleConstraint
^^^^^^^^^^^^^^^^

.. autoclass:: delphin.mrs.components.HandleConstraint

IndividualConstraint
^^^^^^^^^^^^^^^^^^^^

.. autoclass:: delphin.mrs.components.IndividualConstraint

Pred
^^^^

.. autoclass:: delphin.mrs.components.Pred
    :members:

Node
^^^^

.. autoclass:: delphin.mrs.components.Node
    :members:
    :show-inheritance:

ElementaryPredication
^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: delphin.mrs.components.ElementaryPredication
    :members:
    :show-inheritance:

Xmrs Constructor Functions
--------------------------

Mrs
^^^

.. autofunction:: delphin.mrs.Mrs

Rmrs
^^^^

.. autofunction:: delphin.mrs.Rmrs

Dmrs
^^^^

.. autofunction:: delphin.mrs.Dmrs

Serialization Formats
---------------------

The \*MRS serializer/deserializers all use the pickle API of `load()`,
`dump()`, `loads()`, and `dumps()`, which read and write *corpora* of
\*MRSs. Helper functions `load_one()`, `dump_one()`, `loads_one()`,
and `dumps_one()` read/write single |Xmrs| objects instead of lists
of them.

SimpleMRS
^^^^^^^^^

.. automodule:: delphin.mrs.simplemrs
    :members: load, loads, dump, dumps, load_one, loads_one, dump_one,
        dumps_one
    :undoc-members:
    :show-inheritance:
    
MRX
^^^

.. automodule:: delphin.mrs.mrx

The API is the same as :py:mod:`delphin.mrs.simplemrs`.

DMRX
^^^^

.. automodule:: delphin.mrs.dmrx

The API is the same as :py:mod:`delphin.mrs.simplemrs`.
