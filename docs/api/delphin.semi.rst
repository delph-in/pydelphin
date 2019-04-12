
delphin.semi
============

.. automodule:: delphin.semi

  Loading a SEM-I from a File
  ---------------------------

  .. autofunction:: load

  The SemI Class
  --------------

  .. autoclass:: SemI

    The data in the SEM-I can be directly inspected via the
    :attr:`variables`, :attr:`properties`, :attr:`roles`,
    :attr:`predicates`, and :attr:`type_hierarchy` attributes:

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
    ...     print(', '.join('{0.name} {0.value}'.format(roledata) for roledata in synopsis))
    ... 
    ARG0 e, ARG1 i, ARG2 p
    >>> smi.predicates.descendants('some_q')
    ['_another_q', '_many+a_q', '_an+additional_q', '_what+a_q', '_such+a_q', '_some_q_indiv', '_some_q', '_a_q']

    Note that the variables, properties, and predicates are
    :class:`~delphin.tfs.TypeHierarchy` objects.

    .. automethod:: find_synopsis

    The :func:`load` module function is used to read the regular
    file-based SEM-I definitions, but there is also a dictionary
    representation which may be useful for, e.g., an HTTP API that
    makes use of SEM-Is.

    .. automethod:: from_dict
    .. automethod:: to_dict

  .. autoclass:: SynopsisRole

  Exceptions
  ----------

  .. autoclass:: SemIError
    :show-inheritance:
