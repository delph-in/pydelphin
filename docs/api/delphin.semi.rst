
delphin.semi
============

.. automodule:: delphin.semi

   Semantic interfaces (SEM-Is) describe the inventory of semantic
   components in a grammar, including variables, properties, roles,
   and predicates. This information can be used for validating
   semantic structures or for filling out missing information in
   incomplete representations.

   .. seealso::
      The following DELPH-IN wikis contain more information:

      - Technical specifications: http://moin.delph-in.net/SemiRfc
      - Overview and usage: http://moin.delph-in.net/RmrsSemi


   Loading a SEM-I from a File
   ---------------------------

   The :func:`load` module function is used to read the regular
   file-based SEM-I definitions, but there is also a dictionary
   representation which may be useful for JSON serialization, e.g.,
   for an HTTP API that makes use of SEM-Is. See
   :meth:`SemI.to_dict()` for the later.

   .. autofunction:: load


   The SemI Class
   --------------

   The main class modeling a semantic interface is :class:`SemI`. The
   predicate synopses have enough complexity that two more subclasses
   are used to make inspection easier: :class:`Synopsis` contains the
   role information for an individual predicate synopsis, and each role
   is modeled with a :class:`SynopsisRole` class.

   .. autoclass:: SemI

      The data in the SEM-I can be directly inspected via the
      :attr:`variables`, :attr:`properties`, :attr:`roles`, and
      :attr:`predicates` attributes.

      >>> smi = semi.load('../grammars/erg/etc/erg.smi')
      >>> smi.variables['e']
      <delphin.tfs.TypeHierarchyNode object at 0x7fa02f877388>
      >>> smi.variables['e'].parents
      ['i']
      >>> smi.variables['e'].data
      [('SF', 'sf'), ('TENSE', 'tense'), ('MOOD', 'mood'), ('PROG', 'bool'), ('PERF', 'bool')]
      >>> 'sf' in smi.properties
      True
      >>> smi.roles['ARG0']
      'i'
      >>> for synopsis in smi.predicates['can_able'].data:
      ...     print(', '.join('{0.name} {0.value}'.format(roledata)
      ...                     for roledata in synopsis))
      ... 
      ARG0 e, ARG1 i, ARG2 p
      >>> smi.predicates.descendants('some_q')
      ['_another_q', '_many+a_q', '_an+additional_q', '_what+a_q', '_such+a_q', '_some_q_indiv', '_some_q', '_a_q']

      Note that the variables, properties, and predicates are
      :class:`~delphin.tfs.TypeHierarchy` objects.

      .. automethod:: find_synopsis
      .. automethod:: from_dict
      .. automethod:: to_dict

   .. autoclass:: Synopsis(roles)
      :members:

   .. autoclass:: SynopsisRole(name, value, properties=None, optional=False)


   Exceptions and Warnings
   -----------------------

   .. autoexception:: SemIError
     :show-inheritance:

   .. autoexception:: SemISyntaxError
     :show-inheritance:

   .. autoexception:: SemIWarning
     :show-inheritance:
