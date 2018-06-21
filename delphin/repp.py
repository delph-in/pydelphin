# coding: utf-8

"""
Regular Expression Preprocessor (REPP)

A Regular-Expression Preprocessor [REPP]_ is a method of applying a
system of regular expressions for transformation and tokenization while
retaining character indices from the original input string.

.. [REPP] Rebecca Dridan and Stephan Oepen. Tokenization: Returning to
  a long solved problem---a survey, contrastive experiment,
  recommendations, and toolkit. In Proceedings of the 50th Annual
  Meeting of the Association for Computational Linguistics (Volume 2:
  Short Papers), pages 378–382, Jeju Island, Korea, July 2012.
  Association for Computational Linguistics.
  URL http://www.aclweb.org/anthology/P12-2074.

"""
from __future__ import unicode_literals

from os.path import exists, dirname, basename, join as joinpath
import io
import warnings
import re
from sre_parse import parse_template
from array import array
from collections import namedtuple

from delphin.tokens import YyToken, YyTokenLattice
from delphin.mrs.components import Lnk
from delphin.exceptions import REPPError


class REPPStep(namedtuple(
        'REPPStep', 'input output operation applied startmap endmap')):
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


class REPPResult(namedtuple(
        'REPPResult', 'string startmap endmap')):
    """
    The final result of REPP application.

    Attributes:
        string (str): resulting string after all rules have applied
        startmap (:py:class:`array`): integer array of start offsets
        endmap (:py:class:`array`): integer array of end offsets
    """

class _REPPOperation(object):
    """
    The supertype of REPP groups and rules.

    This class defines the apply(), trace(), and tokenize() methods
    which are available in [_REPPRule], [_REPPGroup],
    [_REPPIterativeGroup], and [REPP] instances.
    """
    def _apply(self, s, active):
        raise NotImplementedError()

    def apply(self, s, active=None):
        for step in self.trace(s, active=active):
            pass
        return step

    def trace(self, s, active=None, verbose=False):
        startmap = _zeromap(s)
        endmap = _zeromap(s)
        # initial boundaries
        startmap[0] = 1
        endmap[-1] = -1
        step = None
        for step in self._apply(s, active):
            if step.applied or verbose:
                yield step
            startmap = _mergemap(startmap, step.startmap)
            endmap = _mergemap(endmap, step.endmap)
        if step is not None:
            s = step.output
        yield REPPResult(s, startmap, endmap)

    def tokenize(self, s, pattern=r'[ \t]+', active=None):
        res = self.apply(s, active=active)
        tokens = [
            YyToken(id=i, start=i, end=i+1,
                    lnk=Lnk.charspan(tok[0], tok[1]),
                    form=tok[2])
            for i, tok in enumerate(_tokenize(res, pattern))
        ]
        return YyTokenLattice(tokens)


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
    def __init__(self, pattern, replacement):
        self.pattern = pattern
        self.replacement = replacement
        self._re = re.compile(pattern)
        backrefs, literals = parse_template(replacement, self._re)
        self._backrefs = dict(backrefs)
        self._segments = literals
        # Get "trackable" capture groups; i.e., those that are
        # transparent for characterization. For PET behavior, these
        # must appear in strictly increasing order with no gaps
        self._groupstack = []
        for i, backref in enumerate(backrefs):
            _, grpidx = backref
            if i + 1 != grpidx:
                break
            self._groupstack.append(grpidx)

    def __str__(self):
        return '!{}\t\t{}'.format(self.pattern, self.replacement)

    def _apply(self, s, active):
        ms = list(self._re.finditer(s))
        if ms:
            pos = 0  # current position in original string
            shift = 0  # current original/target length difference
            parts = []
            smap = array('i', [0])
            emap = array('i', [0])
            for m in ms:
                cgs = list(reversed(self._groupstack))  # make a copy
                lb = m.start()
                rb = m.start(cgs[-1]) if cgs else m.end()
                if pos < m.start():
                    _copy_part(s[pos:m.start()], shift, parts, smap, emap)
                pos = m.start()
                for i, seg in enumerate(self._segments):
                    if seg is None and cgs:
                        grpidx = cgs.pop()
                        assert self._backrefs[i] == grpidx
                        seg = m.group(grpidx)
                        _copy_part(seg, shift, parts, smap, emap)
                        # adjust for the next segment
                        lb = m.end(grpidx)
                        rb = m.start(cgs[-1]) if cgs else m.end()
                        pos += len(seg)
                    else:
                        if seg is None:
                            seg = m.group(i)
                        w = rb - lb  # segment width
                        _insert_part(seg, w, shift, parts, smap, emap)
                        pos += w
                        shift = pos - sum(map(len, parts))
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


class _REPPGroup(_REPPOperation):
    def __init__(self, operations=None, name=None):
        if operations is None: operations = []
        self.operations = operations
        self.name = name

    def __repr__(self):
        name = '("{}") '.format(self.name) if self.name is not None else ''
        return '<{} object {}at {}>'.format(
            self.__class__.__name__, name, id(self)
        )

    def __str__(self):
        return 'Module {}'.format(self.name if self.name is not None else '')

    def _apply(self, s, active):
        o = s
        applied = False
        for operation in self.operations:
            for step in operation._apply(o, active):
                yield step
                o = step.output
                applied |= step.applied
        yield REPPStep(s, o, self, applied, _zeromap(o), _zeromap(o))


class _REPPGroupCall(_REPPOperation):
    def __init__(self, name, modules):
        self.name = name
        self.modules = modules

    def _apply(self, s, active):
        if active is not None and self.name in active:
            # TODO 'yield from' may be useful here when Python2.7 is
            # no longer supported. See issue #115
            for step in self.modules[self.name]._apply(s, active):
                yield step


class _REPPIterativeGroup(_REPPGroup):
    def __str__(self):
        return 'Internal group #{}'.format(self.name)

    def _apply(self, s, active):
        o = s
        applied = False
        prev = None
        while prev != o:
            prev = o
            for operation in self.operations:
                for step in operation._apply(o, active):
                    yield step
                    o = step.output
                    applied |= step.applied
            yield REPPStep(s, o, self, applied, _zeromap(o), _zeromap(o))


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

    def __init__(self, name=None, modules=None, active=None):
        self.info = None
        self.tokenize_pattern = None
        self.group = _REPPGroup(name=name)

        if modules is None:
            modules = []
        self.modules = dict(modules)
        self.active = set()
        if active is None:
            active = []
        for mod in active:
            self.activate(mod)

    @classmethod
    def from_config(cls, path, directory=None):
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
        if not exists(path):
            raise REPPError('REPP config file not found: {}'.format(path))
        confdir = dirname(path)

        # TODO: can TDL parsing be repurposed for this variant?
        conf = io.open(path, encoding='utf-8').read()
        conf = re.sub(r';.*', '', conf).replace('\n',' ')
        m = re.search(
            r'repp-modules\s*:=\s*((?:[-\w]+\s+)*[-\w]+)\s*\.', conf)
        t = re.search(
            r'repp-tokenizer\s*:=\s*([-\w]+)\s*\.', conf)
        a = re.search(
            r'repp-calls\s*:=\s*((?:[-\w]+\s+)*[-\w]+)\s*\.', conf)
        f = re.search(
            r'format\s*:=\s*(\w+)\s*\.', conf)
        d = re.search(
            r'repp-directory\s*:=\s*(.*)\.\s*$', conf)

        if m is None:
            raise REPPError('repp-modules option must be set')
        if t is None:
            raise REPPError('repp-tokenizer option must be set')

        mods = m.group(1).split()
        tok = t.group(1).strip()
        active = a.group(1).split() if a is not None else None
        fmt = f.group(1).strip() if f is not None else None

        if directory is None:
            if d is not None:
                directory = d.group(1).strip(' "')
            elif exists(joinpath(confdir, tok + '.rpp')):
                directory = confdir
            elif exists(joinpath(confdir, 'rpp', tok + '.rpp')):
                directory = joinpath(confdir, 'rpp')
            elif exists(joinpath(confdir, '../rpp', tok + '.rpp')):
                directory = joinpath(confdir, '../rpp')
            else:
                raise REPPError('Could not find a suitable REPP directory.')

        # ignore repp-modules and format?
        return REPP.from_file(
            joinpath(directory, tok + '.rpp'),
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
        name = basename(path)
        if name.endswith('.rpp'):
            name = name[:-4]
        lines = _repp_lines(path)
        directory = dirname(path) if directory is None else directory
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

    def activate(self, mod):
        """
        Set external module *mod* to active.
        """
        self.active.add(mod)

    def deactivate(self, mod):
        """
        Set external module *mod* to inactive.
        """
        if mod in self.active:
            self.active.remove(mod)

    def _apply(self, s, active):
        return self.group._apply(s, active)

    def apply(self, s, active=None):
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
        return self.group.apply(s, active=active)

    def trace(self, s, active=None, verbose=False):
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

    def tokenize(self, s, pattern=None, active=None):
        """
        Rewrite and tokenize the input string *s*.

        Args:
            s (str): the input string to process
            pattern (str, optional): the regular expression pattern on
                which to split tokens; defaults to `[ \t]+`
            active (optional): a collection of external module names
                that may be applied if called
        Returns:
            a :class:`~delphin.tokens.YyTokenLattice` containing the
            tokens and their characterization information
        """
        if pattern is None:
            if self.tokenize_pattern is None:
                pattern = r'[ \t]+'
            else:
                pattern = self.tokenize_pattern
        if active is None:
            active = self.active
        return self.group.tokenize(s, pattern=pattern, active=active)


def _zeromap(s):
    return array('i', [0] * (len(s) + 2))


def _mergemap(map1, map2):
    """
    Positions in map2 have an integer indicating the relative shift to
    the equivalent position in map1. E.g., the i'th position in map2
    corresponds to the i + map2[i] position in map1.
    """
    merged = array('i', [0] * len(map2))
    for i, shift in enumerate(map2):
        merged[i] = shift + map1[i + shift]
    return merged


def _copy_part(s, shift, parts, smap, emap):
    parts.append(s)
    smap.extend([shift] * len(s))
    emap.extend([shift] * len(s))


def _insert_part(s, w, shift, parts, smap, emap):
    parts.append(s)
    smap.extend(range(shift, shift - len(s), -1))
    newshift = shift + (w - len(s))
    emap.extend(range(shift + w - 1, newshift - 1, -1))


def _tokenize(result, pattern):
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

def _repp_lines(path):
    if not exists(path):
        raise REPPError('REPP file not found: {}'.format(path))
    return io.open(path, encoding='utf-8').read().splitlines()

def _parse_repp(lines, r, directory):
    ops = list(_parse_repp_group(lines, r, directory))
    if lines:
        raise REPPError('Unexpected termination; maybe the # operator '
                        'appeared without an internal group.')
    r.group.operations.extend(ops)

def _parse_repp_group(lines, r, directory):
    igs = {}  # internal groups
    while lines:
        line = lines.pop(0)
        if line.startswith(';') or line.strip() == '':
            continue  # skip comments and empty lines
        elif line[0] == '!':
            match = re.match(r'([^\t]+)\t+(.*)', line[1:])
            if match is None:
                raise REPPError('Invalid rewrite rule: {}'.format(line))
            yield _REPPRule(match.group(1), match.group(2))
        elif line[0] == '<':
            fn = joinpath(directory, line[1:].rstrip())
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
                        joinpath(directory, modname + '.rpp'),
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
            raise REPPError('Invalid declaration: {}'.format(line))
