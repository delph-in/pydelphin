Elementary Dependency Matching
==============================

:wiki:`Elementary Dependency Matching <ElementaryDependencyMatch>`
(EDM; `Dridan and Oepen, 2011`_) is a metric for comparing two
semantic dependency graphs that annotate the same sentence. It
requires that each node is aligned to a character span in the original
sentence.

.. seealso::

   The :mod:`delphin.edm` module is the programmatic interface for the
   EDM functionality, while this guide describes the command-line
   interface.

.. tip::

   The smatch metric (`Cai and Knight, 2013
   <https://aclanthology.org/P13-2131/>`_) is essentially the same
   except that instead of relying on surface-aligned nodes it finds a
   mapping of nodes that optimizes the number of matching triples. The
   search uses stochastic hill-climbing, whereas EDM gives
   deterministic results. EDS and DMRS representations can be used
   with the `smatch tool <https://github.com/snowblink14/smatch/>`_ if
   they have been serialized to the PENMAN format (see
   :mod:`delphin.codecs.edspenman` and
   :mod:`delphin.codecs.dmrspenman`).

Command-line Usage
------------------

The :command:`edm` subcommand provides a simple interface for
computing EDM for EDS, DMRS, or MRS representations. The basic usage
is:

.. code-block:: console

   $ delphin edm GOLD TEST

``GOLD`` and ``TEST`` may be files containing serialized semantic
representations or :wiki:`[incr tsdb()] <ItsdbTop>` test suites
containing parsed analyses.

For example:

.. code-block:: console

   $ delphin edm gold.eds test.eds
   Precision:	0.9344262295081968
      Recall:	0.9193548387096774
     F-score:	0.9268292682926829

Per-item information can be printed by increasing the logging
verbosity to the ``INFO`` level (``-vv``). Weights for the different
classes of triples can be adjusted with ``-A`` for argument structure,
``-N`` for node names, ``-P`` for node properties, ``-C`` for
constants, and ``-T`` for graph tops. Try ``delphin edm --help`` for
more information.

Differences from Dridan and Oepen, 2011
---------------------------------------

Following the `mtool`_ implementation, :mod:`delphin.edm` treats
constant arguments (``CARG``) as independent triples, however, unlike
mtool, they get their own category and weight. This implementation
also follows mtool in checking if the graph tops are the same, also
with their own category and weight. One can therefore get the same
results as `Dridan and Oepen, 2011`_ by setting the weights for
top-triples and constant-triples to 0:

.. code-block:: console

   $ delphin edm -C0 -T0 GOLD TEST

Sometimes it helps to ignore missing items on the gold side, the test
side, or both. Missing items can occur when ``GOLD`` or ``TEST`` are
files with different numbers of representations, or when they are
:wiki:`[incr tsdb()] <ItsdbTop>` test suites with different numbers of
analyses per item. For example, to ignore pairs where the gold
representation is missing, do the following:

.. code-block:: console

   $ delphin edm --ignore-missing=gold GOLD TEST

Relevance to non-EDS Semantic Representations
---------------------------------------------

While EDM was designed for the semantic dependencies extracted from
Elementary Dependency Structures (:wiki:`EDS <EdsTop>`), it can be
used for other representations as long as they have surface alignments
for the nodes.  This implementation can natively work with a variety
of DELPH-IN representations and :doc:`formats <../api/delphin.codecs>`
via the ``--format`` option, including those for Minimal Recursion
Semantics (:wiki:`MRS <RmrsTop>`) and Dependency Minimal Recursion
Semantics (:wiki:`DMRS <RmrsDmrs>`). Non-DELPH-IN representations are
also possible as long as they can be serialized into one of these
formats.

Other Implementations
---------------------

#. Rebecca Dridan's original Perl version (see the :wiki:`wiki
   <ElementaryDependencyMatch>`):
#. `mtool`_: created for the 2019 CoNLL shared task on `Meaning
   Representation Parsing <http://mrp.nlpl.eu/>`_
#. As part of :wiki:`[incr tsdb()] <ItsdbTop>`
#. As part of `DeepDeepParser <https://github.com/janmbuys/DeepDeepParser>`_

.. _Dridan and Oepen, 2011: https://aclanthology.org/W11-2927/
.. _mtool: https://github.com/cfmrp/mtool
