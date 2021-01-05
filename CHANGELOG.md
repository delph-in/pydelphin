# Change Log

## Unreleased


## [v1.5.1]

**Release date: 2021-01-05**

### Fixed

* `delphin.tsdb.write_schema()` always opens files in UTF-8 ([#324])


## [v1.5.0]

**Release date: 2020-12-30**

### Python Versions

* Added Python 3.9 support

### Added

* `delphin.eds.EDSWarning`
* `delphin.codecs.eds` now reads and writes identifiers ([#323])
* `--no-predicate-modifiers` option for `delphin convert`

### Fixed

* `delphin.codecs.eds` now reads EDSs without tops (related to [#316])
* `delphin.eds` conversion from MRS ignores broken HCONS ([#319])
* `delphin.tsdb.read_schema()` always opens files in UTF-8 ([#324])

### Changed

* `delphin.codecs.eds` no longer outputs `:` when top is `None`
  (related to [#316])
* `delphin.codecs.eds` now defaults to `indent=True`
* `delphin.eds.from_mrs` backs off to index as top if MRS top is
  `None` ([#316])
* `delphin.eds.from_mrs` defaults to `predicate_modifiers=True`
* All semantics codecs now use indentation and blank lines in between
  by default
* `*-lines` codecs now ignore the `--indent` option

### Deprecated

* `--predicate-modifiers`; with predicate modification is now the
  default for EDS


## [v1.4.1]

**Release date: 2020-08-20**

### Fixed

* `delphin.codecs.dmrx` now actually suppresses properties when
  `properties=False` ([#306]); thanks to @arademaker


## [v1.4.0]

**Release date: 2020-07-20**

### Added

* `delphin.commands.process` now has a `report_progress` parameter,
  defaulting to `True`, for printing a progress bar ([#304])
* `delphin.itsdb.TestSuite.process()` now has a `callback` parameter,
  called for each response during processing, which can be used to
  implement a progress bar (among other things) ([#304])

### Fixed

* `delphin.repp` better anticipates unmatched capture groups ([#301])
* `delphin.dmrs.from_mrs()` no longer crashes on bad HCONS ([#303])
* `delphin.codes.simplemrs` is more robust to bad predicate strings,
  but there are still limits ([#302])

### Changed

* `delphin.itsdb.TestSuite.process()` no longer prints a progress bar,
  leaving it instead to the caller via the `callback ` parameter;
  since the progress bar is a side effect this is not a breaking
  change ([#304])


## [v1.3.0]

**Release date: 2020-07-01**

### Added

* `delphin.dmrs.DMRSWarning` for problems with conversion ([#289])
* `delphin.tfs.TFSError` ([#293])

### Fixed

* `delphin mkprof` no longer drops last column when using --delimter
  with a delimiter other than `@` ([#288])
* MRS to DMRS conversion raises a `DMRSWarning` instead of a KeyError
  when an EP has no intrinsic variable ([#289])
* `delphin.mrs.is_isomorphic()` works on disconnected graphs ([#296])

### Changed

* `delphin.tfs.FeatureStructure` raises a `TFSError` when attempting
  to assign a value on a non-subscriptable feature value ([#293])
* `delphin.tsdb.format()` formats `datetime.date` objects in the TSDB
  date format ([#291])
* `delphin.tsdb.write()` no longer requires the `fields` parameter if
  writing to an existing test suite directory ([#290])
* `delphin.tdl.iterparse()` will raise a more informative TDLError
  from a RecursionError when parsing ([#294])


## [v1.2.4]

**Release date: 2020-05-12**

### Fixed

* `delphin.tsdb.open()` does not use universal newlines ([#285])


## [v1.2.3]

**Release date: 2020-04-08**

### Added

* `delphin.itsdb.FieldMapper` now has a `source` parameter ([#283])
* `delphin.itsdb.TestSuite.process()` displays a progress bar when not
  logging individual items ([#282])

### Fixed

* `delphin process -e` no longer requires a `where` condition ([#281])

### Wontfix

* Data loss can occur when writing a TSDB database with invalid
  `:date` values. Workaround: fix the dates. ([#279])

## [v1.2.2]

**Release date: 2020-03-03**

### Fixed

* `delphin.ace.ACETransferer` now has a `stderr` parameter ([#278])
* `delphin.ace.ACEGenerator` now has a `stderr` parameter ([#278])

### Changed

* `delphin.itsdb.match_rows()` accepts either an `int` or `str` for
  the `key` parameter. This was always the case, but now it's
  documented and typed properly.


## [v1.2.1]

**Release date: 2020-01-22**

Bug fixes for recent Python versions and for the `delphin mkprof`
command, and more user-friendly error messages from all `delphin`
commands.

### Fixed

* `delphin.util.LookaheadIterator` no longer raises `RuntimeError` in
  Python 3.7+ ([#275])
* `delphin.commands.mkprof()` suppresses duplicate records ([#273])

### Changed

* `delphin` commands catch `PyDelphinException` and print its message
  without the stacktrace unless logging is at DEBUG ([#276])
* `delphin.commands.process()` raises a `CommandError` if the
  `grammar` argument is not a file ([#276])
* `delphin.commands.process()` raises a `CommandError` if the `source`
  or `testsuite` arguments are not valid TSDB database paths (as
  appropriate) ([#276])
* `delphin.commands.process()` will create a new directory if `source`
  is given and `testsuite` is a non-existing path
* `delphin.commands.process()` raises a `CommandError` if the `select`
  query has a column or relation invalid for the schema ([#276])
* `delphin.commands.compare()` raises a `CommandError` if the
  `testsuite` or `gold` arguments are not valid TSDB databases or
  database paths ([#276])


## [v1.2.0]

**Release date: 2020-01-16**

Removes Python 3.5 support, adds Python 3.8 support, adds the `cli`
namespace, fixes some issues with MRS and DMRS, an expands formatting
options for `delphin convert`.

### Python Versions

* Removed Python 3.5 support ([#219])
* Added Python 3.8 support

### Added

* `delphin.util.inspect_codecs()` ([#270])
* `delphin.util.import_codec()` ([#270])
* `delphin.cli` namespace and modules for existing commands ([#269])
* `-lines` codec suffix for `delphin.commands.convert()` ([#271])

### Fixed

* `delphin.codecs.edspenman` now properly reads predicate names
* `delphin.codecs.edspenman` and `delphin.codecs.dmrspenman` now wrap
  `PenmanError` in `PyDelphinException` ([#266])
* `delphin.mrs.MRS.quantification_pairs()` detects and ignores when
  quantifier(s) are shared by multiple EPs ([#267])
* `delphin.dmrs.from_mrs()` detects when an INDEX is specified but is
  not the intrinsic argument of any EP ([#267])

### Changed

* `delphin.codecs.dmrspenman` update to Penman v0.9
* `delphin.codecs.edspenman` update to Penman v0.9
* `delphin.codecs.edspenman` and `delphin.codecs.dmrspenman` now only
  encode a graph's primary component ([#268])
* `delphin.main` now detects command modules declared in the
  `delphin.cli` namespace ([#269])
* `--indent` option to `delphin convert` can take `"no"` or `"none"`
  to encode without newlines ([#271])


## [v1.1.0]

**Release date: 2020-01-07**

Removes the NetworkX dependency, resolves some TSQL bugs, and adds
some features to Derivations.

### Added

* `requirements.txt` mainly to try and help GitHub detect dependencies
* `delphin.derivation.UDFNode.parent` ([#245])
* `delphin.derivation.UDFNode.internals()` ([#246])
* `delphin.derivation.UDFTerminal.parent` ([#245])

### Changed

* `delphin.mrs.is_isomorphic()` no longer uses NetworkX ([#263])
* Docs no longer require the `sphinx_autodoc_typehints` package as of
  Sphinx 2.2.0 ([#264])
* `delphin.exceptions.PyDelphinSyntaxError` now puts the ^ marker in
  the right spot.
* Lexing in `delphin.util` now tracks the original line with each
  token, allowing for more informative syntax errors.
* `delphin.tsql.select()` will raise a `TSQLError` if a condition's
  type does not match that of the column it checks ([#261])
* `delphin.tsql.select()` now considers ``None`` values when checking
  conditions ([#262])


## [v1.0.3]

**Release date: 2019-11-29**

Resolves some more REPP bugs, improves logging, and ensures the code statically
type-checks.

### Added

* `[repp]` installation extra
* `delphin.repp.REPPWarning` class
* `delphin.repp.DEFAULT_TOKENIZER` module variable
* `delphin.repp.REPP.tokenize_result()` method to tokenize using the result of
  rule application
* `delphin.util.make_highlighter()` to handle getting Pygments highlighters
* `--color` option and `color` parameter for the `repp` command

### Fixed

* REPP now computes alignments even when substitution inserts nothing ([#252])
* REPP now uses the `regex` library if available ([#253])
* `delphin.tsdb.unescape()` doesn't incorrectly parse `\\` followed by `s` or
  `n` ([#257])

### Changed

* The default logging for the main script is now `ERROR` (was: `WARNING`)
* `delphin.tsdb.cast()` now raises an error if the value to cast is not a
  string or `None`
* `delphin.tsdb.Relation` is now a class instead of just a type declaration,
  but its existence is still just for type-checking

## [v1.0.2]

**Release date: 2019-08-21**

Resolves a REPP processing bug and improves REPP performance.

### Fixed

* `delphin.repp.REPP` no longer raises an IndexError when the
  replacement does not use all group references ([#250])

### Changed

* `delphin.repp.REPP` no longer recomputes alignments for unchanged
  strings, boosting performance 2-3x.

## [v1.0.1]

**Release date: 2019-08-15**

Resolves some bugs related to DMRS-to-MRS conversion.

### Fixed

* `delphin.dmrs.DMRS.arguments()` no longer raises a NameError ([#247])
* `delphin.dmrs.DMRS.scopal_arguments()` returns correct labels ([#249])
* `delphin.mrs.from_dmrs()` assigns the correct top handle ([#248])

### Changed

* `delphin.mrs.MRS` can now be instantiated with an empty structure

## [v1.0.0]

**Release date: 2019-08-14**

This is the largest release of PyDelphin yet, with over a year of work
and several years of ideas worked in. The changes are so numerous that
a normal CHANGELOG entry would only make it harder to understand what
is different, and so many changes are breaking that it would be
counterproductive to mark those that break backward
compatibility. Rather, users should treat PyDelphin v1.0.0 as an
entirely new API (that is, assume the entire API is incompatible with
the previous version). And yet, there are rather few new features
introduced in this release.

Two goals of this release are to fix design decisions that users had
found less than ideal, and to improve the codebase's maintainability
for the future. As part of the first goal, the package hierarchy has
been flattened (e.g., the `dmrs` package is no longer under `mrs`) and
the semantic representations are given their own data structures
instead of being converted to an intermediate representation. As part
of the second goal, `delphin` was made a namespace package,
[PEP-8](https://www.python.org/dev/peps/pep-0008/) style conventions
were applied throughout, and every part of the public API was
documented.

### Python Versions

* Removed Python 2.7 support ([#115])
* Removed Python 3.4 support ([#213])

### Main API Changes

* Semantics
  - There is no more intermediate `Xmrs` data structure
  - MRS, DMRS, and EDS are independent data structures but they
    implement common interfaces
  - A new `delphin.scope` module defines scope operations
  - DMRS and EDS are moved to the `delphin.dmrs` and `delphin.eds`
    packages, respectively
  - All unshared semantic components (EPs, Nodes, etc.) are defined by
    their respective packages (`delphin.mrs.EP`, `delphin.dmrs.Node`,
    `delphin.eds.Node`, etc.)
  - Abstract classes are defined in `delphin.sembase` and `delphin.scope`
  - Shared components get their own modules (`delphin.lnk`,
    `delphin.predicate`, etc.)
* Serialization
  - All serialization codecs for semantics representations are now
    under `delphin.codecs`, which is a namespace package
  - These implement a common "Codec API" which allows additional
    codecs to be installed as plugins
* Test Suite Databases
  - Low-level operations are defined in `delphin.tsdb`
  - SQL-database-like operations are defined in `delphin.itsdb`
  - The incremental API of `delphin.itsdb.TestSuite` is simplified;
    Rows are now immutable, Tables are always backed by files (either
    named or temporary), and writing to disk only happens via the
    `TestSuite.commit()` method
  - Table joins for complex queries are now entirely handled by
    `delphin.tsql`
  - Filter and Applicator functionality is removed, but the filtering
    is handled better by `delphin.tsql`
* Interfaces
  - Common interface classes are now in `delphin.interface`
  - The ACE interface is moved up to `delphin.ace`
  - `delphin.ace` now supports full-forest parsing
  - The web interface is no longer called "RESTful" (because it's far
    from it) and is moved to `delphin.web.client`
  - A web server is implemented at `delphin.web.server`
* Hierarchies
  - A new `delphin.hierarchy` module for multiple-inheritance
    hierarchies
  - The hierarchy implementation is used for `delphin.semi` and
    `delphin.tfs` for computing subsumption and type compatibility
* Other Removals Not Listed Above
  - `delphin.mrs` submodules: `compare`, `components`, `config`,
    `path`, `query`, `util`; some functions are moved to `delphin.mrs`
  - `delphin.extra`, but functionality is available as plugins:
    - [`delphin-latex`](https://github.com/delph-in/delphin-latex)
    - [`delphin.highlight`](https://github.com/delph-in/delphin.highlight)
  - `delphin.sh` script
  - `tox`-based testing
  - Various methods and function parameters may be removed; please
    consult the API documentation


## [v0.9.2]

**Release date: 2019-04-01**

### Python Versions

* Added Python 3.7 support

### Added

* `delphin.interfaces.ace.AceProcessError` for unrecoverable ACE
  crashes ([#181])
* ACE command-line options are allowed with `delphin process --options=...`
  and in `delphin.commands.process(..., options=...)` ([#180])
* `delphin.itsdb.Record.from_dict()`
* `delphin.itsdb.Table` ([#186])
  - `write()`
  - `attach()`
  - `detach()`
  - `commit()`
  - `is_attached()`
  - `list_changes()`
  - Various methods to replace `list` functionality: `append()`, `extend()`,
	`__len__()`, `__getitem__()`, `__setitem__()`, and `__iter__()`
* `delphin.itsdb.TestSuite.process()` the `gzip` and `buffer_size` parameters
* `-z` / `--gzip` option to the `delphin process` command

### Fixed

* `delphin.mrs.eds` parsing of predicates and empty property lists ([#203])
* `delphin.commands.convert` wrap the inner step of conversion in a try-except
  block to more gracefully handle crashes on a single input. ([#200])
* `delphin.itsdb.TestSuite.write()` re-enable the `append` parameter

### Removed

* **BREAKING** `name` parameter on `delphin.itsdb.Table`. The `name` attribute
  is still available as it is taken from the table's schema.

### Changed

* **BREAKING** `delphin.itsdb.Table` is no longer a subtype of `list`, meaning
  that some list-like behavior is gone. Most relevant functionality is
  recreated (e.g., `append()`, `extend()`, `__getitem__()`, `__len__()`, etc.)
* **BREAKING** `delphin.itsdb.Record` can no longer be instantiated with a dict
  with column data; use `Record.from_dict()`
* **BREAKING** `delphin.itsdb.Record` stores data as strings, always retrieves
  by default as cast types. Use `Record.get(..., cast=False)` to get the raw
  string value.

### Deprecated

* `delphin.mrs.convert()` use `delphin.commands.convert` instead


## [v0.9.1]

**Release date: 2018-10-31**

### Fixed

* `delphin.tfs.TypedFeatureStructure` no longer duplicates attributes
  on `__slots__`
* TDL identifiers are reverted to the more permissive blacklist pattern ([#192])
* TDL identifiers, coreferences, and 'symbols now use the same pattern ([#191])

### Changed

* Import package information from `delphin/__about__.py` into
  `delphin/__init__.py` ([#190])

## [v0.9.0]

**Release date: 2018-10-20**

This release introduces a completely redone TDL parser that follows
the description of TDL syntax at http://moin.delph-in.net/TdlRfc based
on recent discussions on the DELPH-IN mailing list (links to these
discussions are at the bottom of the linked wiki). In addition, there
are three other major introductions: `delphin.commands`, which gives
programmatic access to the `delphin` command-line utilities;
`delphin.tsql`, which implements a subset of the TSQL query language
(see http://moin.delph-in.net/TsqlRfc) that now replace the --filter
options for certain commands; and the new `TypeHierarchy` class in
`delphin.tfs`. Improvements to the `delphin.itsdb.TestSuite` class
now give it feature-parity with the `ItsdbProfile` class it replaces.
See the rest of the changelog for additional improvements.

### Fixed

* `delphin.tdl.parse()` now accepts a filename argument and returns a properly
  functioning generator ([#104])
* `delphin.itsdb` works better with gzipped tables with Python 2
* `delphin.mrs.penman` no longer calls `Eds.from_xmrs(x)` when `x` is an `Eds`

### Added

* `tests/tdl_test.py` unit tests intended to replace `tests/tdl_test.md`
* `delphin.tdl.TdlType.docstring` contains a list of a type's docstrings
* `delphin.tdl.parse()` now takes an `encoding` parameter ([#172])
* `delphin.tdl.iterparse()` for new-style TDL parsing ([#153], [#167], [#168], [#170])
* `delphin.tdl.format()` for TDL serialization ([#82], [#187])
* Updated TDL entity classes: ([#168])
  - `delphin.tdl.Term`
  - `delphin.tdl.TypeIdentifier`
  - `delphin.tdl.String`
  - `delphin.tdl.Regex`
  - `delphin.tdl.AVM`
  - `delphin.tdl.ConsList`
  - `delphin.tdl.DiffList`
  - `delphin.tdl.Coreference`
  - `delphin.tdl.Conjunction`
  - `delphin.tdl.TypeDefinition`
  - `delphin.tdl.TypeAddendum`
  - `delphin.tdl.LexicalRuleDefinition`
  - `delphin.tdl.LetterSet`
  - `delphin.tdl.WildCard`
  - `delphin.tdl.TypeEnvironment`
  - `delphin.tdl.InstanceEnvironment`
  - `delphin.tdl.FileInclude`
* TDL parameters:
  - `delphin.tdl.LIST_TYPE` (default: `"*list*"`)
  - `delphin.tdl.EMPTY_LIST_TYPE` (default: `"*null*"`)
  - `delphin.tdl.LIST_HEAD` (default: `"FIRST"`)
  - `delphin.tdl.LIST_TAIL` (default: `"REST"`)
  - `delphin.tdl.DIFF_LIST_LIST` (default: `"LIST"`)
  - `delphin.tdl.DIFF_LIST_LAST` (default: `"LAST"`)
* `delphin.tfs.FeatureStructure`, since the type of `TypedFeatureStructure`
  was unused; `TypedFeatureStructure` now inherits from `FeatureStructure`
* `delphin.tfs.FeatureStructure.features()` (as well as the `features()`
  methods on `TypedFeatureStructure`, `AVM`, `Conjunction`, and
  `TypeDefinition`) now take a boolean `expand` argument which, if `True`,
  expands all feature paths.
* `delphin.tfs.TypeHierarchy` with basic tests ([#93])
* `delphin.exceptions.TdlWarning` for notifications about deprecated TDL
  syntaxes
* `delphin.util.LookaheadIterator` for parsing with arbitrary lookahead
* `delphin.commands` module to contain logic for `delphin` commands ([#140])
* `tests/commands_test.py` to test invocation of commands (but not results)
* `delphin.util.detect_encoding` and tests for checking file header for
  encoding information ([#169])
* `delphin.tsql` module for TSQL queries of testsuites
* `delphin.exceptions.TSQLSyntaxError`
* `delphin.itsdb`
  - `Relations.find()` returns the names of tables defining a field
  - `Relations.path()` returns a path of `(table, shared_field)` tuples
    describing how to get from one table to another via shared keys
  - `TestSuite.write()` takes an optional `relations` parameter to write
    a profile with an updated relations file ([#150])
  - `TestSuite.exists()` ([#150])
  - `TestSuite.size()` ([#150])
  - `Record.get()` takes a `cast` parameter; when `True`, values are cast
    to the field's datatype
  - `select_rows()` takes a `cast` parameter as with `Record.get()`

### Changed

* `delphin.tdl` now parses triple-quoted docstrings ([#167]); note that it
  no longer parses the old-style docstrings
* `delphin.tdl.TdlDefinition` inherits from `delphin.tfs.FeatureStructure`
* `delphin.itsdb.TestSuite` no longer casts values by default (see note on
  `Record.get()` above)
* `delphin.itsdb.TestSuite.process()` can take a `Table` as the `source`
  instead of just `TestSuite`.
* **BREAKING** The `delphin` commands have all replaced the previous
  method of filtering testsuites with the new TSQL queries. Applicators
  are no longer available to commands. Please see `delphin <cmd> -h` for
  updated usage notes. ([#138], [#179])

### Deprecated

* `delphin.tdl.parse()` ([#168])
* `delphin.tdl.lex()` ([#168])
* `delphin.tdl.tokenize()` ([#168])

### Removed

* **BREAKING** `delphin.tdl.TdlDefinition.comment`; replaced by
  `TdlType.docstring`
* **BREAKING** `--filter` option on all commands
* **BREAKING** `--apply` option on all commands
* **BREAKING** `--join` option on the `select` command
* `recipes/` directory


## [v0.8.0]

**Release date: 2018-08-23**

This release improves EDS support, cleans up the code, makes the codecs
consistent and makes predicate support harmonious with Delphin. This is the
first release by the new maintainer, Angie McMillan-Major.

### Added

* `delphin.mrs.eds`: `dump()` and `dumps()` take a `show_status` parameter
  which turns on the annotation of disconnected graphs and nodes ([#157])
* `delphin.mrs.eds`: `Eds.from_xmrs()`, `dump()` and `dumps()` take a
  `predicate_modifiers` parameter which enables the use of a function to
  add additional edges in order to join disconnected graphs ([#156])
* `delphin.mrs.eds.non_argument_modifiers()` is the default method for
  EDS predicate modification, but it also works (with different
  parameters) for DMRS-like edges.
* The `convert` command can take a `--show-status` option which annotates
  disconnected graphs and nodes when `--to=eds`
* The `convert` command can take a `--predicate-modifiers` option which
  attempts to rejoin disconnected EDS graphs that fit certain criteria
* Documentation for implementing an ACE preprocessor ([#91])
* `ace` as a `--from` codec for the `convert` subcommand, which reads
    SimpleMRS strings from ACE output ([#92])

### Changed

* Converting with `--to=eds` no longer shows disconnected graphs and nodes
  by default (see `--show-status` above)
* Representative node selection for DMRS and EDS considers the scope
  hierarchy when looking for candidate nodes
* `delphin.mrs.xmrs.Xmrs.from_xmrs()` and `delphin.mrs.eds.Eds.from_xmrs()`
  now take a `**kwargs` argument to facilitate the `convert` command ([#160])
* The following `delphin.tdl` functions are now private:
    `delphin.tdl._parse_avm()`, `delphin.tdl._parse_affixes()`,
    `delphin.tdl._parse_typedef()`, `delphin.tdl._parse_attr_val()`,
    `delphin.tdl._parse_cons_list()`, `delphin.tdl._parse_conjunction()`,
    `delphin.tdl._parse_diff_list()` ([#81])
* **BREAKING** `delphin.interfaces.ace.AceProcess` whitelists certain
    command-line arguments for ACE; invalid arguments or values raise a
    ValueError. This could break code that uses options not whitelisted,
    but such code probably wouldn't work anyway. ([#149])

### Fixed

* Converting to PENMAN via the `convert` command should no longer crash for
  disconnected graphs, but print a log message to stderr, print a blank line
  to stdout, and then continue ([#161])
* Updated the docstrings for `delphin.mrs.xmrs.Xmrs.args()`,
  `delphin.mrs.xmrs.Xmrs.outgoing_args()`, and
  `delphin.mrs.xmrs.Xmrs.incoming_args()`, from "DMRS-style undirected links"
  to "MOD/EQ links" and updated the return value of `Xmrs.args()` and
  `Xmrs.outgoing_args` from `{nodeid: {}}` to `{role: tgt}` ([#133])
* `delphin.mrs.compare.isomorphic()` compares predicates using normalized form
* Updated the code and the docstrings for references to 'string' and 'grammar'
  predicates to refer to 'surface' and 'abstract' predicates ([#117])
* `delphin.tdl.parse()` now accepts either a file or a filename argument ([#104])
* The following dump methods now allow either a file or filename as their
  arguments like `delphin.mrs.penman.dump()`: `delphin.mrs.eds.dump()`,
  `delphin.mrs.simplemrs.dump()`, `delphin.mrs.simpledmrs.dump()`,
  `delphin.mrs.mrx.dump()`, `delphin.mrs.dmrx.dump()`,
  `delphin.mrs.prolog.dump()` ([#152])
* Non-ascii XML output is now able to be processed in Python2 ([#106])
* `delphin.interfaces.ace` now validates parser, transfer, and generator inputs
  and refuses to process invalid inputs ([#155])
* `delphin.interfaces.ace` handles whitespace in s-expressions a bit better
* `itsdb.get_data_specifier()` now allows unicode arguments in Python2 ([#164])

### Deprecated

* `delphin.mrs.query.intrinsic_variable()`; probably should have been
  deprecated in v0.4.1.
* `delphin.mrs.components.Pred.string_or_grammar_pred()`; replaced with
  `delphin.mrs.components.Pred.surface_or_abstract()`
* `delphin.mrs.components.Pred.stringpred()`; replaced with
  `delphin.mrs.components.Pred.surface()`
* `delphin.mrs.components.Pred.grammarpred()`; replaced with
  `delphin.mrs.components.Pred.abstract()`

## [v0.7.2]

**Release date: 2018-06-12**

This is a very minor release that just fixes one bug introduced in v0.7.1.

### Fixed

* ACE interface no longer gives unnecessary error message when reading the run
  info from the first line of output ([#148])

## [v0.7.1]

**Release date: 2018-06-09**

There were some bugs in the last release, particularly with Python 2.7, which
have been addressed in this release. There is one significant new feature,
which is the ability to process [incr tsdb()] profiles, either with the
`process()` method on `TestSuite` objects or via the new `process` command.

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
* Add `process` command to main script

### Changed

* `delphin.itsdb.Record` can now accept a mapping of field names to values
  for instantiation, and the column indices will be looked up from the schema
* `delphin.itsdb.Record` now validates field data (and tests are added)
* `delphin.itsdb.Record` values can be set by the field name and index
* `ace.AceProcess` and `rest.DelphinRestClient` in `delphin.interfaces` now
  inherit from `base.Processor` ([#141])
* `delphin.itsdb.ItsdbProfile` takes an optional `cast` keyword argument; this
  class is deprecated, but the addition is to smooth over the transition to
  the new `TestSuite` class.
* Clarified the documentation and code for `delphin.itsdb.TestSuite.write()`
  regarding the specifications of tables and/or data.
* Reverted an incomplete rewrite of `delphin.itsdb.make_skeleton()`
* Replaced `delphin.util.SExpr` with a custom non-PEG parser, which seems
  to be much faster for pathological items ([#145])
* **BREAKING** `ItsdbProfile`, `TestSuite`, and `Table.from_file()` in
  `delphin.itsdb` now accept an encoding parameter, which defaults to `utf-8`.
  Profiles will be read and written using the specified encoding, instead of
  using whatever is defined by the locale. This should only be a breaking
  change if your preferred locale is neither `ascii` nor `utf-8`.
* **BREAKING** `ItsdbProfile` and `TestSuite` in `delphin.itsdb` delete extra
  table files on writing (e.g., if `item.gz` is written, `item` will be
  deleted if it also exists). This is only breaking if anyone relied on having
  both the gzipped and regular versions of tables.

### Fixed

* The `mkprof` command now correctly makes non-full profiles.
* The `mkprof` command is now more Python 2.7-compatible
* Made `delphin.itsdb` more compatible with Python 2.7

## [v0.7.0]

**Release date: 2018-05-08**

This release adds a number of features. The main ones include a redone
[incr tsdb()] module, Prolog MRS export, and a REPP tokenizer. This
release also removes Python 3.3 support and adds Python 3.6 support,
and removes or mitigates several dependencies.

### Python Versions

* Removed Python 3.3 support
* Added Python 3.6 support

### Added

* `delphin.interface.ace.compile()` can take `executable` and `env`
  parameters, similar to `ace.parse()`, etc. ([#119])
* `remap_nodeids` parameter to `Dmrs.from_triples()`, which defaults to
  `True`, indicates whether the nodeids used in the triples should be coerced
  into standard DMRS integer ids
* `--select` option to `convert` command for non-standard profile schemata
* Ensure the `properties=True|False` parameter existed for dump() and
  dumps() for all MRS codecs; default value may differ ([#114])
* Add `--no-properties` option to delphin convert command; default is
  to always print properties (which may be different from the API
  function default) ([#114])
* `delphin.itsdb.Relations` class for encoding/decoding relations files,
  which now also work on strings instead of actual files ([#99])
* `delphin.itsdb.Relation` class for storing the relations of a single table
* `delphin.itsdb.Record`, `delphin.itsdb.Table`, and
  `delphin.itsdb.TestSuite` for modeling [incr tsdb()] substructures ([#89])
* `delphin.itsdb.join()` does inner and left joins ([#101])
* `delphin.itsdb.Field.default_value()` replaces
  `delphin.itsdb.default_value()`
* `delphin.util.deprecated` decorator for marking deprecated functions and
   methods
* DMRX now encodes index as a graph attribute ([#126])
* DMRS's dictionary view (for JSON output) now encodes index as a
  top-level attribute.
* `delphin.mrs.prolog` serializer ([#8])
* `delphin.repp` for REPP tokenization ([#43])
* `delphin.exceptions.ReppError`
* `delphin.exceptions.ReppWarning`

### Changed

* Nodeids in Xmrs structures are no longer constrained to be integers
* `delphin.itsdb` now has public-facing `tsdb_core_files` and
  `tsdb_coded_attributes` variables
* `mkprof` command includes any non-empty core files in skeletons
* SimpleMRS codec now instantiates with the Mrs class instead of Xmrs ([#103])
* SimpleMRS no longer breaks at non-breaking spaces in predicates ([#128])
* Remove docopt dependency for command-line interfaces ([#137])
* Move imports of dependencies to avoid unnecessary ImportErrors ([#100])
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
  over a year ([#116])
* Non-integer nodeids no longer break sorting and construction
* Fix a bug in EDS getting CVARSORT when properties are printed
* Use target relations for writing empty files in `mkprof` command ([#125])
* Properly split role and post in Dmrs.from_triples()
* Use top-specifying triples (e.g. (0, 'top', 10000)) in Dmrs.from_triples()
* Don't complain about missing POS field in Preds ([#129])
* No longer print ARG0s twice in MRX
* Let MRX deal with missing TOP and INDEX

### Removed

* **BREAKING** `delphin.interfaces.ace._AceResult ([#97])
* **BREAKING** `delphin.interfaces.ace._AceResponse ([#97])

### Deprecated

* `delphin.itsdb.get_relations()` - use `delphin.itsdb.Relations.from_file()`
* `delphin.itsdb.default_value()` - use `delphin.itsdb.Field.default_value()`
* `delphin.itsdb.make_skeleton()` - build a `TestSuite` and write the core
  tables (this will be made more convenient later)
* `delphin.itsdb.filter_rows()`
* `delphin.itsdb.apply_rows()`
* `delphin.itsdb.ItsdbProfile` - use `delphin.itsdb.TestSuite`
* `delphin.itsdb.ItsdbSkeleton` - use `delphin.itsdb.TestSuite`

## [v0.6.2]

**Release date: 2017-06-02**

### Added

* `delphin.itsdb.ItsdbProfile.exists()` ([#112])
* `delphin.itsdb.ItsdbProfile.size()` ([#112])
* `--in-place` option to the `delphin mkprof` command ([#109])
* `delphin.derivation.UdfNode.preterminals()` ([#105])
* `delphin.derivation.UdfNode.terminals()` ([#105])

### Changed

* Hash on the normalized form of Preds. ([#107])

### Fixed

* Properly call `re.sub()` so the flags don't become the count ([#108])
* Include file size of gzipped tables in summary of `delphin mkprof` ([#110])
* `normalize_pred_string()` now strips `_rel` ([#111]) and lowercases
* `is_valid_pred_string()` no longer requires `_rel` ([#111])

## [v0.6.1]

**Release date: 2017-04-06**

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

* `delphin.interfaces.ace` ignores stderr, which effectively fixes ([#86])
* `delphin.interfaces.ace` joins content lines in tsdb mode---fixes ([#95])
* Write empty tables for `delphin mkprof` command unless `--skeleton` is
  used (fixes [#96])
* `delphin.mrs.xmrs.Xmrs` equality test now checks variable properties
* `delphin.mrs.xmrs.Mrs.from_dict()` correctly reads variable properties ([#98])
* `delphin.interfaces.ace._AceResponse.get()` now backs off to ParseResponse
  on KeyError
* `delphin.mrs.simplemrs` fix error message on unexpected token

## [v0.6.0]

**Release date: 2017-01-20**

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
  (resolves [#85])
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
  this mostly resolves ([#84])
* DMRS `/EQ` links are now `MOD/EQ` and fix a direction (resolves [#87])
* All \*MRS serializers/exporters take \*\*kwargs (though many ignore
  them) so that a common API can be used for, e.g., \*MRS conversion.
* Strip quotes on reading CARGs, add them when writing (fixes [#75])

### Fixed

* `delphin.interfaces.ace` now detects interleaved stderr messages when
  there are errors decoding or parsing S-Expressions (fixes [#86])
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

## [v0.5.1]

**Release date: 2016-07-19**

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

## [v0.5.0]

**Release date: 2016-06-19**

### Added

* `delphin.interfaces.rest` ([#66])
* `delphin.mrs.xmrs.Mrs`: `to_dict()` and `from_dict()` methods ([#68])
* `delphin.mrs.xmrs.Dmrs`: `to_dict()` and `from_dict()` methods ([#68])
* `delphin.mrs.eds` ([#25], [#26])
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

* Fixed a regression in reading multiple SimpleMRSs ([#70])
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

## [v0.4.1]

**Release date: 2016-04-21**

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

## [v0.4.0]

**Release date: 2016-03-04**

This release fixes a number of bugs (including fixes from two new
contributors; see the [README]), and adds some minor features:

* more convenient introspection of TDL lists
* a LaTeX exporter for DMRS

From [v0.4.0], pyDelphin uses [semantic versioning](http://semver.org/),
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

## [v0.3]

**Release date: 2015-08-25**

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


## [v0.2]

**Release date: 2015-06-26**

There was no CHANGELOG file prior to this release, so I don't have much
information about changes, except for
[commit messages](../../commits/v0.2).

[v1.5.1]: ../../releases/tag/v1.5.1
[v1.5.0]: ../../releases/tag/v1.5.0
[v1.4.1]: ../../releases/tag/v1.4.1
[v1.4.0]: ../../releases/tag/v1.4.0
[v1.3.0]: ../../releases/tag/v1.3.0
[v1.2.4]: ../../releases/tag/v1.2.4
[v1.2.3]: ../../releases/tag/v1.2.3
[v1.2.2]: ../../releases/tag/v1.2.2
[v1.2.1]: ../../releases/tag/v1.2.1
[v1.2.0]: ../../releases/tag/v1.2.0
[v1.1.0]: ../../releases/tag/v1.1.0
[v1.0.3]: ../../releases/tag/v1.0.3
[v1.0.2]: ../../releases/tag/v1.0.2
[v1.0.1]: ../../releases/tag/v1.0.1
[v1.0.0]: ../../releases/tag/v1.0.0
[v0.9.2]: ../../releases/tag/v0.9.2
[v0.9.1]: ../../releases/tag/v0.9.1
[v0.9.0]: ../../releases/tag/v0.9.0
[v0.8.0]: ../../releases/tag/v0.8.0
[v0.7.2]: ../../releases/tag/v0.7.2
[v0.7.1]: ../../releases/tag/v0.7.1
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

[#8]: https://github.com/delph-in/pydelphin/issues/8
[#25]: https://github.com/delph-in/pydelphin/issues/25
[#26]: https://github.com/delph-in/pydelphin/issues/26
[#43]: https://github.com/delph-in/pydelphin/issues/43
[#66]: https://github.com/delph-in/pydelphin/issues/66
[#68]: https://github.com/delph-in/pydelphin/issues/68
[#68]: https://github.com/delph-in/pydelphin/issues/68
[#70]: https://github.com/delph-in/pydelphin/issues/70
[#75]: https://github.com/delph-in/pydelphin/issues/75
[#81]: https://github.com/delph-in/pydelphin/issues/81
[#82]: https://github.com/delph-in/pydelphin/issues/82
[#84]: https://github.com/delph-in/pydelphin/issues/84
[#85]: https://github.com/delph-in/pydelphin/issues/85
[#86]: https://github.com/delph-in/pydelphin/issues/86
[#86]: https://github.com/delph-in/pydelphin/issues/86
[#87]: https://github.com/delph-in/pydelphin/issues/87
[#89]: https://github.com/delph-in/pydelphin/issues/89
[#91]: https://github.com/delph-in/pydelphin/issues/91
[#92]: https://github.com/delph-in/pydelphin/issues/92
[#93]: https://github.com/delph-in/pydelphin/issues/93
[#95]: https://github.com/delph-in/pydelphin/issues/95
[#96]: https://github.com/delph-in/pydelphin/issues/96
[#97]: https://github.com/delph-in/pydelphin/issues/97
[#97]: https://github.com/delph-in/pydelphin/issues/97
[#98]: https://github.com/delph-in/pydelphin/issues/98
[#99]: https://github.com/delph-in/pydelphin/issues/99
[#100]: https://github.com/delph-in/pydelphin/issues/100
[#101]: https://github.com/delph-in/pydelphin/issues/101
[#103]: https://github.com/delph-in/pydelphin/issues/103
[#104]: https://github.com/delph-in/pydelphin/issues/104
[#104]: https://github.com/delph-in/pydelphin/issues/104
[#105]: https://github.com/delph-in/pydelphin/issues/105
[#105]: https://github.com/delph-in/pydelphin/issues/105
[#106]: https://github.com/delph-in/pydelphin/issues/106
[#107]: https://github.com/delph-in/pydelphin/issues/107
[#108]: https://github.com/delph-in/pydelphin/issues/108
[#109]: https://github.com/delph-in/pydelphin/issues/109
[#110]: https://github.com/delph-in/pydelphin/issues/110
[#111]: https://github.com/delph-in/pydelphin/issues/111
[#111]: https://github.com/delph-in/pydelphin/issues/111
[#112]: https://github.com/delph-in/pydelphin/issues/112
[#112]: https://github.com/delph-in/pydelphin/issues/112
[#114]: https://github.com/delph-in/pydelphin/issues/114
[#114]: https://github.com/delph-in/pydelphin/issues/114
[#115]: https://github.com/delph-in/pydelphin/issues/115
[#116]: https://github.com/delph-in/pydelphin/issues/116
[#117]: https://github.com/delph-in/pydelphin/issues/117
[#119]: https://github.com/delph-in/pydelphin/issues/119
[#125]: https://github.com/delph-in/pydelphin/issues/125
[#126]: https://github.com/delph-in/pydelphin/issues/126
[#128]: https://github.com/delph-in/pydelphin/issues/128
[#129]: https://github.com/delph-in/pydelphin/issues/129
[#133]: https://github.com/delph-in/pydelphin/issues/133
[#137]: https://github.com/delph-in/pydelphin/issues/137
[#138]: https://github.com/delph-in/pydelphin/issues/138
[#140]: https://github.com/delph-in/pydelphin/issues/140
[#141]: https://github.com/delph-in/pydelphin/issues/141
[#145]: https://github.com/delph-in/pydelphin/issues/145
[#148]: https://github.com/delph-in/pydelphin/issues/148
[#149]: https://github.com/delph-in/pydelphin/issues/149
[#150]: https://github.com/delph-in/pydelphin/issues/150
[#150]: https://github.com/delph-in/pydelphin/issues/150
[#150]: https://github.com/delph-in/pydelphin/issues/150
[#152]: https://github.com/delph-in/pydelphin/issues/152
[#153]: https://github.com/delph-in/pydelphin/issues/153
[#155]: https://github.com/delph-in/pydelphin/issues/155
[#156]: https://github.com/delph-in/pydelphin/issues/156
[#157]: https://github.com/delph-in/pydelphin/issues/157
[#160]: https://github.com/delph-in/pydelphin/issues/160
[#161]: https://github.com/delph-in/pydelphin/issues/161
[#164]: https://github.com/delph-in/pydelphin/issues/164
[#167]: https://github.com/delph-in/pydelphin/issues/167
[#167]: https://github.com/delph-in/pydelphin/issues/167
[#168]: https://github.com/delph-in/pydelphin/issues/168
[#168]: https://github.com/delph-in/pydelphin/issues/168
[#168]: https://github.com/delph-in/pydelphin/issues/168
[#168]: https://github.com/delph-in/pydelphin/issues/168
[#168]: https://github.com/delph-in/pydelphin/issues/168
[#169]: https://github.com/delph-in/pydelphin/issues/169
[#170]: https://github.com/delph-in/pydelphin/issues/170
[#172]: https://github.com/delph-in/pydelphin/issues/172
[#179]: https://github.com/delph-in/pydelphin/issues/179
[#180]: https://github.com/delph-in/pydelphin/issues/180
[#181]: https://github.com/delph-in/pydelphin/issues/181
[#186]: https://github.com/delph-in/pydelphin/issues/186
[#187]: https://github.com/delph-in/pydelphin/issues/187
[#190]: https://github.com/delph-in/pydelphin/issues/190
[#191]: https://github.com/delph-in/pydelphin/issues/191
[#192]: https://github.com/delph-in/pydelphin/issues/192
[#200]: https://github.com/delph-in/pydelphin/issues/200
[#203]: https://github.com/delph-in/pydelphin/issues/203
[#213]: https://github.com/delph-in/pydelphin/issues/213
[#219]: https://github.com/delph-in/pydelphin/issues/219
[#245]: https://github.com/delph-in/pydelphin/issues/245
[#246]: https://github.com/delph-in/pydelphin/issues/246
[#247]: https://github.com/delph-in/pydelphin/issues/247
[#248]: https://github.com/delph-in/pydelphin/issues/248
[#249]: https://github.com/delph-in/pydelphin/issues/249
[#250]: https://github.com/delph-in/pydelphin/issues/250
[#252]: https://github.com/delph-in/pydelphin/issues/252
[#253]: https://github.com/delph-in/pydelphin/issues/253
[#257]: https://github.com/delph-in/pydelphin/issues/257
[#261]: https://github.com/delph-in/pydelphin/issues/261
[#262]: https://github.com/delph-in/pydelphin/issues/262
[#263]: https://github.com/delph-in/pydelphin/issues/263
[#264]: https://github.com/delph-in/pydelphin/issues/264
[#266]: https://github.com/delph-in/pydelphin/issues/266
[#267]: https://github.com/delph-in/pydelphin/issues/267
[#268]: https://github.com/delph-in/pydelphin/issues/268
[#269]: https://github.com/delph-in/pydelphin/issues/269
[#270]: https://github.com/delph-in/pydelphin/issues/270
[#271]: https://github.com/delph-in/pydelphin/issues/271
[#273]: https://github.com/delph-in/pydelphin/issues/273
[#275]: https://github.com/delph-in/pydelphin/issues/275
[#276]: https://github.com/delph-in/pydelphin/issues/276
[#278]: https://github.com/delph-in/pydelphin/issues/278
[#279]: https://github.com/delph-in/pydelphin/issues/279
[#281]: https://github.com/delph-in/pydelphin/issues/281
[#282]: https://github.com/delph-in/pydelphin/issues/282
[#283]: https://github.com/delph-in/pydelphin/issues/283
[#285]: https://github.com/delph-in/pydelphin/issues/285
[#288]: https://github.com/delph-in/pydelphin/issues/288
[#289]: https://github.com/delph-in/pydelphin/issues/289
[#290]: https://github.com/delph-in/pydelphin/issues/290
[#291]: https://github.com/delph-in/pydelphin/issues/291
[#293]: https://github.com/delph-in/pydelphin/issues/293
[#294]: https://github.com/delph-in/pydelphin/issues/294
[#296]: https://github.com/delph-in/pydelphin/issues/296
[#301]: https://github.com/delph-in/pydelphin/issues/301
[#302]: https://github.com/delph-in/pydelphin/issues/302
[#303]: https://github.com/delph-in/pydelphin/issues/303
[#304]: https://github.com/delph-in/pydelphin/issues/304
[#306]: https://github.com/delph-in/pydelphin/issues/306
[#316]: https://github.com/delph-in/pydelphin/issues/316
[#319]: https://github.com/delph-in/pydelphin/issues/319
[#323]: https://github.com/delph-in/pydelphin/issues/323
[#324]: https://github.com/delph-in/pydelphin/issues/324
