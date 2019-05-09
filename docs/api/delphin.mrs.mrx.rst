
delphin.mrs.mrx
===============

.. automodule:: delphin.mrs.mrx

   .. seealso::

      :doc:`../tutorials/codecs` for a description of the API.

   Module Constants
   ----------------

   .. data:: HEADER

      `'<mrs-list>'`

   .. data:: JOINER

      `''`

   .. data:: FOOTER

      `'</mrs-list>'`

   Codec API Functions
   -------------------

   .. function:: load(source)
   .. function:: loads(s)
   .. function:: decode(s)
   .. function:: dump(ms, destination, properties=True, lnk=True, indent=False, encoding='utf-8')
   .. function:: dumps(ms, properties=True, lnk=True, indent=False, encoding='utf-8')
   .. function:: encode(m, properties=True, lnk=True, indent=False, encoding='utf-8')
