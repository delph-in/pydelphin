
Using ACE from PyDelphin
========================

`ACE <http://sweaglesw.org/linguistics/ace/>`_ is one of the most
efficient processors for DELPH-IN grammars, and has an impressively
fast start-up time. PyDelphin tries to make it easier to use ACE from
Python with the :mod:`delphin.ace` module, which provides functions
and classes for compiling grammars, parsing, transfer, and generation.

In this guide, `delphin.ace` is assumed to be imported as `ace`, as in
the following:

>>> from delphin import ace


Compiling a Grammar
-------------------

The :func:`~delphin.ace.compile` function can be used to compile a
grammar from its source. It takes two arguments, the location of the
ACE configuration file and the path of the compiled grammar to be
written. For instance (assume the current working directory is the
grammar directory):

>>> ace.compile('ace/config.tdl', 'zhs.dat')

This is equivalent to running the following from the commandline
(again, from the grammar directory):

.. code:: bash

    [~/zhong/cmn/zhs/]$ ace -g ace/config.tdl -G zhs.dat

All of the following topics assume that a compiled grammar exists.


Parsing
-------

The ACE interface handles the interaction between Python and ACE,
giving ACE the arguments to parse and then interpreting the output
back into Python data structures.

The easiest way to parse a single sentence is with the
:func:`~delphin.ace.parse` function. Its first argument is the path to
the compiled grammar, and the second is the string to parse:

>>> response = ace.parse('zhs.dat', '狗 叫 了')
>>> len(response['results'])
8
>>> response['results'][0]['mrs']
'[ LTOP: h0 INDEX: e2 [ e SF: prop-or-ques E.ASPECT: perfective ] RELS: < [ "_狗_n_1_rel"<0:1> LBL: h4 ARG0: x3 [ x SPECI: + SF: prop COG-ST: uniq-or-more PNG.PERNUM: pernum PNG.GENDER: gender PNG.ANIMACY: animacy ] ]  [ generic_q_rel<-1:-1> LBL: h5 ARG0: x3 RSTR: h6 BODY: h7 ]  [ "_叫_v_3_rel"<2:3> LBL: h1 ARG0: e2 ARG1: x3 ARG2: x8 [ x SPECI: bool SF: prop COG-ST: cog-st PNG.PERNUM: pernum PNG.GENDER: gender PNG.ANIMACY: animacy ] ] > HCONS: < h0 qeq h1 h6 qeq h4 > ICONS: < e2 non-focus x8 > ]'

Notice that the response is a Python dictionary. They are in fact a
subclass of dictionaries with some added convenience methods. Using
dictionary access methods returns the raw data, but the function
access can simplify interpretation of the results. For example:

>>> len(response.results())
8
>>> response.result(0).mrs()
<Mrs object (狗 generic 叫) at 2567183400998>

These response objects are described in the documentation for the
:mod:`~delphin.interface` module.

In addition to single sentences, a sequence of sentences can be
parsed, yielding a sequence of results, using
:func:`~delphin.ace.parse_from_iterable`:

>>> for response in ace.parse_from_iterable('zhs.dat', ['狗 叫 了', '狗 叫']):
...     print(len(response.results()))
...
8
5

Both :func:`~delphin.ace.parse` and
:func:`~delphin.ace.parse_from_iterable` use the
:class:`~delphin.ace.ACEParser` class for interacting with ACE. This
class can also be instantiated directly and interacted with as long as
the process is open, but don't forget to close the process when done.

>>> parser = ace.ACEParser('zhs.dat')
>>> len(parser.interact('狗 叫 了').results())
8
>>> parser.close()
0

The class can also be used as a context manager, which removes the
need to explicitly close the ACE process.

>>> with ace.ACEParser('zhs.dat') as parser:
...     print(len(parser.interact('狗 叫 了').results()))
...
8

The :class:`~delphin.ace.ACEParser` class and
:func:`~delphin.ace.parse` and
:func:`~delphin.ace.parse_from_iterable` functions all take additional
arguments for affecting how ACE is accessed, e.g., for selecting the
location of the ACE binary, setting command-line options, and changing
the environment variables of the subprocess:

>>> with ace.ACEParser('zhs-0.9.26.dat',
...                    executable='/opt/ace-0.9.26/ace',
...                    cmdargs=['-n', '3', '--timeout', '5']) as parser:
...     print(len(parser.interact('狗 叫 了').results()))
...
5

See the :mod:`delphin.ace` module documentation for more information
about options for :class:`~delphin.ace.ACEParser`.


Generation
----------

Generating sentences from semantics is similar to parsing, but the
:mod:`~delphin.codecs.simplemrs` serialization of the semantics is
given as input instead of sentences. You can generate from a single
semantic representation with :func:`~delphin.ace.generate`:

>>> m = '''
... [ LTOP: h0
...   RELS: < [ "_rain_v_1_rel" LBL: h1 ARG0: e2 [ e TENSE: pres ] ] >
...   HCONS: < h0 qeq h1 > ]'''
>>> response = ace.generate('erg.dat', m)
>>> response.result(0)['surface']
'It rains.'

The response object is the same as with parsing. You can also generate
from a list of MRSs with :func:`~delphin.ace.generate_from_iterable`:

>>> responses = list(ace.generate_from_iterable('erg.dat', [m, m]))
>>> len(responses)
2

Or instantiate a generation process with
:class:`~delphin.ace.ACEGenerator`:

>>> with ace.ACEGenerator('erg.dat') as generator:
...     print(generator.iteract(m).result(0)['surface'])
...
It rains.


Transfer
--------

ACE also implements most of the `LOGON transfer formalism
<http://moin.delph-in.net/LogonTransfer>`_, and this functionality is
available in PyDelphin via the :class:`~delphin.ace.ACETransferer`
class and related functions. In the current version of ACE, transfer
does not return as much information as with parsing and generation,
but the response object in PyDelphin is the same as with the other
tasks.

>>> j_response = ace.parse('jacy.dat', '雨 が 降る')
>>> je_response = ace.transfer('jaen.dat', j_response.result(0)['mrs'])
>>> e_response = ace.generate('erg.dat', je_response.result(0)['mrs'])
>>> e_response.result(0)['surface']
'It rains.'


Tips and Tricks
---------------

Sometimes the input data needs to be modified before it can be parsed,
such as the morphological segmentation of Japanese text. Users may
also wish to modify the results of processing, such as to streamline
an MRS--DMRS conversion pipeline. The former is an example of a
preprocessor and the latter a postprocessor. There can also be
"coprocessors" that execute alongside the original, such as for
returning the result of a statistical parser when the original fails
to reach a parse. It is straightforward to accomplish all of these
configurations with Python and PyDelphin, but the resulting pipeline
may not be compatible with other interfaces, such as
:meth:`TestSuite.process() <delphin.itsdb.TestSuite.process>`. By
using the :class:`delphin.interface.Process` class to wrap an
:class:`~delphin.ace.ACEProcess` instance, these pre-, co-, and
post-processors can be implemented in a more useful way. See
:ref:`preprocessor-example` for an example of using
:class:`~delphin.interface.Process` as a preprocessor.


Troubleshooting
---------------

Some environments have an encoding that isn't compatible with what ACE
expects. One way to mitigate this issue is to pass in the appropriate
environment variables via the `env` parameter. For example:

>>> import os
>>> env = os.environ
>>> env['LANG'] = 'en_US.UTF8'
>>> ace.parse('zhs.dat', '狗 叫 了', env=env)

