
delphin.codecs
==============

Serialization Codecs for Semantic Representations

The `delphin.codecs` package is a `namespace package
<https://www.python.org/dev/peps/pep-0420>`_ for modules used in the
serialization and deserialization of semantic representations. All
modules included in this namespace must follow the common API (based
on Python's :py:mod:`pickle` and :py:mod:`json` modules) in order to
work correctly with PyDelphin. This document describes that API.

Included Codecs
---------------

MRS:

.. toctree::
   :maxdepth: 1

   delphin.codecs.simplemrs
   delphin.codecs.mrx
   delphin.codecs.indexedmrs
   delphin.codecs.mrsjson
   delphin.codecs.mrsprolog
   delphin.codecs.ace

DMRS:

.. toctree::
   :maxdepth: 1

   delphin.codecs.simpledmrs
   delphin.codecs.dmrx
   delphin.codecs.dmrsjson
   delphin.codecs.dmrspenman

EDS:

.. toctree::
   :maxdepth: 1

   delphin.codecs.eds
   delphin.codecs.edsjson
   delphin.codecs.edspenman


Codec API
---------

Module Constants
""""""""""""""""

There is one required module constant for codecs: `CODEC_INFO`. Its
purpose is primarily to specify which representation (MRS, DMRS, EDS)
it serializes. A codec without `CODEC_INFO` will work for programmatic
usage, but it will not work with the :func:`delphin.commands.convert`
function or at the command line with the :command:`delphin convert`
command, which use the `representation` key in `CODEC_INFO` to
determine when and how to convert representations.

.. data:: CODEC_INFO

   A dictionary containing information about the codec. While codec
   authors may put arbitrary data here, there are two keys used by
   PyDelphin's conversion features: `representation` and
   `description`. Only `representation` is required, and should be set
   to one of `mrs`, `dmrs`, or `eds`. For example, the `mrsjson` codec
   uses the following::

     CODEC_INFO = {
         'representation': 'mrs',
	 'description': 'JSON-serialized MRS for the Web API'
     }

The following module constants are optional and are used to describe
strings that must appear in valid documents when serializing multiple
semantics representations at a time, as with :func:`dump` and
:func:`dumps`. It is used by :func:`delphin.commands.convert` to
provide a streaming serialization rather than dumping the entire file
at once. If the values are not defined in the codec module, default
values will be used.

.. data:: HEADER

   The string to output before any of semantic representations are
   serialized. For example, in :mod:`delphin.codecs.mrx`, the value of
   `HEADER` is `<mrs-list>`, and in the `delphin.codecs.dmrstikz`
   module of the `delphin-latex
   <https://github.com/delph-in/delphin-latex>`_ plugin it is an
   entire LaTeX preamble followed by `\begin{document}`.

.. data:: JOINER

   The string used to join multiple serialized semantic
   representations. For example, in :mod:`delphin.codecs.mrsjson`, it is
   a comma (`,`) following JSON's syntax. Normally it is either an
   empty string, a space, or a newline, depending on the conventions
   for the format and if the `indent` argument is set.

.. data:: FOOTER

   The string to output after all semantic representations have been
   serialized. For example, in :mod:`delphin.codecs.mrx`, it is
   `</mrs-list>`, and in `delphin.codecs.dmrstikz` it is
   `\end{document}`.


Deserialization Functions
"""""""""""""""""""""""""

The deserialization functions :func:`load`, :func:`loads`, and
:func:`decode` accept textual serializations and return the
interpreted semantic representation. Both :func:`load` and
:func:`loads` expect full documents (including headers and footers,
such as `<mrs-list>` and `</mrs-list>` around a
:mod:`~delphin.codecs.mrx` serialization) and return lists of semantic
structure objects. The :func:`decode` function expects single
representations (without headers and footers) and returns a single
semantic structure object.

.. _codec-load:

Reading from a file or stream
'''''''''''''''''''''''''''''

.. function:: load(source)

   Deserialize and return semantic representations from *source*.

   :param source: `path-like object
      <https://docs.python.org/3/glossary.html#term-path-like-object>`_
      or file handle of a source containing serialized semantic
      representations

   :rtype: list

.. _codec-loads:

Reading from a string
'''''''''''''''''''''

.. function:: loads(s)

   Deserialize and return semantic representations from string *s*.

   :param s: string containing serialized semantic representations

   :rtype: list

.. _codec-decode:


Decoding from a string
''''''''''''''''''''''

.. function:: decode(s)

   Deserialize and return the semantic representation from string *s*.

   :param s: string containing a serialized semantic representation

   :rtype: subclass of :class:`delphin.sembase.SemanticStructure`



Serialization Functions
"""""""""""""""""""""""

The serialization functions :func:`dump`, :func:`dumps`, and
:func:`encode` take semantic representations as input as either return
a string or print to a file or stream. Both :func:`dump` and
:func:`dumps` will provide the appropriate :data:`HEADER`,
:data:`JOINER`, and :data:`FOOTER` values to make the result a valid
document. The :func:`encode` function only serializes a single
semantic representation, which is generally useful when working with
single representations, but is also useful when headers and footers
are not desired (e.g., if you want the :mod:`~delphin.codecs.dmrx`
representation of a DMRS without `<dmrs-list>` and `</dmrs-list>`
surrounding it).

.. _codec-dump:

Writing to a file or stream
'''''''''''''''''''''''''''

.. function:: dump(xs, destination, properties=True, lnk=True, indent=False, encoding='utf-8')

   Serialize semantic representations in *xs* to *destination*.

   :param xs: iterable of :class:`~delphin.sembase.SemanticStructure`
	      objects to serialize
   :param destination: `path-like object
      <https://docs.python.org/3/glossary.html#term-path-like-object>`_
      or file object where data will be written to
   :param bool properties: if `False`, suppress morphosemantic
                           properties
   :param bool lnk: if `False`, suppress surface alignments and
                    strings
   :param indent: if `True` or an integer value, add newlines and
                  indentation; some codecs may support an integer
                  value for `indent`, which specifies how many columns
                  to indent
   :param str encoding: if *destination* is a filename, write to the
                        file with the given encoding; otherwise it is
                        ignored

.. _codec-dumps:

Writing to a string
'''''''''''''''''''

.. function:: dumps(xs, properties=True, lnk=True, indent=False)

   Serialize semantic representations in *xs* and return the string.

   The arguments are interpreted as in :func:`dump`.

   :rtype: str

.. _codec-encode:

Encoding to a string
''''''''''''''''''''

.. function:: encode(x, properties=True, lnk=True, indent=False)

   Serialize single semantic representations *x* and return the string.

   The arguments are interpreted as in :func:`dump`.

   :rtype: str


Variations
""""""""""

All serialization codecs should use the function signatures above, but
some variations are possible. Codecs should not remove any positional
or keyword arguments from functions, but they can be ignored. If any
new positional arguments are added, they should appear after the last
positional argument in its function, before the keyword arguments. New
keyword arguments may be added in any order.  Finally, a codec may
omit some functions entirely, such as for export-only codecs that do
not provide :func:`load`, :func:`loads`, or :func:`decode`. The module
constants :data:`HEADER`, :data:`JOINER`, and :data:`FOOTER` are also
optional. Here are some examples of variations in PyDelphin:

* :mod:`delphin.codecs.indexedmrs` requires a `semi` positional argument.

* :mod:`delphin.codecs.mrsjson`, :mod:`delphin.codecs.dmrsjson`, and
  :mod:`delphin.codecs.edsjson` introduce `to_dict()` and `from_dict()`
  functions in their public API as they may be generally useful.

* :mod:`delphin.codecs.dmrspenman` and :mod:`delphin.codecs.edspenman`
  introduce `to_triples()` and `from_triples()` functions in their
  public API.

* :mod:`delphin.codecs.eds` allows a `show_status` keyword argument
  to turn on graph connectedness markers on serialization.

* :mod:`delphin.codecs.mrsprolog` and `delphin.codecs.dmrstikz`
  are export-only codecs and do not provide :func:`load`,
  :func:`loads`, or :func:`decode` functions.

* :mod:`delphin.ace` is an import-only codec and does not provide
  :func:`dump`, :func:`dumps`, or :func:`encode` functions.
