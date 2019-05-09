
delphin.mrs.indexedmrs
======================

.. automodule:: delphin.mrs.indexedmrs

   .. seealso::

      :doc:`../tutorials/codecs` for a description of the API.

   Codec API Functions
   -------------------

   For the following functions, the additional `semi` argument is an
   instance of :class:`delphin.semi.SemI`.

   .. function:: load(source, semi)
   .. function:: loads(s, semi)
   .. function:: decode(s, semi)
   .. function:: dump(ms, destination, semi, properties=True, lnk=True, indent=False, encoding='utf-8')
   .. function:: dumps(ms, semi, properties=True, lnk=True, indent=False, encoding='utf-8')
   .. function:: encode(m, semi, properties=True, lnk=True, indent=False, encoding='utf-8')
