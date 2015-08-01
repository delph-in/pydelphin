# Change Log

## [Unreleased][unreleased]

This release simplifies the pyDelphin core classes and improves
performance for many MRS tasks. Most significantly, the inspection of
Xmrs objects by their components is done internally with basic tuple
(or namedtuple) and dict types, but the old "classy" interface can be
had with functions in delphin.mrs.components. This release also improves
Python 2 compatibility, and co-occurs with improved documentation and
unit tests for pyDelphin.

### Added

* use setuptools for setup.py
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
* delphin.itsdb.ItsdbSkeleton
* recipes/ package for small, useful snippets (which also show how to
  use pyDelphin as a library)
  - recipes.semantics.contiguous_semantic_constituents()
* tests.mrs_compare_test

### Fixed

* Python 2.6+ compatibility
  - delphin._exceptions.TdlParsingError
* delphin.mrs.simplemrs no longer crashes if variable properties are
  specified on the HCONS or ICONS lists (but the varprops are ignored)
* Xmrs now converts variable properties to lists on construction, in
  case a dict is given (which caused problems during serialization).

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
    - Lnk parameters are reversed: Lnk(type, data) (I don't remember
      why, though)
  - config.QUANTIFIER_SORT renamed to QUANTIFIER_POS
  - simplemrs.load() and loads() take a "strict" parameter (if True,
    more tests are performed during parsing)
  - dmrx.loads() no longer has an "encoding" parameter
  - mrx
    - loads() no longer takes an "encoding" parameter
    - has (untested) support for hypothetical ICONS data
  - query
    - select_eps() and select_args() "anchor" parameter is renamed to
      "nodeid"
    - select_icons() "target" and "clause" parameters renamed to "left"
      and "right", respectively
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
[commit messages](https://github.com/goodmami/pydelphin/commits/v0.2).

[unreleased]: https://github.com/goodmami/pydelphin/tree/develop
[v0.3]: https://github.com/goodmami/pydelphin/releases/tag/v0.3
[v0.2]: https://github.com/goodmami/pydelphin/releases/tag/v0.2
