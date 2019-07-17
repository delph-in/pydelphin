
delphin.web.client
==================

.. automodule:: delphin.web.client

This module provides classes and functions for making requests to
servers that implement the DELPH-IN Web API described here:

    http://moin.delph-in.net/ErgApi

.. note::

   Requires `requests` (https://pypi.python.org/pypi/requests). This
   dependency is satisfied if you install PyDelphin with the ``[web]``
   extra (see :doc:`../guides/setup`).

Basic access is available via the :func:`parse`,
:func:`parse_from_iterable`, :func:`generate`, and
:func:`generate_from_iterable` functions:

>>> from delphin.web import client
>>> url = 'http://erg.delph-in.net/rest/0.9/'
>>> client.parse('Abrams slept.', server=url)
Response({'input': 'Abrams slept.', 'readings': 1, 'results': [{'result-id': 0}], 'tcpu': 7, 'pedges': 17})
>>> client.parse_from_iterable(['Abrams slept.', 'It rained.'], server=url)
<generator object parse_from_iterable at 0x7f546661c258>
>>> client.generate('[ LTOP: h0 INDEX: e2 [ e SF: prop TENSE: past MOOD: indicative PROG: - PERF: - ] RELS: < [ proper_q<0:6> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: sg IND: + ] RSTR: h5 BODY: h6 ]  [ named<0:6> LBL: h7 CARG: "Abrams" ARG0: x3 ]  [ _sleep_v_1<7:13> LBL: h1 ARG0: e2 ARG1: x3 ] > HCONS: < h0 qeq h1 h5 qeq h7 > ICONS: < > ]')
Response({'input': '[ LTOP: h0 INDEX: e2 [ e SF: prop TENSE: past MOOD: indicative PROG: - PERF: - ] RELS: < [ proper_q<0:6> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: sg IND: + ] RSTR: h5 BODY: h6 ]  [ named<0:6> LBL: h7 CARG: "Abrams" ARG0: x3 ]  [ _sleep_v_1<7:13> LBL: h1 ARG0: e2 ARG1: x3 ] > HCONS: < h0 qeq h1 h5 qeq h7 > ICONS: < > ]', 'readings': 1, 'results': [{'result-id': 0, 'surface': 'Abrams slept.'}], 'tcpu': 8, 'pedges': 59})


If the `server` parameter is not provided to `parse()`, the default
ERG server (as used above) is used by default. Request parameters
(described at http://moin.delph-in.net/ErgApi) can be provided via the
`params` argument.

These functions instantiate and use subclasses of :class:`Client`,
which manages the connections to a server. They can also be used
directly:

>>> parser = web.Parser(server=url)
>>> parser.interact('Dogs chase cats.')
Response({'input': 'Dogs chase cats.', ...
>>> generator = web.Generator(server=url)
>>> generator.interact('[ LTOP: h0 INDEX: e2 ...')
Response({'input': '[ LTOP: h0 INDEX: e2 ...', ...)

The server responds with JSON data, which PyDelphin parses to a
dictionary. The responses from are then wrapped in
:class:`~delphin.interface.Response` objects, which provide two
methods for inspecting the results. The :meth:`Response.result()
<delphin.interface.Response.result>` method takes a parameter `i` and
returns the *i*\\ th result (0-indexed), and the
:meth:`Response.results() <delphin.interface.Response.results>` method
returns the list of all results. The benefit of using these methods is
that they wrap the result dictionary in a
:class:`~delphin.interface.Result` object, which provides methods for
automatically deserializing derivations, EDS, MRS, or DMRS data. For
example:

>>> r = parser.interact('Dogs chase cats', params={'mrs':'json'})
>>> r.result(0)
Result({'result-id': 0, 'score': 0.5938, ...
>>> r.result(0)['mrs']
{'variables': {'h1': {'type': 'h'}, 'x6': ...
>>> r.result(0).mrs()
<MRS object (udef_q dog_n_1 chase_v_1 udef_q cat_n_1) at 140000394933248>

If PyDelphin does not support deserialization for a format provided by
the server (e.g. LaTeX output), the :class:`~delphin.interface.Result`
object raises a :exc:`TypeError`.


Client Functions
----------------

.. autofunction:: parse
.. autofunction:: parse_from_iterable

.. autofunction:: generate
.. autofunction:: generate_from_iterable


Client Classes
--------------

.. autoclass:: Client
   :show-inheritance:
   :members:

.. autoclass:: Parser
   :show-inheritance:
   :members:

.. autoclass:: Generator
   :show-inheritance:
   :members:
