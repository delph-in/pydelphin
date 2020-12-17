
delphin.eds
===========

.. automodule:: delphin.eds

   Serialization Formats
   ---------------------

   .. toctree::
      :maxdepth: 1

      delphin.codecs.edsjson.rst
      delphin.codecs.eds.rst
      delphin.codecs.edspenman.rst

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
      :show-inheritance:
      :members:

   .. autoclass:: Node
      :show-inheritance:
      :members:

   Module Functions
   ----------------

   .. autofunction:: from_mrs
   .. autofunction:: find_predicate_modifiers
   .. autofunction:: make_ids_unique

   Exceptions
   ----------

   .. autoexception:: EDSError
      :show-inheritance:

   .. autoexception:: EDSSyntaxError
      :show-inheritance:

   .. autoexception:: EDSWarning
      :show-inheritance:
