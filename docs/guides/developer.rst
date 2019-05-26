
Developer Guide
===============

This guide is for helping developers of modules in the `delphin`
namespace or developers of PyDelphin itself.

.. contents::
   :local:

Module Dependencies
-------------------

Below is a listing of modules arranged into tiers by their
dependencies. A "tier" is just a grouping here; there is no
corresponding structure in the code except for the imports used in the
modules. Each module within a tier only imports modules from tiers
above it (imported modules, except for Tier 0 ones, are shown in
parentheses after the module name).

It is good for a module to be conservative with its dependencies
(i.e., climb to higher tiers, where Tier 0 is higher than Tier 1, and
so on). Module authors may consult this list to see on which tier
their modules would be placed.

If someone wants to take over maintainership of a PyDelphin module and
spin it off as a separate repository, then modules without
dependencies are the most eligible. For instance, if someone wants to
take over responsibility for the :mod:`delphin.mrs` module, then they
may want to also include the MRS codecs in their repository, or at
least test the codecs to changes they make.

* Tier 0

  - `delphin.__about__`
  - :mod:`delphin.exceptions`
  - `delphin.util`

* Tier 1

  - :mod:`delphin.derivation`
  - :mod:`delphin.hierarchy`
  - :mod:`delphin.interface` (soft dependencies on `tokens`,
    `derivation`, and `codecs`)
  - :mod:`delphin.lnk`
  - :mod:`delphin.predicate`
  - :mod:`delphin.variable`

* Tier 2

  - :mod:`delphin.ace` [`interface`]
  - :mod:`delphin.itsdb` [`interface`]
  - :mod:`delphin.sembase` [`lnk`]
  - :mod:`delphin.semi` [`hierarchy`, `predicate`]
  - :mod:`delphin.tfs` [`hierarchy`]
  - :mod:`delphin.tokens` [`lnk`]
  - :mod:`delphin.vpm` [`variable`]
  - :mod:`delphin.web` [`interface`]

* Tier 3

  - :mod:`delphin.repp` [`lnk`, `tokens`]
  - :mod:`delphin.scope` [`lnk`, `predicate`, `sembase`]
  - :mod:`delphin.tdl` [`tfs`]
  - :mod:`delphin.tsql` [`itsdb`]

* Tier 4

  - :mod:`delphin.dmrs` [`lnk`, `scope`, `sembase`, `variable`]
  - :mod:`delphin.eds` [`lnk`, `scope`, `sembase`, `variable`]
  - :mod:`delphin.mrs` [`lnk`, `predicate`, `scope`, `sembase`, `variable`]

* Tier 5

  - `delphin.codecs` [`dmrs`, `eds`, `mrs`, ...] (see :doc:`../api/delphin.codecs`)

* Tier 6

  - :mod:`delphin.commands` [`itsdb`, `lnk`, `semi`, `tsql`, ...]


Creating a New Module
---------------------

TBD


Creating a New Codec Module
---------------------------

TBD
