# PyDelphin &mdash; Python libraries for DELPH-IN data

[![PyPI Version](https://img.shields.io/pypi/v/pydelphin.svg)](https://pypi.org/project/PyDelphin/)
![Python Support](https://img.shields.io/pypi/pyversions/pydelphin.svg)
[![Test Status](https://github.com/delph-in/pydelphin/workflows/tests/badge.svg)](https://github.com/delph-in/pydelphin/actions?query=workflow%3A%22tests%22)
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
[Goodman, 2018]), sentence chunking ([Muszyńska, 2016]), neural
semantic parsing ([Buys & Blunsom, 2017]), natural language
generation ([Hajdik et al., 2019]), and more.

[Goodman, 2018]: https://goodmami.org/static/goodman-dissertation.pdf
[Muszyńska, 2016]: https://www.aclweb.org/anthology/P16-3014
[Buys & Blunsom,  2017]: https://www.aclweb.org/anthology/P17-1112
[Hajdik et al., 2019]: https://www.aclweb.org/anthology/N19-1235

Documentation, including guides and an API reference, is available here:
http://pydelphin.readthedocs.io/

New to PyDelphin? Want to see examples? Try the
[walkthrough](https://pydelphin.readthedocs.io/en/latest/guides/walkthrough.html).

## Installation and Upgrading

Get the latest release of PyDelphin from [PyPI]:

```bash
$ pip install pydelphin
```

[PyPI]: https://pypi.python.org/pypi/PyDelphin

For more information about requirements, installing from source, and
running unit tests, please see the
[documentation](https://pydelphin.readthedocs.io/en/latest/guides/setup.html).

API changes in new versions are documented in the
[CHANGELOG](CHANGELOG.md), but for any unexpected changes please [file
an issue][issues].

[issues]: https://github.com/delph-in/pydelphin/issues/

## Features

PyDelphin contains the following modules:

Semantic Representations:
- [`delphin.mrs`]:  [Minimal Recursion Semantics](http://moin.delph-in.net/MrsRfc)
- [`delphin.eds`]:  [Elementary Dependency Structures](http://moin.delph-in.net/EdsTop)
- [`delphin.dmrs`]: [Dependency Minimal Recursion Semantics](http://moin.delph-in.net/RmrsDmrs)

Semantic Components and Interfaces:
- [`delphin.semi`]:      [Semantic Interface](http://moin.delph-in.net/SemiRfc)
- [`delphin.vpm`]:       [Variable Property Mapping](http://moin.delph-in.net/RmrsVpm)
- [`delphin.variable`]:  MRS variables
- [`delphin.predicate`]: [Semantic Predicates](http://moin.delph-in.net/PredicateRfc)
- [`delphin.scope`]:     Underspecified scope
- [`delphin.sembase`]:   Basic semantic structures
- [`delphin.codecs`]:    A wide variety of serialization codecs for MRS, EDS, and DMRS

Grammar and Parse Inspection:
- [`delphin.derivation`]: [Derivation trees](http://moin.delph-in.net/ItsdbDerivations)
- [`delphin.tdl`]:        [Type-Description Language](http://moin.delph-in.net/TdlRfc)
- [`delphin.tfs`]:        Feature structures and type hierarchies

Tokenization:
- [`delphin.repp`]:   [Regular-Expression PreProcessor](http://moin.delph-in.net/ReppTop)
- [`delphin.tokens`]: [YY Token lattices](http://moin.delph-in.net/PetInput#YY_Input_Mode)
- [`delphin.lnk`]:    Lnk surface alignments

Corpus Management and Processing:
- [`delphin.itsdb`]: [\[incr tsdb()\]](http://moin.delph-in.net/ItsdbTop) profiles
- [`delphin.tsdb`]: Low-level interface to test suite databases
- [`delphin.tsql`]:  [TSQL](http://moin.delph-in.net/TsqlRfc) test suite queries

Interfaces with External Processors:
- [`delphin.interface`]: Structures for interacting with external processors
- [`delphin.ace`]:       Python wrapper for common tasks using [ACE](http://sweaglesw.org/linguistics/ace/)
- [`delphin.web`]:       Client for the [web API](http://moin.delph-in.net/ErgApi)

Core Components and Command Line Interface:
- [`delphin.commands`]:   Functional interface to common tasks
- [`delphin.cli`]:        Command-line interface to functional commands
- [`delphin.hierarchy`]:  Multiple-inheritance hierarchies
- [`delphin.exceptions`]: PyDelphin's basic exception classes


[`delphin.cli`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.cli.html
[`delphin.codecs`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.codecs.html
[`delphin.commands`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.commands.html
[`delphin.derivation`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.derivation.html
[`delphin.dmrs`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.dmrs.html
[`delphin.eds`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.eds.html
[`delphin.exceptions`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.exceptions.html
[`delphin.hierarchy`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.hierarchy.html
[`delphin.interface`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.interface.html
[`delphin.ace`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.ace.html
[`delphin.web`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.web.html
[`delphin.tsdb`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.tsdb.html
[`delphin.itsdb`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.itsdb.html
[`delphin.lnk`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.lnk.html
[`delphin.mrs`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.mrs.html
[`delphin.predicate`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.predicate.html
[`delphin.repp`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.repp.html
[`delphin.scope`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.scope.html
[`delphin.sembase`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.sembase.html
[`delphin.semi`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.semi.html
[`delphin.tdl`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.tdl.html
[`delphin.tfs`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.tfs.html
[`delphin.tokens`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.tokens.html
[`delphin.tsql`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.tsql.html
[`delphin.variable`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.variable.html
[`delphin.vpm`]: https://pydelphin.readthedocs.io/en/latest/api/delphin.vpm.html


## Other Information

### Getting Help

Please use the [issue tracker][issues] for bug reports, feature
requests, and PyDelphin-specific questions. For more general questions
and support, try one of the following channels maintained by the
DELPH-IN community:

- [DELPH-IN Discourse](https://delphinqa.ling.washington.edu/) forums
- [developers](http://lists.delph-in.net/mailman/listinfo/developers)
  mailing list

### Citation

Please use the following for academic citations (and see: https://ieeexplore.ieee.org/abstract/document/8939628):

```bibtex
@INPROCEEDINGS{Goodman:2019,
  author={Goodman, Michael Wayne},
  title={A Python Library for Deep Linguistic Resources},
  booktitle={2019 Pacific Neighborhood Consortium Annual Conference and Joint Meetings (PNC)},
  year={2019},
  month=oct,
  address={Singapore},
  keywords={research software;linguistics;semantics;HPSG;computational linguistics;natural language processing;open source software}
}
```

### Acknowledgments

Thanks to PyDelphin's
[contributors](https://github.com/delph-in/pydelphin/graphs/contributors)
and all who've participated by filing issues and feature
requests. Also thanks to the users of PyDelphin!

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
