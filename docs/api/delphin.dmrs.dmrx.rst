
delphin.dmrs.dmrx
=================

.. automodule:: delphin.dmrs.dmrx

   .. seealso::

      :doc:`../tutorials/codecs` for a description of the API.

   Module Constants
   ----------------

   .. data:: HEADER

      `'<dmrs-list>'`

   .. data:: JOINER

      `''`

   .. data:: FOOTER

      `'</dmrs-list>'`

   Codec API Functions
   -------------------

   .. function:: load(source)
   .. function:: loads(s)
   .. function:: decode(s)
   .. function:: dump(ms, destination, properties=True, lnk=True, indent=False, encoding='utf-8')
   .. function:: dumps(ms, properties=True, lnk=True, indent=False, encoding='utf-8')
   .. function:: encode(m, properties=True, lnk=True, indent=False, encoding='utf-8')
