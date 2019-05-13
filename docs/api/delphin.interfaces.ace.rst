
delphin.interfaces.ace
======================

.. seealso::

   See :doc:`../guides/ace` for a more user-friendly introduction.

.. automodule:: delphin.interfaces.ace

   Basic Usage
   -----------

   The following module funtions are the simplest way to interact with
   ACE, although for larger or more interactive jobs it is suggested to
   use an :class:`ACEProcess` subclass instance.

   .. autofunction:: compile
   .. autofunction:: parse
   .. autofunction:: parse_from_iterable
   .. autofunction:: transfer
   .. autofunction:: transfer_from_iterable
   .. autofunction:: generate
   .. autofunction:: generate_from_iterable


   Classes for Managing ACE Processes
   ----------------------------------

   The functions described in `Basic Usage`_ are useful for small jobs
   as they handle the input and then close the ACE process, but for more
   complicated or interactive jobs, directly interacting with an
   instance of an :class:`ACEProcess` sublass is recommended or required
   (e.g., in the case of `[incr tsdb()] testsuite processing <Processing
   Testsuites with ACE>`_). The :class:`ACEProcess` class is where most
   methods are defined, but in practice the :class:`ACEParser`,
   :class:`ACETransferer`, or :class:`ACEGenerator` subclasses are
   directly used.

   .. autoclass:: ACEProcess
     :show-inheritance:
     :members:

   .. autoclass:: ACEParser
     :show-inheritance:
     :members:

   .. autoclass:: ACETransferer
     :show-inheritance:
     :members:

   .. autoclass:: ACEGenerator
     :show-inheritance:
     :members:

   Codec API Functions
   -------------------

   .. seealso::

      :doc:`../guides/codecs` for a description of the API.


   .. function:: load(source)
   .. function:: loads(s)
   .. function:: decode(s)


   Exceptions
   ----------

   .. autoexception:: ACEProcessError
      :show-inheritance:
