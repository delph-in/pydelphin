
delphin.mrs
===========

.. automodule:: delphin.mrs

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
      :members:

   .. autoclass:: EP
      :members:

   .. autoclass:: HCons
      :members:

   .. autoclass:: ICons
      :members:

   Exceptions
   ----------

   .. autoexception:: MRSSyntaxError
      :show-inheritance:

   Serialization Formats
   ---------------------

   .. toctree::

      delphin.mrs.indexedmrs.rst
      delphin.mrs.mrsjson.rst
      delphin.mrs.mrsprolog.rst
      delphin.mrs.mrx.rst
      delphin.mrs.simplemrs.rst
