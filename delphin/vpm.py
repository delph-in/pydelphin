
"""
Variable property mapping (VPM).
"""

import re
from pathlib import Path

from delphin.exceptions import PyDelphinSyntaxError
from delphin import variable
# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401


_LR_OPS = set(['<>', '>>', '==', '=>'])
_RL_OPS = set(['<>', '<<', '==', '<='])
_SUBSUME_OPS = set(['<>', '<<', '>>'])
_EQUAL_OPS = set(['==', '<=', '=>'])
_ALL_OPS = _LR_OPS.union(_RL_OPS)


class VPMSyntaxError(PyDelphinSyntaxError):
    """Raised when loading an invalid VPM."""


def load(source, semi=None):
    """
    Read a variable-property mapping from *source* and return the VPM.

    Args:
        source: a filename or file-like object containing the VPM
            definitions
        semi (:class:`~delphin.semi.SemI`, optional): if provided,
            it is passed to the VPM constructor
    Returns:
        a :class:`VPM` instance
    """
    if hasattr(source, 'read'):
        return _load(source, semi)
    else:
        source = Path(source).expanduser()
        with source.open('r') as fh:
            return _load(fh, semi)


def _load(fh, semi):
    filename = getattr(fh, 'name', '<stream>')
    typemap = []
    propmap = []
    curmap = typemap
    lh, rh = 1, 1  # number of elements expected on each side
    for lineno, line in enumerate(fh, 1):
        line = line.lstrip()

        if not line or line.startswith(';'):
            continue

        match = re.match(r'(?P<lfeats>[^:]+):(?P<rfeats>.+)', line)
        if match is not None:
            lfeats = match.group('lfeats').split()
            rfeats = match.group('rfeats').split()
            lh, rh = len(lfeats), len(rfeats)
            curmap = []
            propmap.append(((lfeats, rfeats), curmap))
            continue

        match = re.match(r'(?P<lvals>.*)(?P<op>[<>=]{2})(?P<rvals>.*)$', line)
        if match is not None:
            lvals = match.group('lvals').split()
            op = match.group('op')
            rvals = match.group('rvals').split()
            msg, offset = '', -1
            if len(lvals) != lh:
                msg = 'wrong number of values on left side'
                offset = match.end('lvals')
            if op not in _ALL_OPS:
                msg = 'invalid operator'
                offset = match.end('op')
            elif len(rvals) != rh:
                msg = 'wrong number of values on right side'
                offset = match.end('rvals')
            if msg:
                raise VPMSyntaxError(msg, filename=filename,
                                     lineno=lineno, offset=offset,
                                     text=line)
            curmap.append((lvals, op, rvals))
            continue

        raise VPMSyntaxError('invalid line in VPM file',
                             filename=filename, lineno=lineno, text=line)

    return VPM(typemap, propmap, semi)


class VPM(object):
    """
    A variable-property mapping.

    This class contains the rules for mapping variable properties from
    the grammar-internal definitions to grammar-external ones, and back
    again.

    Args:
        typemap: an iterable of (src, OP, tgt) iterables
        propmap: an iterable of (featset, valmap) tuples, where
            featmap is a tuple of two lists: (source_features,
            target_features); and valmap is a list of value tuples:
            (source_values, OP, target_values)
        semi (:class:`~delphin.semi.SemI`, optional): if provided,
            this is used for more sophisticated value comparisons
    """

    def __init__(self, typemap, propmap, semi=None):
        """
        Initialize a new variable-property mapping instance.
        """
        self._typemap = typemap  # [(src, OP, tgt)]
        self._propmap = propmap  # [((srcfs, tgtfs), [(srcvs, OP, tgtvs)])]
        self._semi = semi

    def apply(self, var, props, reverse=False):
        """
        Apply the VPM to variable *var* and properties *props*.

        Args:
            var: a variable
            props: a dictionary mapping properties to values
            reverse: if `True`, apply the rules in reverse (e.g. from
                grammar-external to grammar-internal forms)
        Returns:
            a tuple (v, p) of the mapped variable and properties
        """
        vs, vid = variable.split(var)
        if reverse:
            # variable type mapping is disabled in reverse
            # tms = [(b, op, a) for a, op, b in self._typemap if op in _RL_OPS]
            tms = []
        else:
            tms = [(a, op, b) for a, op, b in self._typemap if op in _LR_OPS]
        for src, op, tgt in tms:
            if _valmatch([vs], src, op, None, self._semi, 'variables'):
                vs = vs if tgt == ['*'] else tgt[0]
                break
        newvar = f'{vs}{vid}'

        newprops = {}
        for featsets, valmap in self._propmap:
            if reverse:
                tgtfeats, srcfeats = featsets
                pms = [(b, op, a) for a, op, b in valmap if op in _RL_OPS]
            else:
                srcfeats, tgtfeats = featsets
                pms = [(a, op, b) for a, op, b in valmap if op in _LR_OPS]
            vals = [props.get(f) for f in srcfeats]
            for srcvals, op, tgtvals in pms:
                if _valmatch(vals, srcvals, op, vs, self._semi, 'properties'):
                    for i, featval in enumerate(zip(tgtfeats, tgtvals)):
                        k, v = featval
                        if v == '*':
                            if i < len(vals) and vals[i] is not None:
                                newprops[k] = vals[i]
                        elif v != '!':
                            newprops[k] = v
                    break

        return newvar, newprops


def _valmatch(vs, ss, op, varsort, semi, section):
    """
    Return `True` if for every paired *v* and *s* from *vs* and *ss*:
        v <> s (subsumption or equality if *semi* is `None`)
        v == s (equality)
        s == '*'
        s == '!' and v == `None`
        s == '[xyz]' and varsort == 'xyz'
    """
    if op in _EQUAL_OPS or semi is None:
        return all(
            s == v  # value equality
            or (s == '*' and v is not None)  # non-null wildcard
            or (
                v is None
                and (  # value is null (any or with matching varsort)
                    s == '!'
                    or (s[0], s[-1], s[1:-1]) == ('[', ']', varsort)
                )
            )
            for v, s in zip(vs, ss)
        )
    else:
        pass
