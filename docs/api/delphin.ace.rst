
delphin.ace
===========

.. seealso::

   See :doc:`../guides/ace` for a more user-friendly introduction.

.. automodule:: delphin.ace

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

   When interacting with ACE via the classes and functions in this
   module, responses will be interpreted and wrapped in
   :class:`~delphin.interface.Response` objects, thus separating the
   user from the details of ACE's stdout protocols. Sometimes,
   however, the user will store or pipe ACE's output directly, such as
   when using the :command:`delphin convert` :ref:`command
   <convert-tutorial>` with :command:`ace` at the command line.  Even
   though ACE outputs MRSs using the common :doc:`SimpleMRS
   <delphin.mrs.simplemrs>` format, additional content used in ACE's
   stdout protocols can complicate tasks such as format or
   represenation conversion. The user can provide some options to ACE
   (see http://moin.delph-in.net/AceOptions), such as :command:`-T`,
   to filter the non-MRS content, but for convenience this module also
   provides MRS deserialization functions using the common :ref:`codec
   API <codec-API>`. These functions ignore the non-MRS content so the
   user can use ACE output as a stream or corpus of MRS
   representations. For the :command:`delphin convert` command, this
   codec is named `ace`. For example::

     $ ace -g erg.dat < sentences.txt | delphin convert --from ace

   The functions are able to accommodate the normal and [incr tsdb()]
   protocols (the latter using the `--tsdb-stdout` option on
   :command:`ace`) for parsing and the [incr tsdb()] protocol for
   generation. The non-[incr tsdb()] protocols for generation and
   transfer, however, are not supported by these functions.

   .. seealso::

      :doc:`../guides/codecs` for a description of the API.


   .. function:: load(source)

      See the :func:`load` codec API documentation.

   .. function:: loads(s)

      See the :func:`loads` codec API documentation.

   .. function:: decode(s)

      See the :func:`decode` codec API documentation.


   Exceptions
   ----------

   .. autoexception:: ACEProcessError
      :show-inheritance:
