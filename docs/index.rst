.. pyDelphin documentation master file, created by
   sphinx-quickstart on Wed May 14 15:29:22 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to pyDelphin's documentation!
=====================================

The pyDelphin project aims to facilitate research and work with
`DELPH-IN <http://delph-in.net>`_ formalisms. There are three main tiers
to pyDelphin's functionality:

 1. Serialization/Deserialization of DELPH-IN formalisms
 2. A data model and API for DELPH-IN data structures
 3. Commandline tools for basic operations

pyDelphin does *not* aim to do heavy tasks like parsing or generation.
Rather, it helps those who want to work with the *results* of tasks like
parsing or generation. It has been used for refreshing [incr tsdb()]
profiles to new schemas, converting MRS formalisms, extracting features
for sentiment classification, and more.


Currently there are two packages of pyDelphin:

.. toctree::
   :glob:
   :maxdepth: 2

   api/delphin.itsdb
   api/delphin.mrs

.. additional info
   setup
   tutorial
   pyDelphin
   api
   

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

