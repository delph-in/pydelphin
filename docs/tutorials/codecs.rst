
Serialization Codecs for Semantic Representations
=================================================

PyDelphin has a common API (similar to Python's :py:mod:`pickle` and
:py:mod:`json` modules) for serialization codecs for semantic
representations such as MRS, DMRS, and EDS. This guide serves as the
documentation for all of the following:

MRS Codecs:

- :mod:`delphin.mrs.simplemrs`
- :mod:`delphin.mrs.mrx`
- :mod:`delphin.mrs.indexedmrs`
- :mod:`delphin.mrs.mrsjson`
- :mod:`delphin.mrs.mrsprolog`
- :mod:`delphin.interfaces.ace` (not primarily a codec but one is
  provided for convenience)

DMRS Codecs:

- :mod:`delphin.dmrs.simpledmrs`
- :mod:`delphin.dmrs.dmrx`
- :mod:`delphin.dmrs.dmrsjson`
- :mod:`delphin.dmrs.dmrspenman`
- :mod:`delphin.extra.dmrstikz_codec`

EDS Codecs:

- :mod:`delphin.eds.edsnative`
- :mod:`delphin.eds.edsjson`
- :mod:`delphin.eds.edspenman`


Module Constants
----------------

The following module constants are optional and are used to describe
strings that must appear in valid documents when serializing multiple
semantics representations at a time, as with :func:`dump` and
:func:`dumps`. It is used by :func:`delphin.commands.convert` to
provide a streaming serialization rather than dumping the entire file
at once. If the values are not defined in the codec module, default
values will be used.

.. _codec-HEADER:
.. data:: HEADER

   The string to output before any of semantic representations are
   serialized. For example, in :mod:`delphin.mrs.mrx`, the value of
   `HEADER` is `<mrs-list>`, and in
   :mod:`delphin.extra.dmrstikz_codec` it is an entire LaTeX preamble
   followed by `\begin{document}`.

.. _codec-JOINER:
.. data:: JOINER

   The string used to join multiple serialized semantic
   representations. For example, in :mod:`delphin.mrs.mrsjson`, it is
   a comma (`,`) following JSON's syntax. Normally it is either an
   empty string, a space, or a newline, depending on the conventions
   for the format and if the `indent` argument is set.

.. _codec-FOOTER:
.. data:: FOOTER

   The string to output after all semantic representations have been
   serialized. For example, in :mod:`delphin.mrs.mrx`, it is
   `</mrs-list>`, and in :mod:`delphin.extra.dmrstikz_codec` it is
   `\end{document}`.


Deserialization Functions
-------------------------

The deserialization functions :func:`load`, :func:`loads`, and
:func:`decode` accept textual serializations and return the
interpreted semantic representation. Both :func:`load` and
:func:`loads` expect full documents (including headers and footers,
such as `<mrs-list>` and `</mrs-list>` around a
:mod:`~delphin.mrs.mrx` serialization) and return lists of semantic
structure objects. The :func:`decode` function expects single
representations (without headers and footers) and returns a single
semantic structure object.

.. _codec-load:

Reading from a file or stream
`````````````````````````````

.. function:: load(source)

   Deserialize and return semantic representations from *source*.

   :param source: filename or file handle of a source containing
                  serialized semantic representations

   :rtype: list

.. _codec-loads:

Reading from a string
`````````````````````

.. function:: loads(s)

   Deserialize and return semantic representations from string *s*.

   :param s: string containing serialized semantic representations

   :rtype: list

.. _codec-decode:


Decoding from a string
``````````````````````

.. function:: decode(s)

   Deserialize and return the semantic representation from string *s*.

   :param s: string containing a serialized semantic representation

   :rtype: subclass of :class:`delphin.sembase.SemanticStructure`



Serialization Functions
-----------------------

The serialization functions :func:`dump`, :func:`dumps`, and
:func:`encode` take semantic representations as input as either return
a string or print to a file or stream. Both :func:`dump` and
:func:`dumps` will provide the appropriate :data:`HEADER`,
:data:`JOINER`, and :data:`FOOTER` values to make the result a valid
document. The :func:`encode` function only serializes a single
semantic representation, which is generally useful when working with
single representations, but is also useful when headers and footers
are not desired (e.g., if you want the :mod:`~delphin.dmrs.dmrx`
representation of a DMRS without `<dmrs-list>` and `</dmrs-list>`
surrounding it).

.. _codec-dump:

Writing to a file or stream
```````````````````````````

.. function:: dump(xs, destination, properties=True, lnk=True, indent=False, encoding='utf-8')

   Serialize semantic representations in *xs* to *destination*.

   :param xs: iterable of :class:`~delphin.sembase.SemanticStructure`
	      objects to serialize
   :param destination: filename or file object where data will be
                       written to
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
```````````````````

.. function:: dumps(xs, properties=True, lnk=True, indent=False)

   Serialize semantic representations in *xs* and return the string.

   The arguments are interpreted as in :func:`dump`.

   :rtype: str

.. _codec-encode:

Encoding to a string
````````````````````

.. function:: encode(x, properties=True, lnk=True, indent=False)

   Serialize single semantic representations *x* and return the string.

   The arguments are interpreted as in :func:`dump`.

   :rtype: str


Variations
----------

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

* :mod:`delphin.mrs.indexedmrs` requires a `semi` positional argument.

* :mod:`delphin.mrs.mrsjson`, :mod:`delphin.dmrs.dmrsjson`, and
  :mod:`delphin.eds.edsjson` introduce `to_dict()` and `from_dict()`
  functions in their public API as they may be generally useful.

* :mod:`delphin.dmrs.dmrspenman` and :mod:`delphin.eds.edspenman`
  introduce `to_triples()` and `from_triples()` functions in their
  public API.

* :mod:`delphin.eds.edsnative` allows a `show_status` keyword argument
  to turn on graph connectedness markers on serialization.

* :mod:`delphin.mrs.mrsprolog` and :mod:`delphin.extra.dmrstikz_codec`
  are export-only codecs and do not provide :func:`load`,
  :func:`loads`, or :func:`decode` functions.

* :mod:`delphin.interfaces.ace` is an import-only codec and does not
  provide :func:`dump`, :func:`dumps`, or :func:`encode` functions.
