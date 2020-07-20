# coding: utf-8

"""
Regular Expression Preprocessor (REPP)
"""

from typing import (
    TYPE_CHECKING,
    Optional,
    Union,
    NamedTuple,
    List,
    Tuple,
    Dict,
    Set,
    Pattern,
    Match,
    Iterable,
    Iterator,
)
from sre_parse import parse_template
from pathlib import Path
from array import array
import warnings
import logging

# use regex library if available; otherwise warn
try:
    import regex as re
    re.DEFAULT_VERSION = re.V1
    _regex_available = True
except ImportError:
    import re  # type: ignore
    _regex_available = False

from delphin.util import PathLike
from delphin.tokens import YYToken, YYTokenLattice
from delphin.lnk import Lnk
from delphin.exceptions import PyDelphinException, PyDelphinWarning
# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401


logger = logging.getLogger(__name__)


#: The tokenization pattern used if none is given in a REPP module.
DEFAULT_TOKENIZER = r'[ \t]+'


if TYPE_CHECKING:
    _CMap = array[int]  # characterization map
else:
    _CMap = array


class REPPError(PyDelphinException):
    """Raised when there is an error in tokenizing with REPP."""


class REPPWarning(PyDelphinWarning):
    """Issued when REPP may not behave as expected."""


if not _regex_available:
    warnings.warn(
        "The 'regex' library is not installed, so some regular expression "
        "features may not work as expected. Install PyDelphin with the "
        "[repp] extra to include the 'regex' library.",
        REPPWarning)


class REPPResult(NamedTuple):
    """
    The final result of REPP application.

    Attributes:
        string (str): resulting string after all rules have applied
        startmap (:py:class:`array`): integer array of start offsets
        endmap (:py:class:`array`): integer array of end offsets
    """
    string: str
    startmap: _CMap
    endmap: _CMap


class REPPStep(NamedTuple):
    """
    A single rule application in REPP.

    Attributes:
        input (str): input string (prior to application)
        output (str): output string (after application)
        operation: operation performed
        applied (bool): `True` if the rule was applied
        startmap (:py:class:`array`): integer array of start offsets
        endmap (:py:class:`array`): integer array of end offsets
    """
    input: str
    output: str
    operation: '_REPPOperation'
    applied: bool
    startmap: _CMap
    endmap: _CMap


_Trace = Iterator[Union[REPPStep, REPPResult]]


class _REPPOperation(object):
    """
    The supertype of REPP groups and rules.

    This class defines the apply(), trace(), and tokenize() methods
    which are available in [_REPPRule], [_REPPGroup],
    [_REPPIterativeGroup], and [REPP] instances.
    """
    def _apply(self, s: str, active: Set[str]) -> Iterator[REPPStep]:
        raise NotImplementedError()

    def apply(self, s: str, active: Iterable[str] = None) -> REPPResult:
        logger.info('apply(%r)', s)
        for step in self._trace(s, set(active or []), False):
            pass  # we only care about the last step
        assert isinstance(step, REPPResult)
        return step

    def trace(
        self, s: str, active: Iterable[str] = None, verbose: bool = False
    ) -> _Trace:
        logger.info('trace(%r)', s)
        yield from self._trace(s, set(active or []), verbose)

    def _trace(
        self, s: str, active: Set[str], verbose: bool
    ) -> _Trace:
        startmap = _zeromap(s)
        endmap = _zeromap(s)
        # initial boundaries
        startmap[0] = 1
        endmap[-1] = -1
        step = None
        for step in self._apply(s, active):
            if step.applied or verbose:
                yield step
            if step.applied:
                startmap = _mergemap(startmap, step.startmap)
                endmap = _mergemap(endmap, step.endmap)
        if step is not None:
            s = step.output
        yield REPPResult(s, startmap, endmap)

    def tokenize(
        self,
        s: str,
        pattern: str = DEFAULT_TOKENIZER,
        active: Iterable[str] = None
    ) -> YYTokenLattice:
        logger.info('tokenize(%r, %r)', s, pattern)
        res = self.apply(s, active=set(active or []))
        return self.tokenize_result(res, pattern=pattern)

    def tokenize_result(
            self, result: REPPResult, pattern: str = DEFAULT_TOKENIZER
    ) -> YYTokenLattice:
        logger.info('tokenize_result(%r, %r)', result, pattern)
        tokens = [
            YYToken(id=i, start=i, end=(i + 1),
                    lnk=Lnk.charspan(tok[0], tok[1]),
                    form=tok[2])
            for i, tok in enumerate(_tokenize(result, pattern))
        ]
        return YYTokenLattice(tokens)


class _REPPRule(_REPPOperation):
    """
    A REPP rewrite rule.

    The apply() method of this class works like re.sub() in Python's
    standard library, but it analyzes the replacement pattern in order
    to ensure that character positions in the resulting string can be
    traced back (as much as possible) to the original string.

    Args:
        pattern: the regular expression pattern to match
        replacement: the replacement template
    """
    def __init__(self, pattern: str, replacement: str):
        self.pattern = pattern
        self.replacement = replacement
        self._re = _compile(pattern)

        groups, literals = parse_template(replacement, self._re)
        # if a literal is None then it has a group, so make this
        # easier to iterate over by making pairs of (literal, None) or
        # (None, group)
        group_map = dict(groups)
        self._segments: List[Tuple[Optional[str], Optional[int]]] = [
            (literal, group_map.get(i))
            for i, literal
            in enumerate(literals)
        ]
        # either literal or group must be None, but not both
        assert all((lit is None) != (grp is None)
                   for lit, grp in self._segments)

        # Get "trackable" capture groups; i.e., those that are
        # transparent for characterization. For PET behavior, these
        # must appear in strictly increasing order with no gaps
        self._last_trackable = -1  # index of trackable segment, not group id
        last_trackable_group = 0
        for i, group in groups:
            if group == last_trackable_group + 1:
                self._last_trackable = i
                last_trackable_group = group
            else:
                break

    def __str__(self):
        return f'!{self.pattern}\t\t{self.replacement}'

    def _apply(self, s: str, active: Set[str]) -> Iterator[REPPStep]:
        logger.debug(' %s', self)

        ms = list(self._re.finditer(s))

        if ms:
            pos = 0  # current position in the original string
            shift = 0  # current original/target length difference
            parts: List[str] = []
            smap = array('i', [0])
            emap = array('i', [0])

            for m in ms:
                start = m.start()
                if pos < start:
                    _copy_part(s[pos:start], shift, parts, smap, emap)

                if self._segments:
                    for literal, start, end, tracked in self._itersegments(m):
                        if tracked:
                            _copy_part(literal, shift, parts, smap, emap)
                        else:
                            width = end - start
                            _insert_part(literal, width, shift, parts,
                                         smap, emap)
                            shift += width - len(literal)
                else:
                    # the replacement is empty (match is deleted)
                    shift += m.end() - start

                pos = m.end()

            if pos < len(s):
                _copy_part(s[pos:], shift, parts, smap, emap)
            smap.append(shift)
            emap.append(shift - 1)
            o = ''.join(parts)
            applied = True

        else:
            o = s
            smap = _zeromap(o)
            emap = _zeromap(o)
            applied = False

        yield REPPStep(s, o, self, applied, smap, emap)

    def _itermatches(
            self, ms: Iterable[Match[str]]
    ) -> Iterator[Tuple[int, Match[str]]]:
        """Yield pairs of the last affected position and a match."""
        last_pos = 0
        for m in ms:
            yield (last_pos, m)
            last_pos = m.end()

    def _itersegments(
            self, m: Match[str]
    ) -> Iterator[Tuple[str, int, int, bool]]:
        """Yield tuples of (replacement, start, end, tracked)."""
        start = m.start()

        # first yield segments that might be trackable
        tracked = self._segments[:self._last_trackable + 1]
        if tracked:
            spans = {group: m.span(group)
                     for _, group in tracked
                     if group is not None}
            end = m.start(1)  # if literal before tracked group
            for literal, group in tracked:
                if literal is None:
                    assert group is not None
                    start, end = spans[group]
                    yield (m.group(group) or '', start, end, True)
                    start = end
                    if group + 1 in spans:
                        end = spans[group + 1][0]
                else:
                    assert literal is not None
                    yield (literal, start, end, False)

        # then group all remaining segments together
        remaining: List[Optional[str]] = [
            m.group(grp) if grp is not None else lit
            for lit, grp in self._segments[self._last_trackable + 1:]
        ]
        if remaining:
            # in some cases m.group(grp) can return None, so replace with ''
            literal = ''.join(segment or '' for segment in remaining)
            yield (literal, start, m.end(), False)


class _REPPGroup(_REPPOperation):
    def __init__(
            self, operations: List[_REPPOperation] = None, name: str = None
    ):
        if operations is None:
            operations = []
        self.operations: List[_REPPOperation] = operations
        self.name = name

    def __repr__(self):
        name = '("{}") '.format(self.name) if self.name is not None else ''
        return '<{} object {}at {}>'.format(
            type(self).__name__, name, id(self)
        )

    def __str__(self):
        return 'Module {}'.format(self.name if self.name is not None else '')

    def _apply(self, s: str, active: Set[str]) -> Iterator[REPPStep]:
        o = s
        applied = False
        for operation in self.operations:
            for step in operation._apply(o, active):
                yield step
                o = step.output
                applied |= step.applied

        yield REPPStep(s, o, self, applied, _zeromap(o), _zeromap(o))


class _REPPGroupCall(_REPPOperation):
    def __init__(self, name: str, modules: Dict[str, 'REPP']):
        self.name = name
        self.modules = modules

    def _apply(self, s: str, active: Set[str]) -> Iterator[REPPStep]:
        if active is not None and self.name in active:
            logger.info('>%s', self.name)
            yield from self.modules[self.name]._apply(s, active)
            logger.debug('>%s (done)', self.name)
        else:
            logger.debug('>%s (inactive)', self.name)


class _REPPIterativeGroup(_REPPGroup):
    def __str__(self):
        return f'Internal group #{self.name}'

    def _apply(self, s: str, active: Set[str]) -> Iterator[REPPStep]:
        logger.debug('>%s', self.name)
        o = s
        applied = False
        prev = None
        i = 0
        while prev != o:
            i += 1
            prev = o
            for operation in self.operations:
                for step in operation._apply(o, active):
                    yield step
                    o = step.output
                    applied |= step.applied
            yield REPPStep(s, o, self, applied, _zeromap(o), _zeromap(o))
        logger.debug('>%s (done; iterated %d time(s))', self.name, i)


class REPP(object):
    """
    A Regular Expression Pre-Processor (REPP).

    The normal way to create a new REPP is to read a .rpp file via the
    :meth:`from_file` classmethod. For REPPs that are defined in code,
    there is the :meth:`from_string` classmethod, which parses the same
    definitions but does not require file I/O. Both methods, as does
    the class's `__init__()` method, allow for pre-loaded and named
    external *modules* to be provided, which allow for external group
    calls (also see :meth:`from_file` or implicit module loading). By
    default, all external submodules are deactivated, but they can be
    activated by adding the module names to *active* or, later, via the
    :meth:`activate` method.

    A third classmethod, :meth:`from_config`, reads a PET-style
    configuration file (e.g., `repp.set`) which may specify the
    available and active modules, and therefore does not take the
    *modules* and *active* parameters.

    Args:
        name (str, optional): the name assigned to this module
        modules (dict, optional): a mapping from identifiers to REPP
            modules
        active (iterable, optional): an iterable of default module
            activations
    """

    def __init__(
            self,
            name: str = None,
            modules: Dict[str, 'REPP'] = None,
            active: Iterable[str] = None):
        self.info: Optional[str] = None
        self.tokenize_pattern: Optional[str] = None
        self.group = _REPPGroup(name=name)

        if modules is None:
            modules = {}
        self.modules = dict(modules)
        self.active: Set[str] = set()
        if active is None:
            active = []
        for mod in active:
            self.activate(mod)

    @classmethod
    def from_config(cls, path: PathLike, directory=None):
        """
        Instantiate a REPP from a PET-style `.set` configuration file.

        The *path* parameter points to the configuration file.
        Submodules are loaded from *directory*. If *directory* is not
        given, it is the directory part of *path*.

        Args:
            path (str): the path to the REPP configuration file
            directory (str, optional): the directory in which to search
                for submodules
        """
        path = Path(path).expanduser()
        if not path.is_file():
            raise REPPError(f'REPP config file not found: {path!s}')
        confdir = path.parent

        # TODO: can TDL parsing be repurposed for this variant?
        conf = path.read_text(encoding='utf-8')
        conf = re.sub(r';.*', '', conf).replace('\n', ' ')
        m = re.search(
            r'repp-modules\s*:=\s*((?:[-\w]+\s+)*[-\w]+)\s*\.', conf)
        t = re.search(
            r'repp-tokenizer\s*:=\s*([-\w]+)\s*\.', conf)
        a = re.search(
            r'repp-calls\s*:=\s*((?:[-\w]+\s+)*[-\w]+)\s*\.', conf)
        # f = re.search(
        #     r'format\s*:=\s*(\w+)\s*\.', conf)
        d = re.search(
            r'repp-directory\s*:=\s*(.*)\.\s*$', conf)

        if m is None:
            raise REPPError('repp-modules option must be set')
        if t is None:
            raise REPPError('repp-tokenizer option must be set')

        # mods = m.group(1).split()
        tok = t.group(1).strip()
        active = a.group(1).split() if a is not None else None
        # fmt = f.group(1).strip() if f is not None else None

        if directory is None:
            if d is not None:
                directory = d.group(1).strip(' "')
            elif confdir.joinpath(tok + '.rpp').is_file():
                directory = confdir
            elif confdir.joinpath('rpp', tok + '.rpp').is_file():
                directory = confdir.joinpath('rpp')
            elif confdir.joinpath('../rpp', tok + '.rpp').is_file():
                directory = confdir.joinpath('../rpp')
            else:
                raise REPPError('Could not find a suitable REPP directory.')

        # ignore repp-modules and format?
        return REPP.from_file(
            directory.joinpath(tok + '.rpp'),
            directory=directory,
            active=active
        )

    @classmethod
    def from_file(cls, path, directory=None, modules=None, active=None):
        """
        Instantiate a REPP from a `.rpp` file.

        The *path* parameter points to the top-level module. Submodules
        are loaded from *directory*. If *directory* is not given, it is
        the directory part of *path*.

        A REPP module may utilize external submodules, which may be
        defined in two ways. The first method is to map a module name
        to an instantiated REPP instance in *modules*. The second
        method assumes that an external group call `>abc` corresponds
        to a file `abc.rpp` in *directory* and loads that file. The
        second method only happens if the name (e.g., `abc`) does not
        appear in *modules*. Only one module may define a tokenization
        pattern.

        Args:
            path (str): the path to the base REPP file to load
            directory (str, optional): the directory in which to search
                for submodules
            modules (dict, optional): a mapping from identifiers to
                REPP modules
            active (iterable, optional): an iterable of default module
                activations
        """
        path = Path(path).expanduser()
        if directory is not None:
            directory = Path(directory).expanduser()
        else:
            directory = path.parent
        name = path.with_suffix('').name
        lines = _repp_lines(path)
        r = cls(name=name, modules=modules, active=active)
        _parse_repp(lines, r, directory)
        return r

    @classmethod
    def from_string(cls, s, name=None, modules=None, active=None):
        """
        Instantiate a REPP from a string.

        Args:
            name (str, optional): the name of the REPP module
            modules (dict, optional): a mapping from identifiers to
                REPP modules
            active (iterable, optional): an iterable of default module
                activations
        """
        r = cls(name=name, modules=modules, active=active)
        _parse_repp(s.splitlines(), r, None)
        return r

    def activate(self, mod: str) -> None:
        """
        Set external module *mod* to active.
        """
        self.active.add(mod)

    def deactivate(self, mod: str) -> None:
        """
        Set external module *mod* to inactive.
        """
        if mod in self.active:
            self.active.remove(mod)

    def _apply(self, s: str, active: Set[str]) -> Iterator[REPPStep]:
        return self.group._apply(s, active)

    def apply(self, s: str, active: Iterable[str] = None) -> REPPResult:
        """
        Apply the REPP's rewrite rules to the input string *s*.

        Args:
            s (str): the input string to process
            active (optional): a collection of external module names
                that may be applied if called
        Returns:
            a :class:`REPPResult` object containing the processed
                string and characterization maps
        """
        if active is None:
            active = self.active
        else:
            active = set(active)
        return self.group.apply(s, active=active)

    def trace(
        self, s: str, active: Iterable[str] = None, verbose: bool = False
    ) -> _Trace:
        """
        Rewrite string *s* like `apply()`, but yield each rewrite step.

        Args:
            s (str): the input string to process
            active (optional): a collection of external module names
                that may be applied if called
            verbose (bool, optional): if `False`, only output rules or
                groups that matched the input
        Yields:
            a :class:`REPPStep` object for each intermediate rewrite
                step, and finally a :class:`REPPResult` object after
                the last rewrite
        """
        if active is None:
            active = self.active
        return self.group.trace(s, active=active, verbose=verbose)

    def tokenize(
            self, s: str, pattern: str = None, active: Iterable[str] = None
    ) -> YYTokenLattice:
        """
        Rewrite and tokenize the input string *s*.

        Args:
            s (str): the input string to process
            pattern (str, optional): the regular expression pattern on
                which to split tokens; defaults to `[ \t]+`
            active (optional): a collection of external module names
                that may be applied if called
        Returns:
            a :class:`~delphin.tokens.YYTokenLattice` containing the
            tokens and their characterization information
        """
        if pattern is None:
            if self.tokenize_pattern is None:
                pattern = DEFAULT_TOKENIZER
            else:
                pattern = self.tokenize_pattern
        if active is None:
            active = self.active
        return self.group.tokenize(s, pattern=pattern, active=active)

    def tokenize_result(
            self, result: REPPResult, pattern: str = DEFAULT_TOKENIZER
    ) -> YYTokenLattice:
        """
        Tokenize the result of rule application.

        Args:
            result: a :class:`REPPResult` object
            pattern (str, optional): the regular expression pattern on
                which to split tokens; defaults to `[ \t]+`
        Returns:
            a :class:`~delphin.tokens.YYTokenLattice` containing the
            tokens and their characterization information
        """
        return self.group.tokenize_result(result, pattern=pattern)


def _compile(pattern: str) -> Pattern[str]:
    try:
        return re.compile(pattern)
    except re.error:
        if _regex_available and '[' in pattern or ']' in pattern:
            warnings.warn(
                'Invalid regex in REPP; see warning log for details.',
                REPPWarning)
            logger.warn("Possible unescaped brackets in %r; "
                        "attempting to parse in compatibility mode",
                        pattern)
            return re.compile(pattern, flags=re.V0)
        else:
            raise


def _zeromap(s: str) -> _CMap:
    return array('i', [0] * (len(s) + 2))


def _mergemap(map1: _CMap, map2: _CMap) -> _CMap:
    """
    Positions in map2 have an integer indicating the relative shift to
    the equivalent position in map1. E.g., the i'th position in map2
    corresponds to the i + map2[i] position in map1.
    """
    merged = array('i', [0] * len(map2))
    for i, shift in enumerate(map2):
        newshift = shift + map1[i + shift]
        merged[i] = newshift
    return merged


def _copy_part(
        s: str,
        shift: int,
        parts: List[str],
        smap: _CMap,
        emap: _CMap
) -> None:
    parts.append(s)
    smap.extend([shift] * len(s))
    emap.extend([shift] * len(s))


def _insert_part(
        s: str,
        w: int,
        shift: int,
        parts: List[str],
        smap: _CMap,
        emap: _CMap
) -> None:
    parts.append(s)
    a = shift
    b = a - len(s)
    smap.extend(range(a, b, -1))
    a = shift + w - 1
    b = a - len(s)
    emap.extend(range(a, b, -1))


def _tokenize(result: REPPResult, pattern: str) -> List[Tuple[int, int, str]]:
    s, sm, em = result  # unpack for efficiency in loop
    toks = []
    pos = 0
    for m in re.finditer(pattern, result.string):
        if pos < m.start():
            toks.append((pos + sm[pos + 1],
                         m.start() + em[m.start()],
                         s[pos:m.start()]))
        pos = m.end()
    if pos < len(s):
        toks.append((pos + sm[pos + 1],
                     len(s) + em[len(s)],
                     s[pos:]))
    return toks


def _repp_lines(path: Path) -> List[str]:
    if not path.is_file():
        raise REPPError(f'REPP file not found: {path!s}')
    return path.read_text(encoding='utf-8').splitlines()


def _parse_repp(lines: List[str], r: REPP, directory: Path) -> None:
    ops = list(_parse_repp_group(lines, r, directory))
    if lines:
        raise REPPError('Unexpected termination; maybe the # operator '
                        'appeared without an internal group.')
    r.group.operations.extend(ops)


def _parse_repp_group(
    lines: List[str], r: REPP, directory: Path
) -> Iterator[_REPPOperation]:
    igs: Dict[str, _REPPIterativeGroup] = {}  # internal groups
    while lines:
        line = lines.pop(0)
        if line.startswith(';') or line.strip() == '':
            continue  # skip comments and empty lines
        elif line[0] == '!':
            match = re.match(r'([^\t]+)\t+(.*)', line[1:])
            if match is None:
                raise REPPError(f'Invalid rewrite rule: {line}')
            yield _REPPRule(match.group(1), match.group(2))
        elif line[0] == '<':
            fn = directory.joinpath(line[1:].rstrip())
            lines = _repp_lines(fn) + lines
        elif line[0] == '>':
            modname = line[1:].rstrip()
            if modname.isdigit():
                if modname in igs:
                    yield igs[modname]
                else:
                    raise REPPError(
                        'Iterative group not defined: ' + modname
                    )
            else:
                if modname not in r.modules:
                    if directory is None:
                        raise REPPError('Cannot implicitly load modules if '
                                        'a directory is not given.')
                    mod = REPP.from_file(
                        directory.joinpath(modname + '.rpp'),
                        directory=directory,
                        modules=r.modules
                    )
                    r.modules[modname] = mod
                yield _REPPGroupCall(modname, r.modules)
        elif line[0] == '#':
            igname = line[1:].rstrip()
            if igname.isdigit():
                if igname in igs:
                    raise REPPError(
                        'Internal group name already defined: ' + igname
                    )
                igs[igname] = _REPPIterativeGroup(
                    operations=list(
                        _parse_repp_group(lines, r, directory)
                    ),
                    name=igname
                )
            elif igname == '':
                return
            else:
                raise REPPError('Invalid internal group name: ' + igname)
        elif line[0] == ':':
            if r.tokenize_pattern is not None:
                raise REPPError(
                    'Only one tokenization pattern (:) may be defined.'
                )
            r.tokenize_pattern = line[1:]
        elif line[0] == '@':
            if r.info is not None:
                raise REPPError(
                    'No more than one meta-info declaration (@) may be '
                    'defined.'
                )
            r.info = line[1:]
        else:
            raise REPPError(f'Invalid declaration: {line}')
