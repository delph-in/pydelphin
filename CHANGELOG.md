# Change Log

## [Unreleased][unreleased]

## [v0.5.0][]

### Added

* `delphin.interfaces.rest` (#66)
* `delphin.mrs.xmrs.Mrs`: `to_dict()` and `from_dict()` methods (#68)
* `delphin.mrs.xmrs.Dmrs`: `to_dict()` and `from_dict()` methods (#68)
* `delphin.mrs.eds` (#25, #26)
* `delphin.lib.pegre` [Pegre](https://github.com/goodmami/pegre)
  parsing framework to help with EDS deserialization
* `properties` property accessor on `delphin.mrs.components.Node`

### Changed

* `delphin.mrs.xmrs.Mrs` is now a subclass of Xmrs
* `delphin.mrs.xmrs.Dmrs` is now a subclass of Xmrs
* `delphin.mrs.components.Node` no longer coerces `nodeid` to an
  integer (since `Node` is used by EDS as well)
* `delphin.mrs.dmrx` now casts nodeids to integers (see above)
* `delphin.mrs.xmrs.Xmrs.properties()` can take an `as_list=True`
  parameter to return the properties as a list instead of as a dict
  (to preserve the original order)
* `delphin._exceptions` is now `delphin.exceptions`
* Renamed a number of objects meant to be internal so their
  identifiers start with `_` (e.g. `delphin.derivation._UdfNodeBase`)

### Fixed

* Fixed a regression in reading multiple SimpleMRSs (#70)
* `delphin.mrs.components.Pred`
  - `short_form()` now works as expected when the predicate is already
    short (e.g. has no `_rel` suffix)
  - Short and full preds are now compared as equal
* `delphin.mrs.xmrs.Xmrs.outgoing_args()` no longer tries to remove
  `CARG` from the argument dict twice.
* `delphin.derivation` improve modeling of terminal nodes

### Documented

* Added or updated documentation throughout. Coverage is not complete,
  but should be significantly better.

## [v0.4.1][]

This release fixes a number of bugs and adds some minor features. The
`delphin.mrs.query` module has also been fixed and tested to work with
the current version.

### Added

* `delphin.mrs.xmrs`
  - `Xmrs.nodeids()`
  - `Xmrs.nodeid(iv)`
  - `Xmrs.validate()`
* `tests.mrs_Dmrs_test`
* `tests.mrs_query_test`
* `errors=(ignore|warn|strict)` parameter for SimpleMRS deserialization;
  with `warn` or `strict`, it uses `Xmrs.validate()` to notify of errors

### Fixed

* Quantifiers in DMRS now always point to quantifiees.
* `delphin.mrs.components.VarGenerator` uses a default sort (`u`) if
  none is given
* `delphin.itsdb.ItsdbProfile.join()` now raises an `ItsdbError` when
  the tables don't share a key
* AceGenerator now correctly joins error messages
* The search in `Xmrs.is_connected()` is fixed
* `mrs.path.walk()` now traverses multiple axes of the same name
* `mrs.query`, fixed the following (also see Added tests):
  - `select_nodeids()`
  - `select_nodes()`
  - `select_eps()`
  - `select_args()`
  - `select_links()`
  - `select_hcons()`
  - `select_icons()`
  - `find_argument_target()`
  - `find_subgraphs_by_preds()`
* HCONS and ICONS now serialize in the regular order; they were being
  reversed for some reason
* Improved label equality set head finding involving quantifiers

### Changed

* `delphin.mrs.xmrs.Dmrs()` no longer creates unlinked TOP
* `Xmrs` now stores ICONS as IndividualConstraint objects (and HCONS,
  but this was already the case, but not made explicit)
* `delphin.extra.latex.dmrs_tikz_dependency()` now accounts for
  multiple edges with the same source and target

### Deprecated

* `mrs.query`
  - `find_quantifier()` (use `xmrs.nodeid(..., quantifier=True)`)
  - `get_outbound_args()` (use `xmrs.outgoing_args()`)
  - `nodeid()` (use `xmrs.nodeid()`)

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
[v0.5.0]: ../../releases/tag/v0.5.0
[v0.4.1]: ../../releases/tag/v0.4.1
[v0.4.0]: ../../releases/tag/v0.4.0
[v0.3]: ../../releases/tag/v0.3
[v0.2]: ../../releases/tag/v0.2
[README]: README.md
