
delphin.mrs.interfaces.ace
==========================

.. seealso::

  the :doc:`ACE tutorial <../tutorials/ace>` for a more user-friendly introduction

.. automodule:: delphin.interfaces.ace

  Basic Usage
  -----------

  The following module funtions are the simplest way to interact with
  ACE, although for larger or more interactive jobs it is suggested to
  use an :class:`AceProcess` subclass instance.

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
  instance of an :class:`AceProcess` sublass is recommended or required
  (e.g., in the case of `[incr tsdb()] testsuite processing <Processing
  Testsuites with ACE>`_). The :class:`AceProcess` class is where most
  methods are defined, but in practice the :class:`AceParser`,
  :class:`AceTransferer`, or :class:`AceGenerator` subclasses are
  directly used.

  .. autoclass:: AceProcess
    :members:

  .. autoclass:: AceParser
    :show-inheritance:
    :members:

  .. autoclass:: AceTransferer
    :show-inheritance:
    :members:

  .. autoclass:: AceGenerator
    :show-inheritance:
    :members:
