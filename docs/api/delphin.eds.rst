
delphin.eds
===========

.. automodule:: delphin.eds

   Module Constants
   ----------------

   .. data:: BOUND_VARIABLE_ROLE

      The `BV` role used in edges to select the identifier of the node
      restricted by the quantifier.

   .. data:: PREDICATE_MODIFIER_ROLE

      The `ARG1` role used as a default role when inserting edges for
      predicate modification.

   Classes
   -------

   .. autoclass:: EDS
      :members:

   .. autoclass:: Node
      :members:

   .. autoclass:: Edge
      :members:

   Exceptions
   ----------

   .. autoexception:: EDSSyntaxError

   Serialization Formats
   ---------------------

   .. toctree::

      delphin.eds.edsjson.rst
      delphin.eds.edsnative.rst
