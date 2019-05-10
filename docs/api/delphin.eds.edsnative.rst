
delphin.eds.edsnative
=====================

.. automodule:: delphin.eds.edsnative

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

   .. function:: dump(ms, destination, properties=True, lnk=True, show_status=False, indent=False, encoding='utf-8')

      See the :func:`dump` codec API documentation.

      **Extensions:**

      :param bool show_status: if `True`, indicate disconnected
                               components

   .. function:: dumps(ms, properties=True, lnk=True, show_status=False, indent=False, encoding='utf-8')

      See the :func:`dumps` codec API documentation.

      **Extensions:**

      :param bool show_status: if `True`, indicate disconnected
                               components

   .. function:: encode(m, properties=True, lnk=True, show_status=False, indent=False, encoding='utf-8')

      See the :func:`encode` codec API documentation.

      **Extensions:**

      :param bool show_status: if `True`, indicate disconnected
                               components
