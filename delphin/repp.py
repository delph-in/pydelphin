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
from itertools import takewhile
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

# Mask values
_MASK_B = 1  # start of mask
_MASK_I = 2  # inside mask
_MASK_O = 0  # not masked


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
        mask (:py:class:`array`): integer array of mask indicators
    """
    input: str
    output: str
    operation: '_REPPOperation'
    applied: bool
    startmap: _CMap
    endmap: _CMap
    mask: _CMap  # BIO scheme, B=1, I=2, O=0


_Trace = Iterator[Union[REPPStep, REPPResult]]


class _REPPOperation:
    """
    The supertype of REPP groups and rules.

    This class defines the apply(), trace(), and tokenize() methods
    which are available in [_REPPRule], [_REPPGroup],
    [_REPPInternalGroup], and [REPP] instances.
    """

    def _apply(
        self,
        s: str,
        active: Set[str],
        mask: _CMap
    ) -> Iterator[REPPStep]:
        raise NotImplementedError()


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
        self._tracked, self._untracked = _get_segments(replacement, self._re)

    def __str__(self):
        return f'!{self.pattern}\t\t{self.replacement}'

    def _apply(
        self,
        s: str,
        active: Set[str],
        mask: _CMap
    ) -> Iterator[REPPStep]:
        logger.debug(' %s', self)

        applied = False
        ms = list(self._re.finditer(s))

        if ms:
            pos = 0  # current position in the original string
            shift = 0  # current original/target length difference
            parts: List[str] = []
            smap = array('i', [0])
            emap = array('i', [0])
            new_mask = array('i', [_MASK_O])

            for m in ms:
                sub, _smap, _emap, _mask, delta, blocked = _process_match(
                    m, mask, shift, self._tracked, self._untracked
                )
                if blocked:
                    continue
                applied = True

                start = m.start()

                # copy up to point of match
                if pos < start:
                    _copy_part(s[pos:start], shift, parts, smap, emap)
                    new_mask.extend(mask[pos+1:start+1])

                parts.append(sub)
                smap.extend(_smap)
                emap.extend(_emap)
                new_mask.extend(_mask)
                shift += delta
                pos = m.end()

            if pos < len(s):
                _copy_part(s[pos:], shift, parts, smap, emap)
                new_mask.extend(mask[pos+1:len(s)+1])

            smap.append(shift)
            emap.append(shift - 1)
            new_mask.append(_MASK_O)
            mask = new_mask
            o = ''.join(parts)

        else:
            o = s
            smap = _zeromap(o)
            emap = _zeromap(o)

        yield REPPStep(s, o, self, applied, smap, emap, mask)


class _REPPMask(_REPPOperation):
    """
    A REPP masking rule.

    When a mask is applied and matches a substring, the substring is
    blocked from further modification.

    Args:
        pattern: the regular expression pattern to match
    """
    def __init__(self, pattern: str):
        self.pattern = pattern
        self._re = _compile(pattern)

    def __str__(self):
        return f'={self.pattern}'

    def _apply(
        self,
        s: str,
        active: Set[str],
        mask: _CMap
    ) -> Iterator[REPPStep]:
        logger.debug(' %s', self)
        newmask = array('i', mask)  # make a copy
        for m in self._re.finditer(s):
            start = m.start() + 1
            newmask[start] = max(_MASK_B, mask[start])
            for i in range(start + 1, m.end() + 1):
                newmask[i] = _MASK_I
        yield REPPStep(s, s, self, True, _zeromap(s), _zeromap(s), newmask)


class _REPPGroup(_REPPOperation):
    def __init__(
        self, operations: List[_REPPOperation] = None, name: str = None
    ):
        if operations is None:
            operations = []
        self.operations: List[_REPPOperation] = operations
        self.name = name
        self._loaded = False

    def __repr__(self):
        name = '("{}") '.format(self.name) if self.name is not None else ''
        return '<{} object {}at {}>'.format(
            type(self).__name__, name, id(self)
        )

    def _apply(
        self,
        s: str,
        active: Set[str],
        mask: _CMap
    ) -> Iterator[REPPStep]:
        o = s
        applied = False
        for operation in self.operations:
            for step in operation._apply(o, active, mask):
                yield step
                o = step.output
                mask = step.mask
                applied |= step.applied

        yield REPPStep(s, o, self, applied, _zeromap(o), _zeromap(o), mask)


class _REPPInternalGroup(_REPPGroup):
    def __str__(self):
        return f'Internal group #{self.name}'

    def _apply(
        self,
        s: str,
        active: Set[str],
        mask: _CMap
    ) -> Iterator[REPPStep]:
        logger.debug('>%s', self.name)
        i = 0
        prev = s
        step = None  # in case _REPPGroup._apply() ever yields nothing
        for step in super()._apply(prev, active, mask):
            yield step
            mask = step.mask
        while step and prev != step.output:
            i += 1
            prev = step.output
            for step in super()._apply(prev, active, mask):
                yield step
                mask = step.mask

        logger.debug('>%s (done; iterated %d time(s))', self.name, i)


class REPP(_REPPGroup):
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
        operations: List[_REPPOperation] = None,
        name: str = None,
        modules: Dict[str, 'REPP'] = None,
        active: Iterable[str] = None
    ):
        super().__init__(operations=operations, name=name)
        self.info: Optional[str] = None
        self.tokenize_pattern: Optional[str] = None

        if modules is None:
            modules = {}
        self.modules = dict(modules)
        for modname, mod in self.modules.items():
            mod.name = modname
        self.active: Set[str] = set()
        if active is None:
            active = []
        for modname in active:
            self.activate(modname)

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
        name, directory, lines = _read_file(path, directory)
        r = cls(name=name, modules=modules, active=active)
        _parse_repp_module(lines, r, directory)
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
        _parse_repp_module(s.splitlines(), r, None)
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

    def _apply(
        self,
        s: str,
        active: Set[str],
        mask: _CMap
    ) -> Iterator[REPPStep]:
        if self.name in active:
            logger.info('>%s', self.name)
            for step in super()._apply(s, active, mask):
                yield step
                mask = step.mask
            logger.debug('>%s (done)', self.name)
        else:
            logger.debug('>%s (inactive)', self.name)

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
        logger.info('apply(%r)', s)
        active = self.active if active is None else set(active)
        result = last(self._trace(s, active, False))
        return result

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
        logger.info('trace(%r)', s)
        active = self.active if active is None else set(active)
        yield from self._trace(s, active, verbose)

    def _trace(
        self, s: str, active: Set[str], verbose: bool
    ) -> _Trace:
        startmap = _zeromap(s)
        endmap = _zeromap(s)
        mask = _zeromap(s)
        # initial boundaries
        startmap[0] = 1
        endmap[-1] = -1
        step = None
        for step in super()._apply(s, active, mask):
            if step.applied or verbose:
                yield step
            if step.applied:
                startmap = _mergemap(startmap, step.startmap)
                endmap = _mergemap(endmap, step.endmap)
        if step is not None:
            s = step.output
        yield REPPResult(s, startmap, endmap)

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
        logger.info('tokenize(%r, %r)', s, pattern)
        if pattern is None:
            if self.tokenize_pattern is None:
                pattern = DEFAULT_TOKENIZER
            else:
                pattern = self.tokenize_pattern
        active = self.active if active is None else set(active)
        result = last(self._trace(s, active, False))
        return self.tokenize_result(result, pattern=pattern)

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
        logger.info('tokenize_result(%r, %r)', result, pattern)
        tokens = [
            YYToken(id=i, start=i, end=(i + 1),
                    lnk=Lnk.charspan(tok[0], tok[1]),
                    form=tok[2])
            for i, tok in enumerate(_tokenize(result, pattern))
        ]
        return YYTokenLattice(tokens)


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


def _get_segments(replacement: str, _re):
    # parse_template() is an undocumented function in the standard library
    groups, literals = parse_template(replacement, _re)
    # literals is a list of strings or None (group position);
    # groups is a list of (i, g) where i is the index in literals
    # and g is the capturing group number.

    # first determine the last trackable group, where trackable
    # segments are transparent for characterization. For PET behavior,
    # these must appear in strictly increasing order with no gaps
    last_trackable = 0
    for expected, (i, grp) in zip(range(1, len(groups)+1), groups):
        if grp == expected:
            last_trackable = i + 1  # +1 for slice end

    # we can also combine groups and literals into a single list of
    # (literal, None) or (None, group) pairs for convenience
    group_map = dict(groups)
    segments: List[Tuple[Optional[str], Optional[int]]] = [
        (literal, group_map.get(i))
        for i, literal
        in enumerate(literals)
    ]
    # Divide the segments into trackable/untrackable
    return segments[:last_trackable], segments[last_trackable:]


def last(steps: _Trace) -> REPPResult:
    for step in steps:
        pass
    assert isinstance(step, REPPResult)
    return step


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
    map_part = [shift] * len(s)
    smap.extend(map_part)
    emap.extend(map_part)


def _insert_part(
    s: str,
    width: int,
    shift: int,
    parts: List[str],
    smap: _CMap,
    emap: _CMap
) -> None:
    parts.append(s)
    endshift = shift - len(s)
    _width = width - 1
    smap.extend(range(shift, endshift, -1))
    emap.extend(range(shift + _width, endshift + _width, -1))


def _process_match(
    m: Match[str],
    prev_mask: _CMap,
    shift: int,
    tracked,
    untracked
) -> Tuple[str, _CMap, _CMap, _CMap, int, bool]:
    parts: List[str] = []
    smap = array('i', [])
    emap = array('i', [])
    mask = array('i', [])
    delta = 0
    blocked = False

    if tracked or untracked:
        start = m.start()
        # for literals, the end is the start of the next backreference
        end = next((m.start(g) for _, g in tracked if g), m.end())

        for literal, group in tracked:
            if literal is None:
                literal = m.group(group) or ''
                _copy_part(literal, shift + delta, parts, smap, emap)
                mask.extend(prev_mask[(start+1):(start+len(literal)+1)])
                end = m.start(group+1) if group < m.lastindex else m.end()
            else:
                # block if overlap with mask
                if any(prev_mask[start+1:end+1]):
                    blocked = True
                    break
                width = end - start
                litlen = len(literal)
                _insert_part(literal, width, shift + delta, parts, smap, emap)
                mask.extend([_MASK_O] * litlen)
                delta += width - litlen

            start = end

        if untracked:
            # block if untracked overlaps with mask, including backreferences
            if (any(prev_mask[start+1:m.end()+1])
                or any(any(prev_mask[m.start(grp)+1:m.end(grp)+1])
                       for lit, grp in untracked if grp)):
                blocked = True
            else:
                # untracked segments can be collapsed into one substring
                literal = ''.join(
                    m.group(group) or '' if literal is None else literal
                    for literal, group in untracked
                )
                width = m.end() - start
                litlen = len(literal)
                _insert_part(literal, width, shift+delta, parts, smap, emap)
                mask.extend([_MASK_O] * litlen)
                delta += width - litlen
    else:
        # the replacement is empty (match is deleted)
        delta = m.end() - m.start()

    substring = ''.join(parts)
    if not blocked:
        blocked = _check_mask(substring, m, smap, emap, mask, prev_mask)

    return substring, smap, emap, mask, delta, blocked


def _check_mask(
    s: str,
    m: Match[str],
    smap: _CMap,
    emap: _CMap,
    mask: _CMap,
    prev_mask: _CMap
) -> bool:
    """Returns True if any masked material has changed.

    There are three contexts for mask checks:

      1. The first character in the match is a mask continuation
      2. The first character after the end of the match is a mask continuation
      3. The whole mask is contained within the match

    For (1) and (2), the mask must not change nor move around. For (1)
    it cannot change but it can move.

    """
    start, end = m.span()
    mstart, mend = start + 1, end + 1
    orig = m.group(0)
    # no masked material; no problem
    if not any(prev_mask[mstart:mend]):
        return False
    # whether the final mask is fixed depends on the next mask value;
    # check now as the _make_mask_info() function won't see it
    end_fixed = prev_mask[mend] == _MASK_I
    # prev/next left, middle, right
    pl, pm, pr = _make_mask_info(orig, prev_mask[mstart:mend], end_fixed)
    nl, nm, nr = _make_mask_info(s, mask, end_fixed)

    # check fixed start/end masks
    if pl != nl or pr != nr:
        return True
    # other masks just need to be present in equal number
    for substr in set(pm).union(nm):
        if pm.get(substr, 0) != nm.get(substr, 0):
            return True

    return False


def _make_mask_info(
    s: str,
    mask: _CMap,
    end_fixed: bool
) -> Tuple[str, Dict[str, int], str]:
    if not mask:
        return '', {}, ''
    left = s[:_get_mask_len(mask, 0)] if mask[0] == _MASK_I else ''
    right = s[-_get_mask_len(mask[::-1], 0) or len(s):] if end_fixed else ''
    middle: Dict[str, int] = {}
    i = len(left)
    j = len(s) - len(right)
    while i < j:
        if mask[i] == _MASK_B:
            mlen = _get_mask_len(mask, i+1) + 1
            substr = s[i:mlen]
            if substr not in middle:
                middle[substr] = 1
            else:
                middle[substr] += 1
            i += mlen
        else:
            i += 1
    return left, middle, right


def _get_mask_len(mask: _CMap, i: int):
    return sum(1 for _ in takewhile(lambda v: v == _MASK_I, mask[i:]))


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


def _read_file(
    path: Path,
    directory: Optional[Path]
) -> Tuple[str, Path, List[str]]:
    if directory is not None:
        directory = Path(directory).expanduser()
    else:
        directory = path.parent
    name = path.with_suffix('').name
    lines = _repp_lines(path)
    return name, directory, lines


def _repp_lines(path: Path) -> List[str]:
    if not path.is_file():
        raise REPPError(f'REPP file not found: {path!s}')
    return path.read_text(encoding='utf-8').splitlines()


def _parse_repp_module(
    lines: List[str],
    r: REPP,
    directory: Path
) -> None:
    r._loaded = True

    operations: List[_REPPOperation] = r.operations
    stack: List[List[_REPPOperation]] = [operations]
    internal_groups: Dict[str, _REPPInternalGroup] = {}

    while lines:
        line = lines.pop(0)
        if line.startswith(';') or line.strip() == '':
            continue  # skip comments and empty lines

        operator, operand = line[0], line[1:].rstrip()

        if operator == '!':
            # don't use operand because it was rstripped; use line[1:]
            operations.append(_parse_rewrite_rule(line[1:]))

        elif operator == '<':
            fn = directory.joinpath(operand)
            lines = _repp_lines(fn) + lines

        elif operator == '>':
            operations.append(
                _handle_group_call(operand, internal_groups, r, directory)
            )

        elif operator == '=':
            # don't use operand because it was rstripped; use line[1:]
            operations.append(_REPPMask(line[1:]))

        elif operator == '#':
            _handle_internal_group(operand, internal_groups, stack)
            operations = stack[-1]

        elif operator == ':':
            _handle_tokenization_pattern(operand, r, len(stack) > 1)

        elif operator == '@':
            _handle_metainfo_declaration(operand, r, len(stack) > 1)

        else:
            raise REPPError(f'Invalid declaration: {line}')

    _verify_internal_groups(internal_groups)


def _parse_rewrite_rule(operand: str) -> _REPPRule:
    match = re.match(r'([^\t]+)\t+(.*)', operand)
    if match is None:
        raise REPPError(f'Invalid rewrite rule: !{operand}')
    return _REPPRule(match.group(1), match.group(2))


def _handle_group_call(
    operand: str,
    internal_groups,
    r: REPP,
    directory: Optional[Path],
) -> _REPPGroup:
    if operand.isdigit():
        if operand not in internal_groups:
            internal_groups[operand] = _REPPInternalGroup(operations=[],
                                                          name=operand)
        return internal_groups[operand]
    elif not operand:
        raise REPPError('Missing group name')
    else:
        if operand not in r.modules:
            r.modules[operand] = REPP(name=operand, modules=r.modules)
        mod = r.modules[operand]
        if not mod._loaded:
            if directory is None:
                raise REPPError('Cannot implicitly load modules if '
                                'a directory is not given.')
            modpath = directory / (operand + '.rpp')
            _parse_repp_module(_repp_lines(modpath), mod, directory)
        return mod


def _handle_internal_group(operand, internal_groups, stack) -> None:
    if operand.isdigit():
        if operand not in internal_groups:
            internal_groups[operand] = _REPPInternalGroup(operations=[],
                                                          name=operand)
        ig = internal_groups[operand]
        if ig._loaded:
            raise REPPError(f'Internal group name already defined: {operand}')
        ig._loaded = True
        stack.append(ig.operations)
    elif operand == '':
        stack.pop()
    else:
        raise REPPError('Invalid internal group name: ' + operand)


def _handle_tokenization_pattern(
    operand: str,
    r: REPP,
    in_internal_group: bool,
) -> None:
    if in_internal_group:
        raise REPPError('tokenization pattern defined in internal group')
    if r.tokenize_pattern is not None:
        raise REPPError('Only one tokenization pattern (:) may be defined.')
    r.tokenize_pattern = operand


def _handle_metainfo_declaration(
    operand: str,
    r: REPP,
    in_internal_group: bool,
) -> None:
    if in_internal_group:
        raise REPPError('meta-info declaration defined in internal group')
    if r.info is not None:
        raise REPPError('Only one meta-info declaration (@) may be defined.')
    r.info = operand


def _verify_internal_groups(internal_groups):
    for grpname, grp in internal_groups.items():
        if not grp._loaded:
            raise REPPError(f'internal group not defined: #{grpname}')
