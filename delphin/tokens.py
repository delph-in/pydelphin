
"""
YY tokens and token lattices.
"""

from typing import NamedTuple, Optional, List, Tuple
import re

from delphin.lnk import Lnk
# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401


class _YYToken(NamedTuple):
    id: int
    start: int
    end: int
    lnk: Lnk
    paths: List[int]
    form: str
    surface: Optional[str]
    ipos: int          # relative index of sub-token to which lrules apply
    lrules: List[str]  # list of morphological rules applied, "null" if None
    pos: List[Tuple[str, float]]


class YYToken(_YYToken):
    """
    A tuple of token data in the YY format.

    Args:
        id: token identifier
        start: start vertex
        end: end vertex
        lnk: <from:to> charspan (optional)
        paths: path membership
        form: surface token
        surface: original token (optional; only if `form` was modified)
        ipos: length of `lrules`? always 0?
        lrules: something about lexical rules; always "null"?
        pos: pairs of (POS, prob)
    """
    __slots__ = ()

    def __new__(cls, id, start, end,
                lnk=None, paths=(1,), form=None, surface=None,
                ipos=0, lrules=("null",), pos=()):
        if form is None:
            raise TypeError('Missing required keyword argument \'form\'.')
        if lnk is None:
            lnk = Lnk.default()
        return super(YYToken, cls).__new__(
            cls, id, start, end, lnk, list(paths), form, surface,
            ipos, list(lrules), list(pos)
        )

    def __str__(self):
        parts = [str(self.id), str(self.start), str(self.end)]
        if self.lnk:
            parts.append(str(self.lnk))
        parts.append(' '.join(map(str, self.paths or [1])))
        if self.surface is None:
            parts.append(f'"{self.form}"')
        else:
            parts.append(f'"{self.form}" "{self.surface}"')
        parts.extend([
            str(self.ipos),
            ' '.join(map('"{}"'.format, self.lrules))
        ])
        if self.pos:
            ps = [f'"{pos}" {p:.4f}' for pos, p in self.pos]
            parts.append(' '.join(ps))
        return '({})'.format(', '.join(parts))

    @classmethod
    def from_dict(cls, d):
        """
        Decode from a dictionary as from :meth:`to_dict`.
        """
        return cls(
            d['id'],
            d['start'],
            d['end'],
            Lnk.charspan(d['from'], d['to']) if 'from' in d else None,
            # d.get('paths', [1]),
            form=d['form'],
            surface=d.get('surface'),
            # ipos=
            # lrules=
            pos=list(zip(d.get('tags', []), d.get('probabilities', [])))
        )

    def to_dict(self):
        """
        Encode the token as a dictionary suitable for JSON serialization.
        """
        d = {
            'id': self.id,
            'start': self.start,
            'end': self.end,
            'form': self.form
        }
        if self.lnk:
            cfrom, cto = self.lnk.data
            d['from'] = cfrom
            d['to'] = cto
        # d['paths'] = self.paths
        if self.surface is not None:
            d['surface'] = self.surface
        # d['ipos'] = self.ipos
        # d['lrules'] = self.lrules
        if self.pos:
            d['tags'] = [ps[0] for ps in self.pos]
            d['probabilities'] = [ps[1] for ps in self.pos]
        return d


# from: https://github.com/delph-in/docs/wiki/PetInput
# (id, start, end, [link,] path+, form [surface], ipos, lrule+[, {pos p}+])
_yy_re = re.compile(
    r'\(\s*'
    r'(?P<id>{integer}){comma}'
    r'(?P<start>{integer}){comma}'
    r'(?P<end>{integer}){comma}'
    r'(?:<(?P<lnkfrom>{integer}):(?P<lnkto>{integer})>{comma})?'
    r'(?P<paths>(?:{integer}\s*)+){comma}'
    r'(?P<form>{string})'
    r'(?:\s*(?P<surface>{string}))?'
    r'{comma}'
    r'(?P<ipos>{integer}){comma}'
    r'(?P<lrules>(?:{string}\s*)+)'
    r'(?:{comma}(?P<pos>(?:{string}\s+{float}\s*)+))?'
    r'\s*\)'
    .format(
        integer=r'-?\d+',
        comma=r'\s*,\s*',
        string=r'"[^"\\]*(?:\\.[^"\\]*)*"',
        float=r'-?(0|[1-9]\d*)(\.\d+[eE][-+]?|\.|[eE][-+]?)\d+'
    )
)


class YYTokenLattice:
    """
    A lattice of YY Tokens.

    Args:
        tokens: a list of YYToken objects
    """
    def __init__(self, tokens):
        self.tokens = tokens

    @classmethod
    def from_string(cls, s):
        """
        Decode from the YY token lattice format.
        """
        def _qstrip(s):
            return s[1:-1]  # remove assumed quote characters
        tokens = []
        for match in _yy_re.finditer(s):
            d = match.groupdict()
            lnk, pos = None, []
            if d['lnkfrom'] is not None:
                lnk = Lnk.charspan(d['lnkfrom'], d['lnkto'])
            if d['pos'] is not None:
                ps = d['pos'].strip().split()
                pos = list(zip(map(_qstrip, ps[::2]), map(float, ps[1::2])))
            tokens.append(
                YYToken(
                    int(d['id']),
                    int(d['start']),
                    int(d['end']),
                    lnk,
                    list(map(int, d['paths'].strip().split())),
                    _qstrip(d['form']),
                    None if d['surface'] is None else _qstrip(d['surface']),
                    int(d['ipos']),
                    list(map(_qstrip, d['lrules'].strip().split())),
                    pos
                )
            )
        return cls(tokens)

    @classmethod
    def from_list(cls, toks):
        """
        Decode from a list as from :meth:`to_list`.
        """
        return cls(list(map(YYToken.from_dict, toks)))

    def to_list(self):
        """
        Encode the token lattice as a list suitable for JSON serialization.
        """
        return [t.to_dict() for t in self.tokens]

    def __str__(self):
        return ' '.join(map(str, self.tokens))

    def __eq__(self, other):
        if not isinstance(other, YYTokenLattice):
            return NotImplemented
        if (len(self.tokens) == len(other.tokens)
            and all(t1 == t2 for t1, t2
                    in zip(self.tokens, other.tokens))):
            return True
        return False
