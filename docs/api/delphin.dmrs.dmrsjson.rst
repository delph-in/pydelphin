
delphin.dmrs.dmrsjson
=====================

.. automodule:: delphin.dmrs.dmrsjson

   Module Constants
   ----------------

   .. data:: HEADER

      `'['`

   .. data:: JOINER

      `','`

   .. data:: FOOTER

      `']'`

   Deserialization Functions
   -------------------------

   .. function:: load(source)

      See the :func:`load` codec API documentation.

   .. function:: loads(s)

      See the :func:`loads` codec API documentation.

   .. function:: decode(s)

      See the :func:`decode` codec API documentation.

   Serialization Functions
   -----------------------

   .. function:: dump(ms, destination, properties=True, lnk=True, indent=False, encoding='utf-8')

      See the :func:`dump` codec API documentation.

   .. function:: dumps(ms, properties=True, lnk=True, indent=False, encoding='utf-8')

      See the :func:`dumps` codec API documentation.

   .. function:: encode(m, properties=True, lnk=True, indent=False, encoding='utf-8')

      See the :func:`encode` codec API documentation.

   Complementary Functions
   -----------------------

   .. autofunction:: from_dict
   .. autofunction:: to_dict
