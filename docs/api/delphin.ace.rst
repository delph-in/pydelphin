
delphin.ace
===========

.. seealso::

   See :doc:`../guides/ace` for a more user-friendly introduction.

.. automodule:: delphin.ace

   This module provides classes and functions for managing interactive
   communication with an open `ACE
   <http://sweaglesw.org/linguistics/ace/>`_ process.  The ACE
   software is required for the functionality in this module, but it
   is not included with PyDelphin. Pre-compiled binaries are available
   for Linux and MacOS at http://sweaglesw.org/linguistics/ace/, and
   for installation instructions see
   http://moin.delph-in.net/AceInstall.

   The :class:`ACEParser`, :class:`ACETransferer`, and
   :class:`ACEGenerator` classes are used for parsing, transferring, and
   generating with ACE. All are subclasses of :class:`ACEProcess`, which
   connects to ACE in the background, sends it data via its stdin, and
   receives responses via its stdout. Responses from ACE are interpreted
   so the data is more accessible in Python.

   .. warning::

      Instantiating :class:`ACEParser`, :class:`ACETransferer`, or
      :class:`ACEGenerator` opens ACE in a subprocess, so take care to
      close the process (:meth:`ACEProcess.close`) when finished or,
      preferably, instantiate the class in a context manager so it is
      closed automatically when the relevant code has finished.

   Interpreted responses are stored in a dictionary-like
   :class:`~delphin.interface.Response` object. When queried as a
   dictionary, these objects return the raw response strings. When
   queried via its methods, the PyDelphin models of the data are
   returned.  The response objects may contain a number of
   :class:`~delphin.interface.Result` objects. These objects similarly
   provide raw-string access via dictionary keys and PyDelphin-model
   access via methods. Here is an example of parsing a sentence with
   :class:`ACEParser`:

   >>> from delphin import ace
   >>> with ace.ACEParser('erg-2018-x86-64-0.9.30.dat') as parser:
   ...     response = parser.interact('A cat sleeps.')
   ...     print(response.result(0)['mrs'])
   ...     print(response.result(0).mrs())
   ... 
   [ LTOP: h0 INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ] RELS: < [ _a_q<0:1> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: sg IND: + ] RSTR: h5 BODY: h6 ]  [ _cat_n_1<2:5> LBL: h7 ARG0: x3 ]  [ _sleep_v_1<6:13> LBL: h1 ARG0: e2 ARG1: x3 ] > HCONS: < h0 qeq h1 h5 qeq h7 > ICONS: < > ]
   <MRS object (_a_q _cat_n_1 _sleep_v_1) at 140612036960072>

   Functions exist for non-interactive communication with ACE:
   :func:`parse` and :func:`parse_from_iterable` open and close an
   :class:`ACEParser` instance; :func:`transfer` and
   :func:`transfer_from_iterable` open and close an
   :class:`ACETransferer` instance; and :func:`generate` and
   :func:`generate_from_iterable` open and close an
   :class:`ACEGenerator` instance. Note that these functions open a
   new ACE subprocess every time they are called, so if you have many
   items to process, it is more efficient to use
   :func:`parse_from_iterable`, :func:`transfer_from_iterable`, or
   :func:`generate_from_iterable` than the single-item versions, or to
   interact with the :class:`ACEProcess` subclass instances directly.

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
   as they handle the input and then close the ACE process, but for
   more complicated or interactive jobs, directly interacting with an
   instance of an :class:`ACEProcess` sublass is recommended or
   required (e.g., in the case of `[incr tsdb()] testsuite processing
   <Processing Testsuites with ACE>`_). The :class:`ACEProcess` class
   is where most methods are defined, but in practice the
   :class:`ACEParser`, :class:`ACETransferer`, or
   :class:`ACEGenerator` subclasses are directly used.

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
   - parsing with `--tsdb-stdout` and `--itsdb-forest`
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
   corpus of MRS representations. For example:

   .. code-block:: console

      [~]$ ace -g erg.dat < sentences.txt | delphin convert --from ace

   The codec does not support every stdout protocol that this module
   does. Those it does support are:

   - regular parsing
   - parsing with ACE's `--tsdb-stdout` option
   - generation with ACE's `--tsdb-stdout` option
