
delphin.web.server
==================

.. automodule:: delphin.web.server

This module provides classes and functions that implement a subset of
the DELPH-IN Web API DELPH-IN Web API described here:

    http://moin.delph-in.net/ErgApi

.. note::

   Requires Falcon (https://falcon.readthedocs.io/). This dependency
   is satisfied if you install PyDelphin with the ``[web]`` extra (see
   :doc:`../guides/setup`).

In addition to the parsing API, this module also provides support for
generation and for browsing [incr tsdb()] test suites.  In order to
use it, you will need a WSGI server such as `gunicorn`_, `mod_wsgi`_
for `Apache2`_, etc. You then write a WSGI stub for the server to use,
such as the following example:

.. code-block:: python

   # file: wsgi.py

   import falcon

   from delphin.web import server

   application = falcon.API()

   server.configure(
       application,
       parser='~/grammars/erg-2018-x86-64-0.9.30.dat',
       generator='~/grammars/erg-2018-x86-64-0.9.30.dat',
       testsuites={
           'gold': [
               {'name': 'mrs', 'path': '~/grammars/erg/tsdb/gold/mrs'}
	   ]
       }
   )

You can then run a local instance using, for instance, `gunicorn`_:

.. code-block:: console

   $ gunicorn wsgi
   [2019-07-12 16:03:28 +0800] [29920] [INFO] Starting gunicorn 19.9.0
   [2019-07-12 16:03:28 +0800] [29920] [INFO] Listening at: http://127.0.0.1:8000 (29920)
   [2019-07-12 16:03:28 +0800] [29920] [INFO] Using worker: sync
   [2019-07-12 16:03:28 +0800] [29923] [INFO] Booting worker with pid: 29923

And make requests with, for instance, :command:`curl`:

.. code-block:: console

   $ curl 'http://127.0.0.1:8000/parse?input=Abrams%20slept.&mrs' -v
   *   Trying 127.0.0.1...
   * TCP_NODELAY set
   * Connected to 127.0.0.1 (127.0.0.1) port 8000 (#0)
   > GET /parse?input=Abrams%20slept.&mrs HTTP/1.1
   > Host: 127.0.0.1:8000
   > User-Agent: curl/7.61.0
   > Accept: */*
   > 
   < HTTP/1.1 200 OK
   < Server: gunicorn/19.9.0
   < Date: Fri, 12 Jul 2019 08:04:29 GMT
   < Connection: close
   < content-type: application/json
   < content-length: 954
   < 
   * Closing connection 0
   {"input": "Abrams slept.", "readings": 1, "results": [{"result-id": 0, "mrs": {"top": "h0", "index": "e2", "relations": [{"label": "h4", "predicate": "proper_q", "arguments": {"ARG0": "x3", "RSTR": "h5", "BODY": "h6"}, "lnk": {"from": 0, "to": 6}}, {"label": "h7", "predicate": "named", "arguments": {"CARG": "Abrams", "ARG0": "x3"}, "lnk": {"from": 0, "to": 6}}, {"label": "h1", "predicate": "_sleep_v_1", "arguments": {"ARG0": "e2", "ARG1": "x3"}, "lnk": {"from": 7, "to": 13}}], "constraints": [{"relation": "qeq", "high": "h0", "low": "h1"}, {"relation": "qeq", "high": "h5", "low": "h7"}], "variables": {"e2": {"type": "e", "properties": {"SF": "prop", "TENSE": "past", "MOOD": "indicative", "PROG": "-", "PERF": "-"}}, "x3": {"type": "x", "properties": {"PERS": "3", "NUM": "sg", "IND": "+"}}, "h5": {"type": "h"}, "h6": {"type": "h"}, "h0": {"type": "h"}, "h1": {"type": "h"}, "h7": {"type": "h"}, "h4": {"type": "h"}}}}], "tcpu": 7, "pedges": 17}

.. _gunicorn: https://gunicorn.org/
.. _mod_wsgi: https://modwsgi.readthedocs.io/
.. _Apache2: https://httpd.apache.org/

Module Functions
----------------

.. autofunction:: configure


Server Application Classes
--------------------------

.. autoclass:: ProcessorServer
   :members:

.. autoclass:: ParseServer
   :show-inheritance:
   :members:

.. autoclass:: GenerationServer
   :show-inheritance:
   :members:

.. autoclass:: TestSuiteServer
   :members:
