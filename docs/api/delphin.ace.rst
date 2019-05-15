
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


   Exceptions
   ----------

   .. autoexception:: ACEProcessError
      :show-inheritance:


   ACE stdout Protocols
   --------------------

   PyDelphin communicates with ACE via its "stdout protocols", which
   are the ways ACE's outputs are encoded across its stdout
   stream. There are several protocols that ACE uses and that this
   module supports:

   - regular parsing
   - parsing with ACE's `--tsdb-stdout` option
   - transfer
   - regular generation
   - generation with ACE's `--tsdb-stdout` option

   When a user interacts with ACE via the classes and functions in
   this module, responses will be interpreted and wrapped in
   :class:`~delphin.interface.Response` objects, thus separating the
   user from the details of ACE's stdout protocols. Sometimes,
   however, the user will store or pipe ACE's output directly, such as
   when using the :command:`delphin convert` :ref:`command
   <convert-tutorial>` with :command:`ace` at the command line. Even
   though ACE outputs MRSs using the common :doc:`SimpleMRS
   <delphin.codecs.simplemrs>` format, additional content used in
   ACE's stdout protocols can complicate tasks such as format or
   represenation conversion. The user can provide some options to ACE
   (see http://moin.delph-in.net/AceOptions), such as :command:`-T`,
   to filter the non-MRS content, but for convenience PyDelphin also
   provides the `ace` :doc:`codec <delphin.codecs>`, available at
   :mod:`delphin.codecs.ace`. The codec ignores the non-MRS content in
   ACE's stdout so the user can use ACE output as a stream or as a
   corpus of MRS representations. For example::

     $ ace -g erg.dat < sentences.txt | delphin convert --from ace

   The codec does not support every stdout protocol that this module
   does. Those it does support are:

   - regular parsing
   - parsing with ACE's `--tsdb-stdout` option
   - generation with ACE's `--tsdb-stdout` option
