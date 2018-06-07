# Change Log

## [Unreleased][unreleased]

### Added

* `delphin.interfaces.ace.AceProcess.run_infos` stores information related
  to each run of an AceProcess, such as the machine architecture, user name,
  and start/end times; this info is made available via the `run` key in
  response objects
* `delphin.interfaces.ace.AceProcess.run_info` accesses the run information
  of the currently running process, or the last process if it has already
  ended
* `delphin.interfaces.base.Processor` is the base class for the ACE and REST
  processor interfaces and introduces the `task` member and `process_item()`
  function
* `delphin.util.SExpr` now has a `format()` method which takes basic objects
  (as from `SExpr.parse()`) and formats them in the lisp notation
* `delphin.interfaces.base.FieldMapper` for mapping interface response objects
  to [incr tsdb()] (table, rowdata) tuples.
* `delphin.itsdb.TestSuite.process()` function for using a processor (e.g.,
  AceParser) to process each item in the testsuite.

### Changed

* `delphin.itsdb.Record` can now accept a mapping of field names to values
  for instantiation, and the column indices will be looked up from the schema
* `delphin.itsdb.Record` now validates field data (and tests are added)
* `ace.AceProcess` and `rest.DelphinRestClient` in `delphin.interfaces` now
  inherit from `base.Processor` (#141)
* Clarified the documentation and code for `delphin.itsdb.TestSuite.write()`
  regarding the specifications of tables and/or data.
* Reverted an incomplete rewrite of `delphin.itsdb.make_skeleton()`
* Replaced `delphin.util.SExpr` with a custom non-PEG parser, which seems
  to be much faster for pathological items (#145)

### Fixed

* The `mkprof` command now correctly makes non-full profiles.

## [v0.7.0][]

This release adds a number of features. The main ones include a redone
[incr tsdb()] module, Prolog MRS export, and a REPP tokenizer. This
release also removes Python 3.3 support and adds Python 3.6 support,
and removes or mitigates several dependencies.

**Note**: there are some changes that may break backward compatibility; these
changes are prefixed with "**BREAKING**"

### Python Versions

* Removed Python 3.3 support
* Added Python 3.6 support

### Added

* `delphin.interface.ace.compile()` can take `executable` and `env`
  parameters, similar to `ace.parse()`, etc. (#119)
* `remap_nodeids` parameter to `Dmrs.from_triples()`, which defaults to
  `True`, indicates whether the nodeids used in the triples should be coerced
  into standard DMRS integer ids
* `--select` option to `convert` command for non-standard profile schemata
* Ensure the `properties=True|False` parameter existed for dump() and
  dumps() for all MRS codecs; default value may differ (#114)
* Add `--no-properties` option to delphin convert command; default is
  to always print properties (which may be different from the API
  function default) (#114)
* `delphin.itsdb.Relations` class for encoding/decoding relations files,
  which now also work on strings instead of actual files (#99)
* `delphin.itsdb.Relation` class for storing the relations of a single table
* `delphin.itsdb.Record`, `delphin.itsdb.Table`, and
  `delphin.itsdb.TestSuite` for modeling [incr tsdb()] substructures (#89)
* `delphin.itsdb.join()` does inner and left joins (#101)
* `delphin.itsdb.Field.default_value()` replaces
  `delphin.itsdb.default_value()`
* `delphin.util.deprecated` decorator for marking deprecated functions and
   methods
* DMRX now encodes index as a graph attribute (#126)
* DMRS's dictionary view (for JSON output) now encodes index as a
  top-level attribute.
* `delphin.mrs.prolog` serializer (#8)
* `delphin.repp` for REPP tokenization (#43)
* `delphin.exceptions.ReppError`
* `delphin.exceptions.ReppWarning`

### Changed

* Nodeids in Xmrs structures are no longer constrained to be integers
* `delphin.itsdb` now has public-facing `tsdb_core_files` and
  `tsdb_coded_attributes` variables
* `mkprof` command includes any non-empty core files in skeletons
* SimpleMRS codec now instantiates with the Mrs class instead of Xmrs (#103)
* SimpleMRS no longer breaks at non-breaking spaces in predicates (#128)
* Remove docopt dependency for command-line interfaces (#137)
* Move imports of dependencies to avoid unnecessary ImportErrors (#100)
* **BREAKING**: for `delphin.itsdb.Field`, the `other` list attribute is
  now just the boolean `partial` since there's no other use of it
* Add a few more patterns to `.gitignore`
* Remove unnecessary line in `delphin.main.mkprof()`
* **BREAKING**: Insert `top`, `index`, and `xarg` parameters into the
  `delphin.mrs.Dmrs` class instantiator before the `lnk` parameter;
  other arbitrary parameters are now disallowed
* **BREAKING**: SimpleDMRS format encodes top, index, xarg, lnk, and
  surface as graph attributes and removes the top link (`0:/H -> ...`)
* The `delphin` command no longer catches errors when converting; it was
  catching and hiding errors that were not intended to be hidden

### Fixed

* Corrected docstrings that had been misplaced in delphin.mrs.xmrs for
  over a year (#116)
* Non-integer nodeids no longer break sorting and construction
* Fix a bug in EDS getting CVARSORT when properties are printed
* Use target relations for writing empty files in `mkprof` command (#125)
* Properly split role and post in Dmrs.from_triples()
* Use top-specifying triples (e.g. (0, 'top', 10000)) in Dmrs.from_triples()
* Don't complain about missing POS field in Preds (#129)
* No longer print ARG0s twice in MRX
* Let MRX deal with missing TOP and INDEX

### Removed

* **BREAKING** `delphin.interfaces.ace._AceResult (#97)
* **BREAKING** `delphin.interfaces.ace._AceResponse (#97)

### Deprecated

* `delphin.itsdb.get_relations()` - use `delphin.itsdb.Relations.from_file()`
* `delphin.itsdb.default_value()` - use `delphin.itsdb.Field.default_value()`
* `delphin.itsdb.make_skeleton()` - build a `TestSuite` and write the core
  tables (this will be made more convenient later)
* `delphin.itsdb.filter_rows()`
* `delphin.itsdb.apply_rows()`
* `delphin.itsdb.ItsdbProfile` - use `delphin.itsdb.TestSuite`
* `delphin.itsdb.ItsdbSkeleton` - use `delphin.itsdb.TestSuite`

## [v0.6.2][]

### Added

* `delphin.itsdb.ItsdbProfile.exists()` (#112)
* `delphin.itsdb.ItsdbProfile.size()` (#112)
* `--in-place` option to the `delphin mkprof` command (#109)
* `delphin.derivation.UdfNode.preterminals()` (#105)
* `delphin.derivation.UdfNode.terminals()` (#105)

### Changed

* Hash on the normalized form of Preds. (#107)

### Fixed

* Properly call `re.sub()` so the flags don't become the count (#108)
* Include file size of gzipped tables in summary of `delphin mkprof` (#110)
* `normalize_pred_string()` now strips `_rel` (#111) and lowercases
* `is_valid_pred_string()` no longer requires `_rel` (#111)

## [v0.6.1][]

This minor release fixes a number of bugs with the ACE interface and a
number of small bugs that came up during testing. While a minor release,
one new (minor) feature is added: an AceTransferer and associated
functions.

### Added

* `delphin.interfaces.ace.AceTransferer` - due to a limitation with ACE,
  only the regular (non-tsdb) mode is allowed in transfer
* `delphin.interfaces.ace.transfer()`
* `delphin.interfaces.ace.transfer_from_iterable()`

### Changed

* `delphin.interfaces.ace` no longer captures stderr
* `delphin.interfaces.ace` attempts to restart a process that closed
  unexpectedly

### Fixed

* `delphin.interfaces.ace` ignores stderr, which effectively fixes #86
* `delphin.interfaces.ace` joins content lines in tsdb mode---fixes #95
* Write empty tables for `delphin mkprof` command unless `--skeleton` is
  used (fixes #96)
* `delphin.mrs.xmrs.Xmrs` equality test now checks variable properties
* `delphin.mrs.xmrs.Mrs.from_dict()` correctly reads variable properties (#98)
* `delphin.interfaces.ace._AceResponse.get()` now backs off to ParseResponse
  on KeyError
* `delphin.mrs.simplemrs` fix error message on unexpected token

## [v0.6.0][]

This release replaces the top-level `pyDelphin` and `mrs.py` scripts
with `delphin.sh` (when installed, a `delphin` command is made available
that accomplishes the same thing). The PENMAN codec is introduced for
DMRS and EDS. SEM-I and VPM modules are added with tests, but proper
subsumption comparisons aren't available until type hierarchies are also
added. Finally, various bugs and inconsistencies in MRS components are
fixed or the functionality is deprecated.

### Added

* `delphin.sh` top-level script (replaces the former `pyDelphin` and
  `mrs.py`)
* `delphin.main` module for script usage
* `mrs-json`, `dmrs-json`, and `eds-json` codecs for the `convert`
  script command
* `dmrs-penman` and `eds-penman` codecs for the `convert` script command
* Skeleton creation from sentence lists in the `mkprof` script command
* `delphin.mrs.xmrs.Xmrs.from_xmrs()` (meant to be used by subclasses)
* `delphin.mrs.xmrs.Dmrs.to_triples()`
* `delphin.mrs.xmrs.Dmrs.to_triples()`
* `delphin.mrs.eds.Eds.to_triples()`
* `delphin.mrs.eds.Eds.from_triples()`
* `delphin.mrs.penman` module for PENMAN serialization of DMRS and EDS
  (resolves #85)
* `delphin.vpm` and tests
* `delphin.semi` and tests

### Changed

* Filters and applicators in the `select`, `mkprof`, and `compare`
  script commands now have the form `table:col=expr` instead of taking
  two arguments
* The `mkprof` script command produces skeletons by default, to mimic
  [art](http://sweaglesw.org/linguistics/libtsdb/art)'s `mkprof` tool.
* `delphin.extra.latex` has nicer looking DMRS output
* Quantifiers are detected more consistently for, e.g., DMRS conversion;
  this mostly resolves #84
* DMRS `/EQ` links are now `MOD/EQ` and fix a direction (resolves #87)
* All \*MRS serializers/exporters take \*\*kwargs (though many ignore
  them) so that a common API can be used for, e.g., \*MRS conversion.
* Strip quotes on reading CARGs, add them when writing (fixes #75)

### Fixed

* `delphin.interfaces.ace` now detects interleaved stderr messages when
  there are errors decoding or parsing S-Expressions (fixes #86)
* Custom test runner in `setup.py`; now just call `tox`

### Removed

* `pyDelphin` top-level script (see `delphin.sh`)
* `mrs.py` top-level script (see `delphin.sh`)
* @total_ordering decorator on `delphin.mrs.components.Node` and
  `delphin.mrs.components.ElementaryPredication`, which provided
  comparisons for `__gt__`, `__ge__`, and `__le__` (`__lt__` was
  defined), is removed, but it didn't do much anyway because
  `__eq__` was not also defined on these classes.

### Deprecated

* `delphin.mrs.components.Pred.is_quantifier()`
* `delphin.mrs.components.Node.is_quantifier()`
* `delphin.mrs.components.Node.__lt__()`
* `delphin.mrs.components.ElementaryPredication.__lt__()`

## [v0.5.1][]

This minor release adds support for getting more parse information
from ACE (via the ACE 0.9.24's `--tsdb-stdout`), updates derivation
objects so UDX fields (e.g. `type`) can appear on all nonterminals,
and adds support for YY token lattices.

### Added

* `delphin.derivation.UdfNode.type` stores UDX grammar type info
* `delphin.derivation.UdfNode.to_udx()` serializes with UDX extensions
* `delphin.derivation.UdfNode.to_dict()` now allows an optional
  `labels` parameter for embedding short labels
* `delphin.interfaces.base` general interface helper classes (e.g.
  response classes)
* `delphin.tokens` encodes/decodes YY token lattices
* Support for retrieving tokens and labeled trees from REST client.
* `delphin.util.SExpr` S-Expression parser

### Changed

* `delphin.derivation.UdfNode.is_head()` now considers siblings
* `delphin.derivation.UdfNode.entity` returns only the entity (e.g.
  for UDX), not the type or head info
* `delphin.derivation.Derivation.from_string()` decomposes UDX
  entities and stores the type and head info separately
* `delphin.derivation.Derivation.from_dict()` now consideres `type`
  and `head` attributes
* `delphin.derivation.UdfNode` normalizes entity case for comparison
* `delphin.interfaces.ace` now returns a response object (like the
  RESTful interface) instead of just a dict
* ACE interface also supports the `--tsdb-stdout` and
  `--report-labels` options for future versions of ACE.

### Fixed

* `delphin.derivation.UdfNode` is_head() now works for JSON-encoded
  derivations.

### Removed

* `delphin.lib.six` was barely used, so is removed (and relevant
  Python 2 compatibility measures were made more consistent)

### Deprecated

* `delphin.derivation.UdfNode.basic_entity()` (use UdfNode.entity)
* `delphin.derivation.UdfNode.lexical_type()` (use UdfNode.type)

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
[v0.7.0]: ../../releases/tag/v0.7.0
[v0.6.2]: ../../releases/tag/v0.6.2
[v0.6.1]: ../../releases/tag/v0.6.1
[v0.6.0]: ../../releases/tag/v0.6.0
[v0.5.1]: ../../releases/tag/v0.5.1
[v0.5.0]: ../../releases/tag/v0.5.0
[v0.4.1]: ../../releases/tag/v0.4.1
[v0.4.0]: ../../releases/tag/v0.4.0
[v0.3]: ../../releases/tag/v0.3
[v0.2]: ../../releases/tag/v0.2
[README]: README.md
