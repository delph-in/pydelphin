from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Optional, Union

from delphin import util
from delphin.tdl._exceptions import TDLError
from delphin.tfs import FeatureStructure

# Values for list expansion
LIST_TYPE = '*list*'        #: type of lists in TDL
EMPTY_LIST_TYPE = '*null*'  #: type of list terminators
LIST_HEAD = 'FIRST'         #: feature for list items
LIST_TAIL = 'REST'          #: feature for list tails
DIFF_LIST_LIST = 'LIST'     #: feature for diff-list lists
DIFF_LIST_LAST = 'LAST'     #: feature for the last path in a diff-list

AttrSeq = Sequence[tuple[str, Union['Conjunction', 'Term']]]
AttrMap = Mapping[str, Union['Conjunction', 'Term']]


# Classes for TDL entities

class Term:
    """
    Base class for the terms of a TDL conjunction.

    All terms are defined to handle the binary '&' operator, which
    puts both into a Conjunction:

    >>> TypeIdentifier('a') & TypeIdentifier('b')
    <Conjunction object at 140008950372168>

    Args:
        docstring (str): documentation string

    Attributes:
        docstring (str): documentation string
    """
    def __init__(self, docstring=None):
        self.docstring = docstring

    def __repr__(self):
        return "<{} object at {}>".format(
            type(self).__name__, id(self))

    def __and__(self, other):
        if isinstance(other, Term):
            return Conjunction([self, other])
        elif isinstance(other, Conjunction):
            return Conjunction([self] + other._terms)
        else:
            return NotImplemented


class TypeTerm(Term, str):
    """
    Base class for type terms (identifiers, strings and regexes).

    This subclass of :class:`Term` also inherits from :py:class:`str`
    and forms the superclass of the string-based terms
    :class:`TypeIdentifier`, :class:`String`, and :class:`Regex`.
    Its purpose is to handle the correct instantiation of both the
    :class:`Term` and :py:class:`str` supertypes and to define
    equality comparisons such that different kinds of type terms with
    the same string value are not considered equal:

    >>> String('a') == String('a')
    True
    >>> String('a') == TypeIdentifier('a')
    False

    """
    def __new__(cls, string, docstring=None):
        return str.__new__(cls, string)

    def __init__(self, string, docstring=None):
        super(TypeTerm, self).__init__(docstring=docstring)

    def __repr__(self):
        return "<{} object ({}) at {}>".format(
            type(self).__name__, self, id(self))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return str.__eq__(self, other)

    def __ne__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return str.__ne__(self, other)


class TypeIdentifier(TypeTerm):
    """
    Type identifiers, or type names.

    Unlike other :class:`TypeTerms <TypeTerm>`, TypeIdentifiers use
    case-insensitive comparisons:

    >>> TypeIdentifier('MY-TYPE') == TypeIdentifier('my-type')
    True

    Args:
        string (str): type name
        docstring (str): documentation string

    Attributes:
        docstring (str): documentation string
    """

    def __eq__(self, other):
        if (isinstance(other, TypeTerm)
                and not isinstance(other, TypeIdentifier)):
            return NotImplemented
        return self.lower() == other.lower()

    def __ne__(self, other):
        if (isinstance(other, TypeTerm)
                and not isinstance(other, TypeIdentifier)):
            return NotImplemented
        return self.lower() != other.lower()


class String(TypeTerm):
    """
    Double-quoted strings.

    Args:
        string (str): type name
        docstring (str): documentation string

    Attributes:
        docstring (str): documentation string
    """


class Regex(TypeTerm):
    """
    Regular expression patterns.

    Args:
        string (str): type name
        docstring (str): documentation string

    Attributes:
        docstring (str): documentation string
    """


class AVM(FeatureStructure, Term):
    """
    A feature structure as used in TDL.

    Args:
        featvals (list, dict): a sequence of `(attribute, value)` pairs
            or an attribute to value mapping
        docstring (str): documentation string

    Attributes:
        docstring (str): documentation string
    """

    def __init__(
        self,
        featvals: Union[AttrSeq, AttrMap, None] = None,
        docstring=None,
    ) -> None:
        # super() doesn't work because I need to split the parameters
        FeatureStructure.__init__(self)
        Term.__init__(self, docstring=docstring)
        if featvals is not None:
            self.aggregate(featvals)

    @classmethod
    def _default(cls):
        return _ImplicitAVM()

    def __setitem__(self, key: str, val: Union['Conjunction', Term]) -> None:
        if not (val is None or isinstance(val, (Term, Conjunction))):
            raise TypeError(
                'invalid attribute value type: {}'.format(type(val).__name__)
            )
        super(AVM, self).__setitem__(key, val)

    def aggregate(self, featvals: Union[AttrSeq, AttrMap]) -> None:
        """Combine features in a single AVM.

        This function takes feature paths and values and merges them
        into the AVM, but does not do full unification. For example:

        >>> avm = tdl.AVM([("FEAT", tdl.TypeIdentifier("val1"))])
        >>> avm.aggregate([
        ...     ("FEAT", tdl.TypeIdentifier("val2")),
        ...     ("FEAT.SUB", tdl.TypeIdentifier("val3")),
        ... ])
        >>> print(tdl.format(avm))
        [ FEAT val1 & val2 & [ SUB val3 ] ]

        The *featvals* argument may be an sequence of (feature, value)
        pairs or a mapping of features to values.

        """
        if hasattr(featvals, 'items'):
            featvals = list(featvals.items())
        for feat, val in featvals:
            avm = self
            feat = feat.upper()
            while feat:
                subkey, _, rest = feat.partition(".")
                cur_val = avm.get(subkey)
                # new feature, just assign
                if subkey not in avm:
                    avm[feat] = val
                    break
                # last feature on path, conjoin
                elif not rest:
                    avm[subkey] = cur_val & val
                # non-conjunction implicit AVM; follow the dots
                elif isinstance(cur_val, _ImplicitAVM):
                    avm = cur_val
                # conjunction with implicit AVM; follow the AVM's dots
                elif (
                    isinstance(cur_val, Conjunction)
                    and (avm_ := cur_val._last_avm())
                    and isinstance(avm_, _ImplicitAVM)
                ):
                    avm = avm_
                # some other term; create conjunction with implicit AVM
                else:
                    avm_ = _ImplicitAVM()
                    avm[subkey] = cur_val & avm_
                    avm = avm_
                feat = rest

    def normalize(self):
        """
        Reduce trivial AVM conjunctions to just the AVM.

        For example, in `[ ATTR1 [ ATTR2 val ] ]` the value of `ATTR1`
        could be a conjunction with the sub-AVM `[ ATTR2 val ]`. This
        method removes the conjunction so the sub-AVM nests directly
        (equivalent to `[ ATTR1.ATTR2 val ]` in TDL).
        """
        for attr in self._avm:
            val = self._avm[attr]
            if isinstance(val, Conjunction):
                val.normalize()
                if len(val.terms) == 1 and isinstance(val.terms[0], AVM):
                    self._avm[attr] = val.terms[0]
            elif isinstance(val, AVM):
                val.normalize()

    def features(self, expand=False):
        """
        Return the list of tuples of feature paths and feature values.

        Args:
            expand (bool): if `True`, expand all feature paths
        Example:
            >>> avm = AVM([('A.B', TypeIdentifier('1')),
            ...            ('A.C', TypeIdentifier('2')])
            >>> avm.features()
            [('A', <AVM object at ...>)]
            >>> avm.features(expand=True)
            [('A.B', <TypeIdentifier object (1) at ...>),
             ('A.C', <TypeIdentifier object (2) at ...>)]
        """
        fs = []
        for featpath, val in super(AVM, self).features(expand=expand):
            # don't juse Conjunction.features() here because we want to
            # include the non-AVM terms, too
            if expand and isinstance(val, Conjunction):
                for term in val.terms:
                    if isinstance(term, AVM):
                        for fp, v in term.features(True):
                            fs.append((f'{featpath}.{fp}', v))
                    else:
                        fs.append((featpath, term))
            else:
                fs.append((featpath, val))
        return fs


class _ImplicitAVM(AVM):
    """AVM implicitly constructed by dot-notation and list syntax."""


class ConsList(AVM):
    """
    AVM subclass for cons-lists (``< ... >``)

    This provides a more intuitive interface for creating and
    accessing the values of list structures in TDL. Some combinations
    of the *values* and *end* parameters correspond to various TDL
    forms as described in the table below:

    ============  ========  =================  ======
    TDL form      values    end                state
    ============  ========  =================  ======
    `< >`         `None`    `EMPTY_LIST_TYPE`  closed
    `< ... >`     `None`    `LIST_TYPE`        open
    `< a >`       `[a]`     `EMPTY_LIST_TYPE`  closed
    `< a, b >`    `[a, b]`  `EMPTY_LIST_TYPE`  closed
    `< a, ... >`  `[a]`     `LIST_TYPE`        open
    `< a . b >`   `[a]`     `b`                closed
    ============  ========  =================  ======

    Args:
        values (list): a sequence of :class:`Conjunction` or
            :class:`Term` objects to be placed in the AVM of the list.
        end (str, :class:`Conjunction`, :class:`Term`): last item in
            the list (default: :data:`LIST_TYPE`) which determines if
            the list is open or closed
        docstring (str): documentation string

    Attributes:
        terminated (bool): if `False`, the list can be further
            extended by following the :data:`LIST_TAIL` features.
        docstring (str): documentation string

    """
    def __init__(self, values=None, end=LIST_TYPE, docstring=None):
        super(ConsList, self).__init__(docstring=docstring)

        if values is None:
            values = []
        self._last_path = ''
        self.terminated = False
        for value in values:
            self.append(value)
        self.terminate(end)

    def __len__(self):
        return len(self.values())

    def values(self):
        """
        Return the list of values in the ConsList feature structure.
        """
        if self._avm is None:
            return []
        else:
            return [val for _, val in _collect_list_items(self)]

    def append(self, value):
        """
        Append an item to the end of an open ConsList.

        Args:
            value (:class:`Conjunction`, :class:`Term`): item to add
        Raises:
            :class:`TDLError`: when appending to a closed list
        """
        if self._avm is not None and not self.terminated:
            path = self._last_path
            if path:
                path += '.'
            self[path + LIST_HEAD] = value
            self._last_path = path + LIST_TAIL
            self[self._last_path] = _ImplicitAVM()
        else:
            raise TDLError('Cannot append to a closed list.')

    def terminate(self, end):
        """
        Set the value of the tail of the list.

        Adding values via :meth:`append` places them on the `FIRST`
        feature of some level of the feature structure (e.g.,
        `REST.FIRST`), while :meth:`terminate` places them on the
        final `REST` feature (e.g., `REST.REST`). If *end* is a
        :class:`Conjunction` or :class:`Term`, it is typically a
        :class:`Coreference`, otherwise *end* is set to
        `tdl.EMPTY_LIST_TYPE` or `tdl.LIST_TYPE`. This method does
        not necessarily close the list; if *end* is `tdl.LIST_TYPE`,
        the list is left open, otherwise it is closed.

        Args:
            end (str, :class:`Conjunction`, :class:`Term`): value to
            use as the end of the list.
        """
        if self.terminated:
            raise TDLError('Cannot terminate a closed list.')
        if end == LIST_TYPE:
            self.terminated = False
        elif end == EMPTY_LIST_TYPE:
            if self._last_path:
                self[self._last_path] = None
            else:
                self._avm = None
            self.terminated = True
        elif self._last_path:
            self[self._last_path] = end
            self.terminated = True
        else:
            raise TDLError(
                f'Empty list must be {LIST_TYPE} or {EMPTY_LIST_TYPE}')


class DiffList(AVM):
    """
    AVM subclass for diff-lists (``<! ... !>``)

    As with :class:`ConsList`, this provides a more intuitive
    interface for creating and accessing the values of list structures
    in TDL. Unlike :class:`ConsList`, DiffLists are always closed
    lists with the last item coreferenced with the `LAST` feature,
    which allows for the joining of two diff-lists.

    Args:
        values (list): a sequence of :class:`Conjunction` or
            :class:`Term` objects to be placed in the AVM of the list
        docstring (str): documentation string

    Attributes:
        last (str): the feature path to the list position coreferenced
            by the value of the :data:`DIFF_LIST_LAST` feature.
        docstring (str): documentation string
    """
    def __init__(self, values=None, docstring=None):
        cr = Coreference(None)
        if values:
            # use ConsList to construct the list, but discard the class
            tmplist = ConsList(values, end=cr)
            dl_list = _ImplicitAVM()
            dl_list._avm.update(tmplist._avm)
            self.last = 'LIST.' + tmplist._last_path
        else:
            dl_list = cr
            self.last = 'LIST'
        dl_last = cr

        featvals = [(DIFF_LIST_LIST, dl_list),
                    (DIFF_LIST_LAST, dl_last)]
        super(DiffList, self).__init__(
            featvals, docstring=docstring)

    def __len__(self):
        return len(self.values())

    def values(self):
        """
        Return the list of values in the DiffList feature structure.
        """
        if isinstance(self[DIFF_LIST_LIST], Coreference):
            vals = []
        else:
            vals = [val for _, val
                    in _collect_list_items(self.get(DIFF_LIST_LIST))]
            vals.pop()  # last item of diff list is coreference
        return vals


def _collect_list_items(d):
    if not isinstance(d, AVM) or d.get(LIST_HEAD) is None:
        return []
    vals = [(LIST_HEAD, d[LIST_HEAD])]
    rest = d[LIST_TAIL]
    if isinstance(rest, _ImplicitAVM):
        vals.extend((LIST_TAIL + '.' + path, val)
                    for path, val in _collect_list_items(rest))
    elif rest is not None:
        vals.append((LIST_TAIL, rest))
    return vals


class Coreference(Term):
    """
    TDL coreferences, which represent re-entrancies in AVMs.

    Args:
        identifier (str): identifier or tag associated with the
            coreference; for internal use (e.g., in :class:`DiffList`
            objects), the identifier may be `None`
        docstring (str): documentation string

    Attributes:
        identifier (str): corefernce identifier or tag
        docstring (str): documentation string
    """
    def __init__(self, identifier, docstring=None):
        super(Coreference, self).__init__(docstring=docstring)
        self.identifier = identifier

    def __str__(self):
        if self.identifier is not None:
            return str(self.identifier)
        return ''


class Conjunction:
    """
    Conjunction of TDL terms.

    Args:
        terms (list): sequence of :class:`Term` objects
    """
    def __init__(self, terms=None):
        self._terms = []
        if terms is not None:
            for term in terms:
                self.add(term)

    def __repr__(self):
        return f"<Conjunction object at {id(self)}>"

    def __and__(self, other):
        if isinstance(other, Conjunction):
            return Conjunction(self._terms + other._terms)
        elif isinstance(other, Term):
            return Conjunction(self._terms + [other])
        else:
            return NotImplemented

    def __eq__(self, other):
        if isinstance(other, Term) and len(self._terms) == 1:
            return self._terms[0] == other
        elif not isinstance(other, Conjunction):
            return NotImplemented
        return self._terms == other._terms

    def __contains__(self, key):
        return any(key in term
                   for term in self._terms
                   if isinstance(term, AVM))

    def __getitem__(self, key):
        """Get the value of *key* across all AVMs in the conjunction"""
        terms = []
        for term in self._terms:
            if isinstance(term, AVM):
                val = term.get(key)
                if val is not None:
                    terms.append(val)
        if len(terms) == 0:
            raise KeyError(key)
        elif len(terms) == 1:
            return terms[0]
        else:
            return Conjunction(terms)

    def __setitem__(self, key, val):
        """Set *key* to *val* in the last AVM in the conjunction"""
        if avm := self._last_avm():
            avm[key] = val
        else:
            raise TDLError('no AVM in Conjunction')

    def __delitem__(self, key):
        """Delete *key* from all AVMs in the conjunction"""
        found = False
        for term in self._terms:
            if isinstance(term, AVM) and key in term:
                found = True
                del term[key]
        if not found:
            raise KeyError(key)

    def get(self, key, default=None):
        """
        Get the value of attribute *key* in any AVM in the conjunction.

        Args:
            key: attribute path to search
            default: value to return if *key* is not defined on any AVM
        """
        try:
            return self[key]
        except KeyError:
            return default

    def normalize(self):
        """
        Rearrange the conjunction to a conventional form.

        This puts any coreference(s) first, followed by type terms,
        then followed by AVM(s) (including lists). AVMs are
        normalized via :meth:`AVM.normalize`.
        """
        corefs = []
        types = []
        avms = []
        for term in self._terms:
            if isinstance(term, TypeTerm):
                types.append(term)
            elif isinstance(term, AVM):
                term.normalize()
                avms.append(term)
            elif isinstance(term, Coreference):
                corefs.append(term)
            else:
                raise TDLError(f'unexpected term {term}')
        self._terms = corefs + types + avms

    @property
    def terms(self):
        """The list of terms in the conjunction."""
        return list(self._terms)

    def add(self, term):
        """
        Add a term to the conjunction.

        Args:
            term (:class:`Term`, :class:`Conjunction`): term to add;
                if a :class:`Conjunction`, all of its terms are added
                to the current conjunction.
        Raises:
            :class:`TypeError`: when *term* is an invalid type
        """
        if isinstance(term, Conjunction):
            for term_ in term.terms:
                self.add(term_)
        elif isinstance(term, Term):
            self._terms.append(term)
        else:
            raise TypeError('Not a Term or Conjunction')

    def types(self):
        """Return the list of type terms in the conjunction."""
        return [term for term in self._terms
                if isinstance(term, (TypeIdentifier, String, Regex))]

    def features(self, expand=False):
        """Return the list of feature-value pairs in the conjunction."""
        featvals = []
        for term in self._terms:
            if isinstance(term, AVM):
                featvals.extend(term.features(expand=expand))
        return featvals

    def string(self):
        """
        Return the first string term in the conjunction, or `None`.
        """
        for term in self._terms:
            if isinstance(term, String):
                return str(term)
        return None  # conjunction does not have a string type (not an error)

    def _last_avm(self) -> Optional[AVM]:
        for term in reversed(self._terms):
            if isinstance(term, AVM):
                return term
        return None


class TypeDefinition:
    """
    A top-level Conjunction with an identifier.

    Args:
        identifier (str): type name
        conjunction (:class:`Conjunction`, :class:`Term`): type
            constraints
        docstring (str): documentation string

    Attributes:
        identifier (str): type identifier
        conjunction (:class:`Conjunction`): type constraints
        docstring (str): documentation string
    """

    _operator = ':='

    def __init__(self, identifier, conjunction, docstring=None):
        self.identifier = identifier

        if isinstance(conjunction, Term):
            conjunction = Conjunction([conjunction])
        assert isinstance(conjunction, Conjunction)
        self.conjunction = conjunction

        self.docstring = docstring

    def __repr__(self):
        return "<{} object '{}' at {}>".format(
            type(self).__name__, self.identifier, id(self)
        )

    @property
    def supertypes(self):
        """The list of supertypes for the type."""
        return self.conjunction.types()

    def features(self, expand=False):
        """Return the list of feature-value pairs in the conjunction."""
        return self.conjunction.features(expand=expand)

    def __contains__(self, key):
        return key in self.conjunction

    def __getitem__(self, key):
        return self.conjunction[key]

    def __setitem__(self, key, value):
        self.conjunction[key] = value

    def __delitem__(self, key):
        del self.conjunction[key]

    def documentation(self, level='first'):
        """
        Return the documentation of the type.

        By default, this is the first docstring on a top-level term.
        By setting *level* to `"top"`, the list of all docstrings on
        top-level terms is returned, including the type's `docstring`
        value, if not `None`, as the last item. The docstring for the
        type itself is available via :attr:`TypeDefinition.docstring`.

        Args:
            level (str): `"first"` or `"top"`
        Returns:
            a single docstring or a list of docstrings

        """
        docs = (t.docstring for t in list(self.conjunction.terms) + [self]
                if t.docstring is not None)
        if level.lower() == 'first':
            doc = next(docs, None)
        elif level.lower() == 'top':
            doc = list(docs)
        return doc


class TypeAddendum(TypeDefinition):
    """
    An addendum to an existing type definition.

    Type addenda, unlike :class:`type definitions <TypeDefinition>`,
    do not require supertypes, or even any feature constraints. An
    addendum, however, must have at least one supertype, AVM, or
    docstring.

    Args:
        identifier (str): type name
        conjunction (:class:`Conjunction`, :class:`Term`): type
            constraints
        docstring (str): documentation string

    Attributes:
        identifier (str): type identifier
        conjunction (:class:`Conjunction`): type constraints
        docstring (str): documentation string
    """

    _operator = ':+'

    def __init__(self, identifier, conjunction=None, docstring=None):
        if conjunction is None:
            conjunction = Conjunction()
        super(TypeAddendum, self).__init__(identifier, conjunction, docstring)


class LexicalRuleDefinition(TypeDefinition):
    """
    An inflecting lexical rule definition.

    Args:
        identifier (str): type name
        affix_type (str): `"prefix"` or `"suffix"`
        patterns (list): sequence of `(match, replacement)` pairs
        conjunction (:class:`Conjunction`, :class:`Term`): conjunction
            of constraints applied by the rule
        docstring (str): documentation string

    Attributes:
        identifier (str): type identifier
        affix_type (str): `"prefix"` or `"suffix"`
        patterns (list): sequence of `(match, replacement)` pairs
        conjunction (:class:`Conjunction`): type constraints
        docstring (str): documentation string
    """

    def __init__(self,
                 identifier,
                 affix_type,
                 patterns,
                 conjunction,
                 **kwargs):
        super(LexicalRuleDefinition, self).__init__(
            identifier, conjunction, **kwargs)
        self.affix_type = affix_type
        self.patterns = patterns


class _MorphSet:
    def __init__(self, var, characters):
        self.var = var
        self.characters = characters


class LetterSet(_MorphSet):
    """
    A capturing character class for inflectional lexical rules.

    LetterSets define a pattern (e.g., `"!a"`) that may match any one
    of its associated characters. Unlike :class:`WildCard` patterns,
    LetterSet variables also appear in the replacement pattern of an
    affixing rule, where they insert the character matched by the
    corresponding letter set.

    Args:
        var (str): variable used in affixing rules (e.g., `"!a"`)
        characters (str): string or collection of characters that may
            match an input character

    Attributes:
        var (str): letter-set variable
        characters (str): characters included in the letter-set
    """
    pass


class WildCard(_MorphSet):
    """
    A non-capturing character class for inflectional lexical rules.

    WildCards define a pattern (e.g., `"?a"`) that may match any one
    of its associated characters. Unlike :class:`LetterSet` patterns,
    WildCard variables may not appear in the replacement pattern of an
    affixing rule.

    Args:
        var (str): variable used in affixing rules (e.g., `"!a"`)
        characters (str): string or collection of characters that may
            match an input character

    Attributes:
        var (str): wild-card variable
        characters (str): characters included in the wild-card
    """
    pass


class _Environment:
    """
    TDL environment.
    """
    def __init__(self, entries=None):
        if entries is None:
            entries = []
        self.entries = entries


class TypeEnvironment(_Environment):
    """
    TDL type environment.

    Args:
        entries (list): TDL entries
    """


class InstanceEnvironment(_Environment):
    """
    TDL instance environment.

    Args:
        status (str): status (e.g., `"lex-rule"`)
        entries (list): TDL entries
    """
    def __init__(self, status, entries=None):
        super(InstanceEnvironment, self).__init__(entries)
        self.status = status


class FileInclude:
    """
    Include other TDL files in the current environment.

    Args:
        value: quoted value of the TDL include statement
        basedir: directory containing the file with the include
            statement
    Attributes:
        value: The quoted value of TDL include statement.
        path: The path to the TDL file to include.
    """
    def __init__(self, value: str = '', basedir: util.PathLike = '') -> None:
        self.value = value
        self.path = Path(basedir, value).with_suffix('.tdl')


class LineComment(str):
    """Single-line comments in TDL."""


class BlockComment(str):
    """Multi-line comments in TDL."""
