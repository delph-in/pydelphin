
delphin.mrs.indexedmrs
======================

.. automodule:: delphin.mrs.indexedmrs

   Deserialization Functions
   -------------------------

   .. function:: load(source, semi)

      See the :func:`load` codec API documentation.

      **Extensions:**

      :param SemI semi: the semantic interface for the grammar
			that produced the MRS

   .. function:: loads(s, semi)

      See the :func:`loads` codec API documentation.

      **Extensions:**

      :param SemI semi: the semantic interface for the grammar
			that produced the MRS

   .. function:: decode(s, semi)

      See the :func:`decode` codec API documentation.

      **Extensions:**

      :param SemI semi: the semantic interface for the grammar
			that produced the MRS

   Serialization Functions
   -----------------------

   .. function:: dump(ms, destination, semi, properties=True, lnk=True, indent=False, encoding='utf-8')

      See the :func:`dump` codec API documentation.

      **Extensions:**

      :param SemI semi: the semantic interface for the grammar
			that produced the MRS

   .. function:: dumps(ms, semi, properties=True, lnk=True, indent=False, encoding='utf-8')

      See the :func:`dumps` codec API documentation.

      **Extensions:**

      :param SemI semi: the semantic interface for the grammar
			that produced the MRS

   .. function:: encode(m, semi, properties=True, lnk=True, indent=False, encoding='utf-8')

      See the :func:`encode` codec API documentation.

      **Extensions:**

      :param SemI semi: the semantic interface for the grammar
			that produced the MRS
