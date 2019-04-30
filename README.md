# PyDelphin &mdash; Python libraries for DELPH-IN data

[![PyPI Version](https://img.shields.io/pypi/v/pydelphin.svg)](https://pypi.org/project/PyDelphin/)
![Python Support](https://img.shields.io/pypi/pyversions/pydelphin.svg)
[![Build Status](https://travis-ci.org/delph-in/pydelphin.svg?branch=develop)](https://travis-ci.org/delph-in/pydelphin)
[![Documentation Status](https://readthedocs.org/projects/pydelphin/badge/?version=latest)](https://pydelphin.readthedocs.io/en/latest/?badge=latest)

[DELPH-IN](http://delph-in.net) is an international consortium of
researchers committed to producing precise, high-quality language
processing tools and resources, primarily in the
[HPSG](http://hpsg.stanford.edu/) syntactic and
[MRS](http://moin.delph-in.net/RmrsTop) semantic frameworks, and
PyDelphin is a suite of Python libraries for processing data and
interacting with tools in the DELPH-IN ecosystem. PyDelphin's goal is
to lower the barriers to making use of DELPH-IN resources to help
users quickly build applications or perform experiments, and it has
been successfully used for research into machine translation (e.g.,
[Goodman, 2018][]), sentence chunking ([Muszyńska, 2016][]),
neural semantic parsing ([Buys & Blunsom, 2017][]), and more.

[Goodman, 2018]: https://goodmami.org/static/goodman-dissertation.pdf
[Muszyńska, 2016]: http://www.aclweb.org/anthology/P/P16/P16-3014.pdf
[Buys & Blunsom,  2017]: http://www.aclweb.org/anthology/P/P17/P17-1112.pdf

Documentation, including tutorials and an API reference, is available here:
http://pydelphin.readthedocs.io/

New to PyDelphin? Want to see examples? Try the
[walkthrough](https://pydelphin.readthedocs.io/en/latest/tutorials/walkthrough.html).

## Installation and Upgrading

Get the latest release of PyDelphin from [PyPI][]:

```bash
$ pip install pydelphin
```

[PyPI]: https://pypi.python.org/pypi/pyDelphin

For more information about requirements, installing from source, and
running unit tests, please see the
[documentation](https://pydelphin.readthedocs.io/en/latest/tutorials/setup.html).

API changes in new versions are documented in the
[CHANGELOG](CHANGELOG.md), but for any unexpected changes please
[file an issue](https://github.com/delph-in/pydelphin/issues).

## Features

PyDelphin implements the following DELPH-IN specifications:

Semantic Representations:
- [`delphin.mrs`][]:  [Minimal Recursion Semantics](http://moin.delph-in.net/MrsRfc)
- [`delphin.eds`][]:  [Elementary Dependency Structures](http://moin.delph-in.net/EdsTop)
- [`delphin.dmrs`][]: [Dependency Minimal Recursion Semantics](http://moin.delph-in.net/RmrsDmrs)

Semantic Components and Interfaces:
- [`delphin.semi`][]:      [Semantic Interface](http://moin.delph-in.net/SemiRfc)
- [`delphin.vpm`][]:       [Variable Property Mapping](http://moin.delph-in.net/RmrsVpm)
- [`delphin.variable`][]:  MRS variables
- [`delphin.predicate`][]: [Semantic Predicates](http://moin.delph-in.net/PredicateRfc)
- [`delphin.scope`][]:     Underspecified scope
- [`delphin.lnk`][]:       Lnk surface alignments

Grammar and Parse Inspection
- [`delphin.derivation`][]: [Derivation trees](http://moin.delph-in.net/ItsdbDerivations)
- [`delphin.tdl`][]:        [Type-Description Language](http://moin.delph-in.net/TdlRfc)
- [`delphin.tfs`][]:        Feature structures and type hierarchies

Tokenization:
- [`delphin.repp`][]:   [Regular-Expression PreProcessor](http://moin.delph-in.net/ReppTop)
- [`delphin.tokens`][]: [YY Token lattices](http://moin.delph-in.net/PetInput#YY_Input_Mode)

Corpus Management and Processing
- [`delphin.itsdb`][]: [\[incr tsdb()\]](http://moin.delph-in.net/ItsdbTop) profiles
- [`delphin.tsql`][]:  [TSQL](http://moin.delph-in.net/TsqlRfc) test suite queries

In addition, PyDelphin provides the following packages and tools for convenience:

- [`delphin.commands`][]:        Functional or CLI interface to common tasks
- [`delphin.interfaces.ace`][]:  Python wrapper for common tasks using [ACE](http://sweaglesw.org/linguistics/ace/)
- [`delphin.interfaces.rest`][]: Client for the [web API](http://moin.delph-in.net/ErgApi)
- [`delphin.extra.highlight`][]: [Pygments](http://pygments.org/)-based syntax highlighting (currently just for TDL and SimpleMRS)
- [`delphin.extra.latex`][]:     Formatting for LaTeX (just DMRS)


[`delphin.commands`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.commands.html
[`delphin.derivation`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.derivation.html
[`delphin.dmrs`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.dmrs.html
[`delphin.eds`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.eds.html
[`delphin.extra.highlight`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.extra.html#module-delphin.extra.highlight
[`delphin.extra.latex`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.extra.html#module-delphin.extra.latex
[`delphin.interfaces.ace`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.interfaces.ace.html
[`delphin.interfaces.rest`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.interfaces.rest.html
[`delphin.itsdb`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.itsdb.html
[`delphin.lnk`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.lnk.html
[`delphin.mrs`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.mrs.html
[`delphin.predicate`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.predicate.html
[`delphin.repp`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.repp.html
[`delphin.scope`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.scope.html
[`delphin.semi`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.semi.html
[`delphin.tdl`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.tdl.html
[`delphin.tfs`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.tfs.html
[`delphin.tokens`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.tokens.html
[`delphin.tsql`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.tsql.html
[`delphin.variable`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.variable.html
[`delphin.vpm`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.vpm.html


## Other Information

### Contributors

PyDelphin is developed and maintained by several contributors:

- [Michael Wayne Goodman](https://github.com/goodmami/) (primary author)
- [T.J. Trimble](https://github.com/dantiston/) (packaging, derivations, ACE)
- [Guy Emerson](https://github.com/guyemerson/) (MRS)
- [Alex Kuhnle](https://github.com/AlexKuhnle/) (MRS, ACE)
- [Francis Bond](https://github.com/fcbond/) (LaTeX export)
- [Angie McMillan-Major](https://github.com/mcmillanmajora/) (maintainer)

### Related Software

* Parser/Generators (chronological order)
  - LKB: http://moin.delph-in.net/LkbTop (also: http://moin.delph-in.net/LkbFos)
  - PET: http://moin.delph-in.net/PetTop
  - ACE: http://sweaglesw.org/linguistics/ace/
  - agree: http://moin.delph-in.net/AgreeTop
* Grammar profiling, testing, and analysis
  - \[incr tsdb()\]: http://www.delph-in.net/itsdb/
  - gDelta: https://github.com/ned2/gdelta
  - Typediff: https://github.com/ned2/typediff
  - gTest: https://github.com/goodmami/gtest
* Software libraries and repositories
  - LOGON: http://moin.delph-in.net/LogonTop
  - pydmrs: https://github.com/delph-in/pydmrs
* Also see (may have overlap with the above):
  - http://moin.delph-in.net/ToolsTop
  - http://moin.delph-in.net/DelphinApplications

### Spelling

Earlier versions of PyDelphin were spelled "pyDelphin" with a
lower-case "p" and this form is used in several publications. The
current recommended spelling has an upper-case "P".
