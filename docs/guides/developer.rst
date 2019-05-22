
Developer Guide
===============

Code Organization
-----------------

* Tier 0

  - `__about__`
  - `exceptions`
  - `util`

* Tier 1

  - `derivation`
  - `hierarchy`
  - `lnk`
  - `predicate`
  - `variable`

* Tier 2

  - `sembase` (lnk)
  - `semi` (hierarchy, predicate)
  - `tfs` (hierarchy)
  - `tokens` (lnk)
  - `vpm` (variable)

* Tier 3

  - `repp` (lnk, tokens)
  - `scope` (lnk, predicate, sembase)
  - `tdl` (tfs)

* Tier 4

  - `dmrs` (lnk, scope, sembase, variable)
  - `eds` (lnk, scope, sembase, variable)
  - `mrs` (lnk, predicate, scope, sembase, variable)

* Tier 5

  - `codecs` (dmrs, eds, mrs, ...)

* Tier 6

  - `interface` (codecs, derivation, tokens)

* Tier 7

  - `ace` (interface)
  - `itsdb` (interface)

* Tier 8

  - `tsql` (itsdb)

* Tier 9

  - `commands` (itsdb, lnk, semi, tsql, ...)
