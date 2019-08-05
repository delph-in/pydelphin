
delphin.mrs
===========

.. automodule:: delphin.mrs

   Serialization Formats
   ---------------------

   .. toctree::
      :maxdepth: 1

      delphin.codecs.indexedmrs.rst
      delphin.codecs.mrsjson.rst
      delphin.codecs.mrsprolog.rst
      delphin.codecs.mrx.rst
      delphin.codecs.simplemrs.rst

   Module Constants
   ----------------

   .. data:: INTRINSIC_ROLE

      The `ARG0` role that is associated with the intrinsic variable
      (:data:`EP.iv`).

   .. data:: RESTRICTION_ROLE

      The `RSTR` role used to select the restriction of a quantifier.

   .. data:: BODY_ROLE

      The `BODY` role used to select the body of a quantifier.

   .. data:: CONSTANT_ROLE

      The `CARG` role used to encode the constant value
      (:data:`EP.carg`) associated with certain kinds of predications,
      such as named entities, numbers, etc.

   Classes
   -------

   .. autoclass:: MRS
      :show-inheritance:
      :members:

   .. autoclass:: EP
      :show-inheritance:
      :members:

   .. autoclass:: HCons
      :members:

   .. autoclass:: ICons
      :members:

   Module Functions
   ----------------

   .. autofunction:: is_connected
   .. autofunction:: has_intrinsic_variable_property
   .. autofunction:: has_complete_intrinsic_variables
   .. autofunction:: has_unique_intrinsic_variables
   .. autofunction:: is_well_formed
   .. autofunction:: plausibly_scopes
   .. autofunction:: is_isomorphic
   .. autofunction:: compare_bags
   .. autofunction:: from_dmrs

   Exceptions
   ----------

   .. autoexception:: MRSError
      :show-inheritance:

   .. autoexception:: MRSSyntaxError
      :show-inheritance:
