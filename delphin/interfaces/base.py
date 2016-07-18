
from collections import Sequence

from delphin.derivation import Derivation
from delphin.tokens import YyTokenLattice
from delphin.mrs import (
    Mrs,
    Dmrs,
    simplemrs,
    eds,
)
from delphin.util import SExpr, stringtypes

class ParseResult(dict):
    """
    A wrapper around a result dictionary to automate deserialization
    for supported formats. A ParseResult is still a dictionary, so the
    raw data can be obtained using dict access.
    """

    def __repr__(self):
        return 'ParseResult({})'.format(dict.__repr__(self))

    def derivation(self):
        """
        Deserialize and return a Derivation object for UDF- or
        JSON-formatted derivation data; otherwise return the original
        string.
        """
        drv = self.get('derivation')
        if drv is not None:
            if isinstance(drv, dict):
                drv = Derivation.from_dict(drv)
            elif isinstance(drv, stringtypes):
                drv = Derivation.from_string(drv)
        return drv

    def tree(self):
        """
        Deserialize and return a labeled syntax tree. The tree data
        may be a standalone datum, or embedded in the derivation.
        """
        tree = self.get('tree')
        if isinstance(tree, stringtypes):
            tree = SExpr.parse(tree).data
        elif tree is None:
            drv = self.get('derivation')
            if isinstance(drv, dict) and 'label' in drv:
                def _extract_tree(d):
                    t = [d.get('label', '')]
                    if 'tokens' in d:
                        t.append([d.get('form', '')])
                    else:
                        for dtr in d.get('daughters', []):
                            t.append(_extract_tree(dtr))
                    return t
                tree = _extract_tree(drv)
        return tree

    def mrs(self):
        """
        Deserialize and return an Mrs object for simplemrs or
        JSON-formatted MRS data; otherwise return the original string.
        """
        mrs = self.get('mrs')
        if mrs is not None:
            if isinstance(mrs, dict):
                mrs = Mrs.from_dict(mrs)
            elif isinstance(mrs, stringtypes):
                mrs = simplemrs.loads_one(mrs)
        return mrs

    def eds(self):
        """
        Deserialize and return an Eds object for native- or
        JSON-formatted EDS data; otherwise return the original string.
        """
        _eds = self.get('eds')
        if _eds is not None:
            if isinstance(_eds, dict):
                _eds = eds.Eds.from_dict(_eds)
            elif isinstance(_eds, stringtypes):
                _eds = eds.loads_one(_eds)
        return _eds

    def dmrs(self):
        """
        Deserialize and return a Dmrs object for JSON-formatted DMRS
        data; otherwise return the original string.
        """
        dmrs = self.get('dmrs')
        if dmrs is not None:
            if isinstance(dmrs, dict):
                dmrs = Dmrs.from_dict(dmrs)
        return dmrs

class ParseResponse(dict):
    """
    A wrapper around the response dictionary for more convenient
    access to results.
    """
    _result_factory = ParseResult

    def __repr__(self):
        return 'ParseResponse({})'.format(dict.__repr__(self))

    def results(self):
        """Return ParseResult objects for each result."""
        return [self._result_factory(r) for r in self.get('results', [])]

    def result(self, i):
        """Return a ParseResult object for the *i*th result."""
        return self._result_factory(self.get('results', [])[i])

    def tokens(self, tokenset='internal'):
        """
        Deserialize and return a YyTokenLattice object for the
        initial or internal token set, if provided, from the YY
        format or the JSON-formatted data; otherwise return the
        original string.

        Args:
            tokenset: either `initial` or `internal` (default: `internal`)
        """
        toks = self.get('tokens', {}).get(tokenset)
        if toks is not None:
            if isinstance(toks, stringtypes):
                toks = YyTokenLattice.from_string(toks)
            elif isinstance(toks, Sequence):
                toks = YyTokenLattice.from_list(toks)
        return toks

