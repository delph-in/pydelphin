# Change Log

## [Unreleased][unreleased]

### Added

* `delphin.mrs.xmrs`
  - `Xmrs.nodeids()`
  - `Xmrs.nodeid(iv)`
* `tests.mrs_Dmrs_test`

### Changed

* `delphin.mrs.xmrs.Dmrs()` no longer creates unlinked TOP
* `delphin.mrs.components.VarGenerator` uses a default sort (`u`) if
  none is given

## [v0.4.0][]

This release fixes a number of bugs (including fixes from two new
contributors; see the [README][]), and adds some minor features:

* more convenient introspection of TDL lists
* a LaTeX exporter for DMRS

From [v0.4.0][], pyDelphin uses [semantic versioning](http://semver.org/),
and is available on [PyPI](https://pypi.python.org/pypi/pyDelphin).

This release also drops support for Python 2.6 (Python 2.7 is still
supported and tested).

### Added

* `delphin.extra.latex` is added for exporting to LaTeX; currently
  contains DMRS export via `dmrs_tikz_dependency()`
* TdlConsList and TdlDiffList classes are added, which make working
  with list structures in TDL more convenient; e.g., the `values()`
  function returns a Python list of the elements (instead of having
  to get them via `REST.REST.FIRST`, etc.)

### Removed

* Python2.6 support
* unused top-level util.py

### Fixed

* `Xmrs.subgraph()` no longer crashes when selecting only the top node
* allow hyphens in long-style variable sorts (e.g. `ref-ind2`)
* `dmrx.loads()` no longer fails for Python2
* DMRS->MRS conversion no longer generates invalid labels for
  transitive `*/EQ` links in particular orders
* MrsPath walks don't no longer cross `/EQ` links twice
* fix a bug in compound `ARG&ARG2` connectors in MrsPath

### Changed

* `delphin.mrs.simplemrs`
  - uppercase variable property names
  - don't print top-level `<-1:-1>` Lnk values for SimpleMRS 1.1
  - normalize case for other features and role names
* EPs in Xmrs are stored as ElementaryPredication objects instead of
  plain tuples (with no significant drop in performance)
* VarGenerator uses next unused vid instead of next in sequence (i.e.
  it fills in gaps)
* `delphin.mrs.components.Pred`
  - comparison is now case-insensitive
  - characters like `<` are now allowed inside a pred
  - don't allow the invalid `_relation` suffix, and pretend the `_rel`
    suffix is there if it isn't
* `ElementaryPredication.is_quantifier()` looks for the `RSTR` role;
  Pred and Node still look for a `q` POS, since they don't have access
  to the arguments/links
* added `__contains__()` method to TypedFeatureStructure to check for
  the presence of features
* TDL parsing treats strings as primitives instead of as the supertype
  of some TypedFeatureStructure

## [v0.3][]

This release simplifies the pyDelphin core classes and improves
performance for many MRS tasks. Most significantly, the inspection
ofXmrs objects by their components is done internally with basic tuple
(or namedtuple) and dict types, but the old "classy" interface can be
had with functions in delphin.mrs.components. This release also adds a
module for working with derivation trees, improves Python 2
compatibility, and co-occurs with improved documentation and unit
tests for pyDelphin.

### Added

* use setuptools for setup.py
* delphin.derivation (and associated tests)
* delphin.interfaces.ace.AceProcess `env` parameter for custom
  environment variables
* delphin.mrs
  - components.var_sort()
  - components.var_id()
  - components.sort_vid_split()
  - components.VarGenerator `store` attribute
  - components.split_pred_string() (moved from the Pred class)
  - components.is_valid_pred_string() (moved from the Pred class)
  - components.normalize_pred_string() (moved from the Pred class)
  - components.links()
  - components.hcons()
  - components.icons()
  - components.nodes()
  - components.elementarypredication()
  - components.elementarypredications()
  - compare.isomorphic `check_varprops` parameter
  - path.walk()
  - path.reify_xmrs()
  - path.merge()
  - path.XmrsPathNode.depth()
  - path.XmrsPathNode.order()
  - util.rargname_sortkey()
  - xmrs.Xmrs.outgoing_args()
  - xmrs.Xmrs.incoming_args()
* delphin.itsdb.ItsdbSkeleton
* recipes/ package for small, useful snippets (which also show how to
  use pyDelphin as a library)
  - recipes.semantics.contiguous_semantic_constituents()
* tests.mrs_compare_test

### Fixed

* Python 2.6+ compatibility
  - delphin._exceptions.TdlParsingError
* delphin.mrs.simplemrs no longer crashes if variable properties are
  specified on the HCONS or ICONS lists
* Xmrs now converts variable properties to lists on construction, in
  case a dict is given (which caused problems during serialization).
* delphin.mrs.components.normalize_pred_string() is more robust

### Changed

* delphin.mrs
  - Xmrs (significant changes, here's some of them)
    - class parameters are now: (top, index, xarg, eps, hcons, icons,
      vars, lnk, surface, identifier)
    - new composition functions: add_eps(), add_hcons(), add_icons()
    - new access functions: ep(), pred(), hcons(), properties(), etc...
    - (re)moved access functions: intrinsic_variables(),
      introduced_variables(), get_pred(), get_arg(), etc...
  - components
    - All (remaining) components for building MRS structures are now
      subclasses of namedtuples. This means the individual attributes
      cannot be reassigned (but mutable ones can be changed).
    - Lnk can no longer be instantiated with non-standard types
    - Lnk parameters are reversed: Lnk(type, data) (I don't remember
      why, though)
    - VarGenerator stores properties as a list by default (as is done
      with Xmrs properties)
    - is_valid_pred_string() is stricter in checking for valid preds
  - config.QUANTIFIER_SORT renamed to QUANTIFIER_POS
  - simplemrs.load() and loads() take a "strict" parameter (if True,
    more tests are performed during parsing)
  - simplemrs.dump() and dumps() will output ICONS even with version=1.0
  - dmrx.loads() no longer has an "encoding" parameter
  - mrx
    - loads() no longer takes an "encoding" parameter
    - has (untested) support for hypothetical ICONS data
  - query
    - select_eps() and select_args() "anchor" parameter is renamed to
      "nodeid"
    - select_icons() "target" and "clause" parameters renamed to "left"
      and "right", respectively
* delphin.interfaces.ace
  - `INPUT` key is added when AceProcess.interact() is called.
  - Generation response dictionaries are made consistent with parsing
    ones (including having dictionaries in RESULTS instead of just
    strings)
* delphin.tfs.TypedFeatureStructure
  - `features()` now returns a list, and sub-AVMs are only descended
    into if there is one feature and no supertypes.
* delphin.tdl.TdlDefinition
  - `features()` now returns a list, and sub-AVMs are only descended
    into if there is one feature and no supertypes.
  - `local_constraints()` now returns a list
* test now use pyTest for unittests (and doctests)

### Removed

* delphin.mrs
  - components.MrsVariable
  - components.Hook
  - components.AnchorMixin
  - components.Argument
  - components.Pred.split_pred_string() (moved to module function)
  - components.Pred.is_valid_pred_string() (moved to module function)
  - components.Pred.normalize_pred_string() (moved to module function)
  - components.Node.properties
  - components.ElementaryPredication.from_node()
  - components.ElementaryPredication.sortinfo
  - components.ElementaryPredication.properties
  - components.ElementaryPredication.get_arg()
  - components.ElementaryPredication.arg_value()
  - components.ElementaryPredication.add_argument()
  - config.ANCHOR_SORT
  - config.QEQ (moved to components.HandleConstraint.QEQ)
  - config.LHEQ (moved to components.HandleConstraint.LHEQ)
  - config.OUTSCOPES (moved to components.HandleConstraint.OUTSCOPES)
  - util.XmrsDiGraph
  - path.XmrsPath
  - path.XmrsPathNode.copy()
  - util.XmrsDiGraph


## [v0.2][]

There was no CHANGELOG file prior to this release, so I don't have much
information about changes, except for
[commit messages](../../commits/v0.2).

[unreleased]: ../../tree/develop
[v0.4.0]: ../../releases/tag/v0.4.0
[v0.3]: ../../releases/tag/v0.3
[v0.2]: ../../releases/tag/v0.2
[README]: README.md
