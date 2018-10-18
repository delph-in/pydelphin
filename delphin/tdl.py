# coding: utf-8

"""
Classes and functions for parsing and inspecting TDL.

This module makes it easy to inspect what is written on definitions in
Type Description Language (TDL), but it doesn't interpret type
hierarchies (such as by performing unification, subsumption
calculations, or creating GLB types). That is, while it wouldn't be
useful for creating a parser, it is useful if you want to statically
inspect the types in a grammar and the constraints they apply.

TDL was originally described in Krieger and Schäfer, 1994 [KS1994]_,
but it describes many features not in use by the DELPH-IN variant,
such as disjunction. Copestake, 2002 [COP2002]_ better describes the
subset in use by DELPH-IN, but it has become outdated and its TDL
syntax description is inaccurate in places, but it is still a great
resource for understanding the interpretation of TDL grammar
descriptions. The TdlRfc_ page of the `DELPH-IN Wiki`_ contains the
most up-to-date description of the TDL syntax used by DELPH-IN
grammars, including features such as documentation strings and regular
expressions.

.. [KS1994] Hans-Ulrich Krieger and Ulrich Schäfer.  TDL: a type
  description language for constraint-based grammars. In Proceedings
  of the 15th conference on Computational linguistics, volume 2, pages
  893–899. Association for Computational Linguistics, 1994.

.. [COP2002] Ann Copestake. Implementing typed feature structure
  grammars, volume 110. CSLI publications Stanford, 2002.

.. _TdlRfc: http://moin.delph-in.net/TdlRfc
.. _`DELPH-IN Wiki`: http://moin.delph-in.net/
"""

from __future__ import unicode_literals

import re
import io
from collections import deque, defaultdict
import textwrap
import warnings

from delphin.exceptions import (TdlError, TdlParsingError, TdlWarning)
from delphin.tfs import FeatureStructure
from delphin.util import LookaheadIterator, deprecated

str = type(u'')  # short-term fix for Python 2

# Values for list expansion
LIST_TYPE = '*list*'        #: type of lists in TDL
EMPTY_LIST_TYPE = '*null*'  #: type of list terminators
LIST_HEAD = 'FIRST'         #: feature for list items
LIST_TAIL = 'REST'          #: feature for list tails
DIFF_LIST_LIST = 'LIST'     #: feature for diff-list lists
DIFF_LIST_LAST = 'LAST'     #: feature for the last path in a diff-list

# Values for serialization
_base_indent = 2  # indent when an AVM starts on the next line
_max_inline_list_items = 3  # number of list items that may appear inline
_line_width = 79  # try not to go beyond this number of characters


# Classes for TDL entities

class Term(object):
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
            self.__class__.__name__, id(self))

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
            self.__class__.__name__, self, id(self))

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

    def __unicode__(self):
        return self.__str__()

    def __eq__(self, other):
        if (isinstance(other, TypeTerm) and
                not isinstance(other, TypeIdentifier)):
            return NotImplemented
        return self.lower() == other.lower()

    def __ne__(self, other):
        if (isinstance(other, TypeTerm) and
                not isinstance(other, TypeIdentifier)):
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

    def __unicode__(self):
        return self.__str__()


class Regex(TypeTerm):
    """
    Regular expression patterns.

    Args:
        string (str): type name
        docstring (str): documentation string

    Attributes:
        docstring (str): documentation string
    """

    def __unicode__(self):
        return self.__str__()


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

    def __init__(self, featvals=None, docstring=None):
        # super() doesn't work because I need to split the parameters
        FeatureStructure.__init__(self, featvals)
        Term.__init__(self, docstring=docstring)

    @classmethod
    def _default(cls): return AVM()

    def __setitem__(self, key, val):
        if not (val is None or isinstance(val, (Term, Conjunction))):
            raise TypeError('invalid attribute value type: {}'.format(
                val.__class__.__name__))
        super(AVM, self).__setitem__(key, val)

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
                            fs.append(('{}.{}'.format(featpath, fp), v))
                    else:
                        fs.append((featpath, term))
            else:
                fs.append((featpath, val))
        return fs


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
            vals = [val for _, val in _collect_list_items(self)]
            # the < a . b > notation puts b on the last REST path,
            # which is not returned by _collect_list_items()
            if self.terminated and self[self._last_path] is not None:
                vals.append(self[self._last_path])
            return vals

    def append(self, value):
        """
        Append an item to the end of an open ConsList.

        Args:
            value (:class:`Conjunction`, :class:`Term`): item to add
        Raises:
            :class:`TdlError`: when appending to a closed list
        """
        if self._avm is not None and not self.terminated:
            path = self._last_path
            if path:
                path += '.'
            self[path + LIST_HEAD] = value
            self._last_path = path + LIST_TAIL
            self[self._last_path] = AVM()
        else:
            raise TdlError('Cannot append to a closed list.')

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
            raise TdlError('Cannot terminate a closed list.')
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
            raise TdlError('Empty list must be {} or {}'.format(
                LIST_TYPE, EMPTY_LIST_TYPE))


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
            dl_list = AVM()
            dl_list._avm.update(tmplist._avm)
            dl_list._feats = tmplist._feats
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
        return [val for _, val
                in _collect_list_items(self.get(DIFF_LIST_LIST))]


def _collect_list_items(d):
    if d is None or not isinstance(d, AVM) or d.get(LIST_HEAD) is None:
        return []
    vals = [(LIST_HEAD, d[LIST_HEAD])]
    vals.extend((LIST_TAIL + '.' + path, val)
                for path, val in _collect_list_items(d.get(LIST_TAIL)))
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


class Conjunction(object):
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
        return "<Conjunction object at {}>".format(id(self))

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

    def __ne__(self, other):
        if not isinstance(other, Conjunction):
            return NotImplemented
        return self._terms != other._terms

    def __contains__(self, key):
        return any(key in term
                   for term in self._terms
                   if isinstance(term, AVM))

    def __getitem__(self, key):
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
                raise TdlError('unexpected term {}'.format(term))
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


class TypeDefinition(object):
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
            self.__class__.__name__, self.identifier, id(self)
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
        return self.conjunction.__getitem__(key)

    def __setitem__(self, key, value):
        return self.conjunction.__setitem__(key, value)

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


class _MorphSet(object):
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


class _Environment(object):
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


class FileInclude(object):
    """
    Include other TDL files in the current environment.

    Args:
        path (str): path to the TDL file to include
        basedir (str): parent directory of *path*
    """
    def __init__(self, path='', basedir=''):
        self.path = path
        self.basedir = basedir


# Old classes

class TdlDefinition(FeatureStructure):
    """
    A typed feature structure with supertypes.

    A TdlDefinition is like a :class:`~delphin.tfs.FeatureStructure`
    but each structure may have a list of supertypes.
    """

    @deprecated(final_version='v1.0.0', alternative='Conjunction')
    def __init__(self, supertypes=None, featvals=None):
        FeatureStructure.__init__(self, featvals=featvals)
        self.supertypes = list(supertypes or [])

    @classmethod
    def _default(cls): return TdlDefinition()

    def __repr__(self):
        return '<TdlDefinition object at {}>'.format(id(self))

    def _is_notable(self):
        """
        TdlDefinitions are notable if they define supertypes or have no
        sub-features or more than one sub-feature.
        """
        return bool(self.supertypes) or len(self._avm) != 1

    def local_constraints(self):
        """
        Return the constraints defined in the local AVM.
        """
        cs = []
        for feat, val in self._avm.items():
            try:
                if val.supertypes and not val._avm:
                    cs.append((feat, val))
                else:
                    for subfeat, subval in val.features():
                        cs.append(('{}.{}'.format(feat, subfeat), subval))
            except AttributeError:
                cs.append((feat, val))
        return cs


class TdlConsList(TdlDefinition):
    """
    A TdlDefinition for cons-lists (``< ... >``)

    Navigating the feature structure for lists can be cumbersome, so
    this subclass of :class:`TdlDefinition` provides the :meth:`values`
    method to collect the items nested inside the list and return them
    as a Python list.
    """
    def __repr__(self):
        return "<TdlConsList object at {}>".format(id(self))

    def values(self):
        """
        Return the list of values.
        """
        def collect(d):
            if d is None or d.get('FIRST') is None:
                return []
            vals = [d['FIRST']]
            vals.extend(collect(d.get('REST')))
            return vals
        return collect(self)


class TdlDiffList(TdlDefinition):
    """
    A TdlDefinition for diff-lists (``<! ... !>``)

    Navigating the feature structure for lists can be cumbersome, so
    this subclass of :class:`TdlDefinition` provides the :meth:`values`
    method to collect the items nested inside the list and return them
    as a Python list.
    """
    def __repr__(self):
        return "<TdlDiffList object at {}>".format(id(self))

    def values(self):
        """
        Return the list of values.
        """
        def collect(d):
            if d is None or d.get('FIRST') is None:
                return []
            vals = [d['FIRST']]
            vals.extend(collect(d.get('REST')))
            return vals
        return collect(self.get('LIST'))


class TdlType(TdlDefinition):
    """
    A top-level TdlDefinition with an identifier.

    Args:
        identifier (str): type name
        definition (:class:`TdlDefinition`): definition of the type
        coreferences (list): (tag, paths) tuple of coreferences, where
            paths is a list of feature paths that share the tag
        docstring (list): list of documentation strings
    """

    @deprecated(final_version='v1.0.0', alternative='TypeDefinition')
    def __init__(self, identifier, definition, coreferences=None,
                 docstring=None):
        TdlDefinition.__init__(self, definition.supertypes,
                               definition._avm.items())
        self.identifier = identifier
        self.definition = definition
        self.coreferences = list(coreferences or [])
        if docstring is None:
            docstring = []
        self.docstring = docstring

    def __repr__(self):
        return "<TdlType object '{}' at {}>".format(
            self.identifier, id(self)
        )

    # @property
    # def supertypes(self):
    #     return self.definition.supertypes


class TdlInflRule(TdlType):
    """
    TDL inflectional rule.

    Args:
        identifier (str): type name
        affix (str): inflectional affixes
    """

    @deprecated(final_version='v1.0.0', alternative='LexicalRuleDefinition')
    def __init__(self, identifier, affix=None, **kwargs):
        TdlType.__init__(self, identifier, **kwargs)
        self.affix = affix


# NOTE: be careful rearranging subpatterns in _tdl_lex_re; some must
#       appear before others, e.g., """ before ", <! before <, etc.,
#       to prevent short-circuiting from blocking the larger patterns
# NOTE: some patterns only match the beginning (e.g., """, #|, etc.)
#       as they require separate handling for proper lexing
# NOTE: only use one capture group () for each pattern; if grouping
#       inside the pattern is necessary, use non-capture groups (?:)
_tdl_lex_re = re.compile(
    r'''# regex-pattern                gid  description
    (""")                            #   1  start of multiline docstring
    |(\#\|)                          #   2  start of multiline comment
    |;([^\n]*)                       #   3  single-line comment
    |"([^"\\]*(?:\\.[^"\\]*)*)"      #   4  double-quoted "strings"
    |'([^\s!"#$&'(),./:;<=>[\]^]+)   #   5  single-quoted 'symbols
    |\^([^$\\]*(?:\\.|[^$\\]*)*)\$   #   6  regular expression
    |(:[=<])                         #   7  type def operator
    |(:\+)                           #   8  type addendum operator
    |(\.\.\.)                        #   9  list ellipsis
    |(\.)                            #  10  dot operator
    |(&)                             #  11  conjunction operator
    |(,)                             #  12  list delimiter
    |(\[)                            #  13  AVM open
    |(<!)                            #  14  diff list open
    |(<)                             #  15  cons list open
    |(\])                            #  16  AVM close
    |(!>)                            #  17  diff list close
    |(>)                             #  18  cons list close
    |\#([^\s!"#$&'(),./:;<=>[\]^]+)  #  19  coreference
    |%\s*\((.*)\)\s*$                #  20  letter-set or wild-card
    |%(prefix|suffix)                #  21  start of affixing pattern
    |\(([^ ]+\s+(?:[^ )\\]|\\.)+)\)  #  22  affix subpattern
    |(\/)                            #  23  defaults (currently unused)
    |([\w_+*?-]+)                    #  24  identifiers and symbols
    |(:begin)                        #  25  start a :type or :instance block
    |(:end)                          #  26  end a :type or :instance block
    |(:type|:instance)               #  27  environment type
    |(:status)                       #  28  instance status
    |(:include)                      #  29  file inclusion
    |([^\s])                         #  30  unexpected
    ''',
    flags=re.VERBOSE|re.UNICODE)


# Parsing helper functions

def _is_comment(data):
    """helper function for filtering out comments"""
    return 2 <= data[0] <= 3


def _peek(tokens, n=0):
    """peek and drop comments"""
    return tokens.peek(n=n, skip=_is_comment, drop=True)


def _next(tokens):
    """pop the next token, dropping comments"""
    return tokens.next(skip=_is_comment)


def _shift(tokens):
    """pop the next token, then peek the gid of the following"""
    after = tokens.peek(n=1, skip=_is_comment, drop=True)
    tok = tokens._buffer.popleft()
    return tok[0], tok[1], tok[2], after[0]


def _accumulate(lexitems):
    """
    Yield lists of tokens based on very simple parsing that checks the
    level of nesting within a structure. This is probably much faster
    than the LookaheadIterator method, but it is less safe; an unclosed
    list or AVM may cause it to build a list including the rest of the
    file, or it may return a list that doesn't span a full definition.

    As PyDelphin's goals for TDL parsing do not include speed, this
    method is not currently used, although it is retained in the source
    code as an example if future priorities change.
    """
    data = []
    stack = []
    break_on = 10
    in_def = False
    for item in lexitems:
        gid = item[0]
        # only yield comments outside of definitions
        if gid in (2, 3):
            if len(data) == 0:
                yield [item]
            else:
                continue
        elif gid == 20:
            assert len(data) == 0
            yield [item]
        # the following just checks if the previous definition was not
        # terminated when the next one is read in
        elif gid in (7, 8):
            if in_def:
                yield data[:-1]
                data = data[-1:] + [item]
                stack = []
                break_on = 10
            else:
                data.append(item)
                in_def = True
        else:
            data.append(item)
            if gid == break_on:
                if len(stack) == 0:
                    yield data
                    data = []
                    in_def = False
                else:
                    break_on = stack.pop()
            elif gid in (13, 14, 15):
                stack.append(break_on)
                break_on = gid + 3
    if data:
        yield data


def _lex(stream):
    """
    Lex the input stream according to _tdl_lex_re.

    Yields
        (gid, token, line_number)
    """
    lines = enumerate(stream, 1)
    line_no = pos = 0
    try:
        while True:
            if pos == 0:
                line_no, line = next(lines)
            matches = _tdl_lex_re.finditer(line, pos)
            pos = 0  # reset; only used for multiline patterns
            for m in matches:
                gid = m.lastindex
                if gid <= 2:  # potentially multiline patterns
                    if gid == 1:  # docstring
                        s, start_line_no, line_no, line, pos = _bounded(
                            '"""', '"""', line, m.end(), line_no, lines)
                    elif gid == 2:  # comment
                        s, start_line_no, line_no, line, pos = _bounded(
                            '#|', '|#', line, m.end(), line_no, lines)
                    yield (gid, s, line_no)
                    break
                elif gid == 30:
                    raise TdlParsingError(
                        ('Syntax error:\n  {}\n {}^'
                         .format(line, ' ' * m.start())),
                        line_number=line_no)
                else:
                    # token = None
                    # if not (6 < gid < 20):
                    #     token = m.group(gid)
                    token = m.group(gid)
                    yield (gid, token, line_no)
    except StopIteration:
        pass


def _bounded(p1, p2, line, pos, line_no, lines):
    """Collect the contents of a bounded multiline string"""
    substrings = []
    start_line_no = line_no
    end = pos
    while not line.startswith(p2, end):
        if line[end] == '\\':
            end += 2
        else:
            end += 1
        if end >= len(line):
            substrings.append(line[pos:])
            try:
                line_no, line = next(lines)
            except StopIteration:
                pattern = 'docstring' if p1 == '"""' else 'block comment'
                raise TdlParsingError('Unterminated {}'.format(pattern),
                                      line_number=start_line_no)
            pos = end = 0
    substrings.append(line[pos:end])
    end += len(p2)
    return ''.join(substrings), start_line_no, line_no, line, end


# Parsing functions
def iterparse(source, encoding='utf-8'):
    """
    Parse the TDL file *source* and iteratively yield parse events.

    If *source* is a filename, the file is opened and closed when the
    generator has finished, otherwise *source* is an open file object
    and will not be closed when the generator has finished.

    Parse events are `(event, object, lineno)` tuples, where `event`
    is a string (`"TypeDefinition"`, `"TypeAddendum"`,
    `"LexicalRuleDefinition"`, `"LetterSet"`, `"WildCard"`,
    `"LineComment"`, or `"BlockComment"`), `object` is the interpreted
    TDL object, and `lineno` is the line number where the entity began
    in *source*.

    Args:
        source (str, file): a filename or open file object
        encoding (str): the encoding of the file (default: `"utf-8"`;
            ignored if *source* is an open file)
    Yields:
        `(event, object, lineno)` tuples
    Example:
        >>> lex = {}
        >>> for event, obj, lineno in tdl.iterparse('erg/lexicon.tdl'):
        ...     if event == 'TypeDefinition':
        ...         lex[obj.identifier] = obj
        ... 
        >>> lex['eucalyptus_n1']['SYNSEM.LKEYS.KEYREL.PRED']
        <String object (_eucalyptus_n_1_rel) at 140625748595960>
    """
    if hasattr(source, 'read'):
        for event in _parse2(source):
            yield event
    else:
        with io.open(source, encoding=encoding) as fh:
            for event in _parse2(fh):
                yield event


def _parse2(f):
    tokens = LookaheadIterator(_lex(f))
    try:
        for event in _parse_tdl(tokens):
            yield event
    except TdlParsingError as ex:
        if hasattr(f, 'name'):
            ex.filename = f.name
        raise


def _parse_tdl(tokens):
    environment = None
    envstack = []
    try:
        line_no = 1
        while True:
            obj = None
            try:
                gid, token, line_no = tokens.next()
            except StopIteration:  # normal EOF
                break
            if gid == 2:
                yield ('BlockComment', token, line_no)
            elif gid == 3:
                yield ('LineComment', token, line_no)
            elif gid == 20:
                obj = _parse_letterset(token, line_no)
                yield (obj.__class__.__name__, obj, line_no)
            elif gid == 24:
                obj = _parse_tdl_definition(token, tokens)
                yield (obj.__class__.__name__, obj, line_no)
            elif gid == 25:
                envstack.append(environment)
                _environment = _parse_tdl_begin_environment(tokens)
                if environment is not None:
                    environment.entries.append(_environment)
                environment = _environment
                yield ('BeginEnvironment', environment, line_no)
            elif gid == 26:
                _parse_tdl_end_environment(tokens, environment)
                yield ('EndEnvironment', environment, line_no)
                environment = envstack.pop()
            elif gid == 29:
                obj = _parse_tdl_include(tokens)
                yield ('FileInclude', obj, line_no)
            else:
                raise TdlParsingError(
                    'Syntax error; unexpected token: {}'.format(token),
                    line_number=line_no)
            if environment is not None and obj is not None:
                environment.entries.append(obj)
    except StopIteration:
        raise TdlParsingError('Unexpected end of input.')


def _parse_tdl_definition(identifier, tokens):
    gid, token, line_no, nextgid = _shift(tokens)

    if gid == 7 and nextgid == 21:  # lex rule with affixes
        atype, pats = _parse_tdl_affixes(tokens)
        conjunction, nextgid = _parse_tdl_conjunction(tokens)
        obj = LexicalRuleDefinition(
            identifier, atype, pats, conjunction)

    elif gid == 7:
        if token == ':<':
            warnings.warn(
                'Subtype operator :< encountered at line {} for '
                '{}; Continuing as if it were the := operator.'
                .format(line_no, identifier),
                TdlWarning)
        conjunction, nextgid = _parse_tdl_conjunction(tokens)
        if isinstance(conjunction, Term):
            conjunction = Conjunction([conjunction])
        if len(conjunction.types()) == 0:
            raise TdlParsingError('No supertypes defined.',
                                  identifier=identifier,
                                  line_number=line_no)
        obj = TypeDefinition(identifier, conjunction)

    elif gid == 8:
        if nextgid == 1 and _peek(tokens, n=1)[0] == 10:
            # docstring will be handled after the if-block
            conjunction = Conjunction()
        else:
            conjunction, nextgid = _parse_tdl_conjunction(tokens)
        obj = TypeAddendum(identifier, conjunction)

    else:
        raise TdlParsingError("Expected: := or :+",
                              line_number=line_no)

    if nextgid == 1:  # pre-dot docstring
        _, token, _, nextgid = _shift(tokens)
        obj.docstring = token
    if nextgid != 10:  # . dot
        raise TdlParsingError('Expected: .', line_number=line_no)
    tokens.next()

    return obj


def _parse_letterset(token, line_no):
    end = r'\s+((?:[^) \\]|\\.)+)\)\s*$'
    m = re.match(r'\s*letter-set\s*\((!.)' + end, token)
    if m is not None:
        chars = re.sub(r'\\(.)', r'\1', m.group(2))
        return LetterSet(m.group(1), chars)
    else:
        m = re.match(r'\s*wild-card\s*\((\?.)' + end, token)
        if m is not None:
            chars = re.sub(r'\\(.)', r'\1', m.group(2))
            return WildCard(m.group(1), chars)
    # if execution reached here there was a problems
    raise TdlParsingError(
        'invalid letter-set or wild-card: {}'.format(token),
        line_number=line_no)


def _parse_tdl_affixes(tokens):
    gid, token, line_no, nextgid = _shift(tokens)
    assert gid == 21
    affixtype = token
    affixes = []
    while nextgid == 22:
        gid, token, line_no, nextgid = _shift(tokens)
        match, replacement = token.split(None, 1)
        affixes.append((match, replacement))
    return affixtype, affixes


def _parse_tdl_conjunction(tokens):
    terms = []
    while True:
        term, nextgid = _parse_tdl_term(tokens)
        terms.append(term)
        if nextgid == 11:  # & operator
            tokens.next()
        else:
            break
    if len(terms) == 1:
        return terms[0], nextgid
    else:
        return Conjunction(terms), nextgid


def _parse_tdl_term(tokens):
    doc = None

    gid, token, line_no, nextgid = _shift(tokens)

    # docstrings are not part of the conjunction so check separately
    if gid == 1:  # docstring
        doc = token
        gid, token, line_no, nextgid = _shift(tokens)

    if gid == 4:  # string
        term = String(token, docstring=doc)
    elif gid == 5:  # quoted symbol
        warnings.warn(
            'Single-quoted symbol encountered at line {}; '
            'Continuing as if it were a regular symbol.'
            .format(line_no),
            TdlWarning)
        term = TypeIdentifier(token, docstring=doc)
    elif gid == 6:  # regex
        term = Regex(token, docstring=doc)
    elif gid == 13:  # AVM open
        featvals, nextgid = _parse_tdl_feature_structure(tokens)
        term = AVM(featvals, docstring=doc)
    elif gid == 14:  # diff list open
        values, _, nextgid = _parse_tdl_list(tokens, break_gid=17)
        term = DiffList(values, docstring=doc)
    elif gid == 15:  # cons list open
        values, end, nextgid = _parse_tdl_list(tokens, break_gid=18)
        term = ConsList(values, end=end, docstring=doc)
    elif gid == 19:  # coreference
        term = Coreference(token, docstring=doc)
    elif gid == 24:  # identifier
        term = TypeIdentifier(token, docstring=doc)
    else:
        raise TdlParsingError('Expected a TDL conjunction term.',
                              line_number=line_no)
    return term, nextgid


def _parse_tdl_feature_structure(tokens):
    feats = []
    gid, token, line_no, nextgid = _shift(tokens)
    if gid != 16:  # ] feature structure terminator
        while True:
            if gid != 24:  # identifier (attribute name)
                raise TdlParsingError('Expected a feature name',
                                      line_number=line_no)
            path = [token]
            while nextgid == 10:  # . dot
                tokens.next()
                gid, token, line_no, nextgid = _shift(tokens)
                assert gid == 24
                path.append(token)
            attr = '.'.join(path)

            conjunction, nextgid = _parse_tdl_conjunction(tokens)
            feats.append((attr, conjunction))

            if nextgid == 12:  # , list delimiter
                tokens.next()
                gid, token, line_no, nextgid = _shift(tokens)
            elif nextgid == 16:
                gid, _, _, nextgid = _shift(tokens)
                break
            else:
                raise TdlParsingError('Expected: , or ]',
                                      line_number=line_no)

    assert gid == 16

    return feats, nextgid


def _parse_tdl_list(tokens, break_gid):
    values = []
    end = None
    nextgid = _peek(tokens)[0]
    if nextgid == break_gid:
        _, _, _, nextgid = _shift(tokens)
    else:
        while True:
            if nextgid == 9:  # ... ellipsis
                _, _, _, nextgid = _shift(tokens)
                end = LIST_TYPE
                break
            else:
                term, nextgid = _parse_tdl_conjunction(tokens)
                values.append(term)

            if nextgid == 10:  # . dot
                tokens.next()
                end, nextgid = _parse_tdl_conjunction(tokens)
                break
            elif nextgid == break_gid:
                break
            elif nextgid == 12:  # , comma delimiter
                _, _, _, nextgid = _shift(tokens)
            else:
                raise TdlParsingError('Expected: comma or end of list')

        gid, _, line_no, nextgid = _shift(tokens)
        if gid != break_gid:
            raise TdlParsingError('Expected: end of list',
                                  line_number=line_no)

    if len(values) == 0 and end is None:
        end = EMPTY_LIST_TYPE

    return values, end, nextgid


def _parse_tdl_begin_environment(tokens):
    gid, envtype, lineno = tokens.next()
    if gid != 27:
        raise TdlParsingError('Expected: :type or :instance',
                              line_number=lineno)
    gid, token, lineno = tokens.next()
    if envtype == ':instance':
        status = envtype[1:]
        if token == ':status':
            status = tokens.next()[1]
            gid, token, lineno = tokens.next()
        elif gid != 10:
            raise TdlParsingError('Expected: :status or .',
                                  line_number=lineno)
        env = InstanceEnvironment(status)
    else:
        env = TypeEnvironment()
    if gid != 10:
        raise TdlParsingError('Expected: .', line_number=lineno)
    return env


def _parse_tdl_end_environment(tokens, env):
    _, envtype, lineno = tokens.next()
    if envtype == ':type' and not isinstance(env, TypeEnvironment):
        raise TdlParsingError('Expected: :type', line_number=lineno)
    elif envtype == ':instance' and not isinstance(env, InstanceEnvironment):
        raise TdlParsingError('Expected: :instance', line_number=lineno)
    gid, _, lineno = tokens.next()
    if gid != 10:
        raise TdlParsingError('Expected: .', line_number=lineno)
    return envtype


def _parse_tdl_include(tokens):
    gid, path, lineno = tokens.next()
    if gid != 4:
        raise TdlParsingError('Expected: a quoted filename',
                              line_number=lineno)
    gid, _, lineno = tokens.next()
    if gid != 10:
        raise TdlParsingError('Expected: .', line_number=lineno)
    return FileInclude(path)


break_characters = r'<>!=:.#&,[];$()^/"'

_tdl_re = re.compile(
    r'("""[^"\\]*(?:(?:\\.|"(?!")|""(?!"))[^"\\]*)*(?:""")?'  # """doc"""
    r'|"[^"\\]*(?:\\.[^"\\]*)*"'  # double-quoted "strings"
    r"|'[^ \\]*(?:\\.[^ \\]*)*"  # single-quoted 'strings
    r'|[^\s{break_characters}]+'  # terms w/o break chars
    r'|#[^\s{break_characters}]+'  # coreferences
    r'|!\w'  # character classes
    r'|:=|:\+|:<|<!|!>|\.\.\.'  # special punctuation constructs
    r'|[{break_characters}])'  # break characters
    .format(break_characters=re.escape(break_characters)),
    re.MULTILINE
)

# both ;comments and #|comments|#
_tdl_start_comment_re = re.compile(r'^\s*;|^\s*#\|')
_tdl_end_comment_re = re.compile(r'.*#\|\s*$')


@deprecated(final_version='v1.0.0')
def tokenize(s):
    """
    Tokenize a string *s* of TDL code.
    """
    return [m.group(m.lastindex) for m in _tdl_re.finditer(s)]


@deprecated(final_version='v1.0.0')
def lex(stream):
    lines = enumerate(stream, 1)
    line_no = 0
    try:
        while True:
            block = None
            line_no, line = next(lines)
            if re.match(r'^\s*;', line):
                yield (line_no, 'LINECOMMENT', line)
            elif re.match(r'^\s*#\|', line):
                block = []
                while not re.match(r'.*\|#\s*$', line):
                    block.append(line)
                    _, line = next(lines)
                block.append(line)  # also add the last match
                yield (line_no, 'BLOCKCOMMENT', ''.join(block))
            elif re.match(r'^\s*$', line):
                continue
            elif re.match(r'^\s*%', line):
                block = _read_block('(', ')', line, lines)
                yield (line_no, 'LETTERSET', block)
            else:
                block = _read_block('[', ']', line, lines, terminator='.')
                yield (line_no, 'TYPEDEF', block)

    except StopIteration:
        if block:
            raise TdlParsingError(
                'Unexpected termination around line {}.'.format(line_no)
            )


def _read_block(in_pattern, out_pattern, line, lines, terminator=None):
    block = []
    try:
        tokens = tokenize(line)
        # fixup for multiline docstrings and comments
        tail = tokens[-1]
        while tail.startswith('"""') and not tail.endswith('"""'):
            tokens[-1:] = tokenize(tail + next(lines)[1])
            tail = tokens[-1]
        while tail.startswith('#|') and not tail.endswith('|#'):
            tokens[-1:] = tokenize(tail + next(lines)[1])
            tail = tokens[-1]
        lvl = _nest_level(in_pattern, out_pattern, tokens)
        while lvl > 0 or (terminator and tokens[-1] != terminator):
            block.extend(tokens)
            _, line = next(lines)
            tokens = tokenize(line)
            lvl += _nest_level(in_pattern, out_pattern, tokens)
        block.extend(tokens)  # also add the last match
    except StopIteration:
        pass  # the next StopIteration should catch this so return block
    return block


def _nest_level(in_pattern, out_pattern, tokens):
    lookup = {in_pattern: 1, out_pattern: -1}
    return sum(lookup.get(tok, 0) for tok in tokens)


@deprecated(final_version='v1.0.0', alternative='iterparse()')
def parse(f, encoding='utf-8'):
    """
    Parse the TDL file *f* and yield the interpreted contents.

    If *f* is a filename, the file is opened and closed when the
    generator has finished, otherwise *f* is an open file object and
    will not be closed when the generator has finished.

    Args:
        f (str, file): a filename or open file object
        encoding (str): the encoding of the file (default: `"utf-8"`;
            ignored if *f* is an open file)
    """
    if hasattr(f, 'read'):
        for event in _parse(f):
            yield event
    else:
        with io.open(f, encoding=encoding) as fh:
            for event in _parse(fh):
                yield event


def _parse(f):
    for line_no, event, data in lex(f):
        data = deque(data)
        try:
            if event == 'TYPEDEF':
                yield _parse_typedef(data)
        except TdlParsingError as ex:
            ex.line_number = line_no
            if hasattr(f, 'name'):
                ex.filename = f.name
            raise


def _parse_typedef(tokens):
    t = None
    identifier = None  # in case of StopIteration on first token
    try:
        identifier = tokens.popleft()
        assignment = tokens.popleft()
        affixes = _parse_affixes(tokens)  # only for inflectional rules
        tdldef, corefs, doc = _parse_conjunction(tokens)
        # Now make coref paths a string instead of list
        corefs = _make_coreferences(corefs)
        # features = parse_conjunction(tokens)
        if tokens[0].startswith('"""'):
            doc.append(_parse_docstring(tokens))
        assert tokens.popleft() == '.'
        # :+ doesn't need supertypes
        if assignment != ':+' and len(tdldef.supertypes) == 0:
            raise TdlParsingError('Type definition requires supertypes.')
        t = TdlType(identifier, tdldef, coreferences=corefs, docstring=doc)
    except AssertionError:
        msg = 'Remaining tokens: {}'.format(list(tokens))
        #   previously used six library:
        # raise_from(TdlParsingError(msg, identifier=identifier), ex)
        #   use the following when Python2.7 support is dropped
        # raise TdlParsingError(msg, identifier=identifier) from ex
        raise TdlParsingError(msg, identifier=identifier)
    except (StopIteration, IndexError):
        msg = 'Unexpected termination.'
        #   previously used six library:
        # raise_from(TdlParsingError(msg, identifier=identifier or '?'), ex)
        #   use the following when Python2.7 support is dropped
        # raise TdlParsingError(msg, identifier=identifier or '?') from ex
        raise TdlParsingError(msg, identifier=identifier or '?')
    return t


def _parse_affixes(tokens):
    affixes = None
    if tokens[0] in ('%prefix', '%suffix'):
        affixes = []
        aff = tokens.popleft()
        while tokens[0] == '(':
            tokens.popleft()  # the '('
            affixes.append(tokens.popleft(), tokens.popleft())
            assert tokens.popleft() == ')'
    return affixes


def _parse_conjunction(tokens):
    if tokens and tokens[0][:1] in ('\'"') and tokens[0][:3] != '"""':
        return tokens.popleft(), [], []  # basic string value
    supertypes = []
    features = []
    coreferences = []
    doc = []

    cls = TdlDefinition  # default type

    # type-addendum with only a docstring
    if tokens[0].startswith('"""') and tokens[1] == '.':
        doc.append(_parse_docstring(tokens))
        return cls(), coreferences, doc

    tokens.appendleft('&')  # simplify the loop
    while tokens[0] == '&':
        tokens.popleft()  # remove '&'

        feats = []
        corefs = []
        if tokens[0].startswith('"""'):
            doc.append(_parse_docstring(tokens))

        if tokens[0] == '.':
            raise TdlParsingError('"." cannot appear after & in conjunction.')

        if tokens[0].startswith('#'):
            # coreferences don't have features, so just add it and move on
            coreferences.append((tokens.popleft(), [[]]))
            continue
        # other terms may have features or other coreferences
        elif tokens[0] == '[':
            feats, corefs = _parse_avm(tokens)
        elif tokens[0] == '<':
            feats, corefs = _parse_cons_list(tokens)
            cls = TdlConsList
        elif tokens[0] == '<!':
            feats, corefs = _parse_diff_list(tokens)
            cls = TdlDiffList
        # elif tokens[0][:1] in ('\'"'):
        #     raise TdlParsingError('String cannot be part of a conjunction.')
        elif not tokens[0].startswith('"""'):
            supertypes.append(tokens.popleft())

        if feats is None:
            features = None
        else:
            assert features is not None
            features.extend(feats)
        coreferences.extend(corefs)

    if features is None and cls is TdlDefinition:
        tdldef = None
    else:
        tdldef = cls(supertypes, features)

    return tdldef, coreferences, doc


def _parse_docstring(tokens):
    assert tokens[0].endswith('"""')
    return tokens.popleft()[3:-3]


def _parse_avm(tokens):
    # [ attr-val (, attr-val)* ]
    features = []
    coreferences = []
    assert tokens.popleft() == '['
    if tokens[0] != ']':  # non-empty AVM
        tokens.appendleft(',')  # to make the loop simpler
    while tokens[0] != ']':
        tokens.popleft()
        attrval, corefs = _parse_attr_val(tokens)
        features.append(attrval)
        coreferences.extend(corefs)
    # '[', '.', '"', '/', '<', '#'
    assert tokens.popleft() == ']'
    return features, coreferences


def _parse_attr_val(tokens):
    # PATH(.PATH)* val
    path = [tokens.popleft()]
    while tokens[0] == '.':
        tokens.popleft()
        path.append(tokens.popleft())
    path = '.'.join(path)  # put it back together (maybe shouldn'ta broke it)
    value, corefs, _ = _parse_conjunction(tokens)
    corefs = [(c, [[path] + p for p in ps]) for c, ps in corefs]
    return ((path, value), corefs)


def _parse_cons_list(tokens):
    assert tokens.popleft() == '<'
    feats, last_path, coreferences = _parse_list(tokens, ('>', '.', '...'))
    if tokens[0] == '...':  # < ... > or < a, ... >
        tokens.popleft()
        # do nothing (don't terminate the list)
    elif tokens[0] == '.':  # e.g. < a . #x >
        tokens.popleft()
        tdldef, corefs, _ = _parse_conjunction(tokens)
        feats.append((last_path, tdldef))
        corefs = [(c, [[last_path] + p for p in ps]) for c, ps in corefs]
        coreferences.extend(corefs)
    elif len(feats) == 0:  # < >
        feats = None  # list is null; nothing can be added
    else:  # < a, b >
        feats.append((last_path, None))  # terminate the list
    assert tokens.popleft() == '>'
    return (feats, coreferences)


def _parse_diff_list(tokens):
    assert tokens.popleft() == '<!'
    feats, last_path, coreferences = _parse_list(tokens, ('!>'))
    if not feats:
        # always have the LIST path
        feats.append((DIFF_LIST_LIST, TdlDefinition()))
        last_path = DIFF_LIST_LIST
    else:
        # prepend 'LIST' to all paths
        feats = [('.'.join([DIFF_LIST_LIST, path]), val)
                 for path, val in feats]
        last_path = '{}.{}'.format(DIFF_LIST_LIST, last_path)
    # always have the LAST path
    feats.append((DIFF_LIST_LAST, TdlDefinition()))
    coreferences.append((None, [[last_path], [DIFF_LIST_LAST]]))
    assert tokens.popleft() == '!>'
    return (feats, coreferences)


def _parse_list(tokens, break_on):
    feats = []
    coreferences = []
    path = LIST_HEAD
    while tokens[0] not in break_on:
        tdldef, corefs, _ = _parse_conjunction(tokens)
        feats.append((path, tdldef))
        corefs = [(c, [[path] + p for p in ps]) for c, ps in corefs]
        coreferences.extend(corefs)
        if tokens[0] == ',':
            path = '{}.{}'.format(LIST_TAIL, path)
            tokens.popleft()
        elif tokens[0] == '.':
            break
    path = path.replace(LIST_HEAD, LIST_TAIL)
    return (feats, path, coreferences)


def _make_coreferences(corefs):
    corefs = [(cr, ['.'.join(p) for p in paths]) for cr, paths in corefs]
    merged = defaultdict(list)
    unlabeled = []
    # unlabeled ones (e.g. from diff lists) don't have a coref tag, but
    # probably already have all the paths-to-unify. Labeled ones likely
    # only have one path each, so merge those with the same tag.
    for (cr, paths) in corefs:
        if cr is None:
            unlabeled.append((cr, paths))
        else:
            merged[cr].extend(paths)
    # now we can put them back together
    corefs = list(merged.items()) + unlabeled
    # just check that all have at least two paths
    if not all(len(paths) >= 2 for cr, paths in corefs):
        raise TdlError(
            'Solitary coreference: {}\n{}'
            .format(str(cr), repr(paths))
        )
    return corefs


# Serialization helpers

def format(obj, indent=0):
    """
    Serialize TDL objects to strings.

    Args:
        obj: instance of :class:`Term`, :class:`Conjunction`, or
            :class:`TypeDefinition` classes or subclasses
        indent (int): number of spaces to indent the formatted object
    Returns:
        str: serialized form of *obj*
    Example:
        >>> conj = tdl.Conjunction([
        ...     tdl.TypeIdentifier('lex-item'),
        ...     tdl.AVM([('SYNSEM.LOCAL.CAT.HEAD.MOD',
        ...               tdl.ConsList(end=tdl.EMPTY_LIST_TYPE))])
        ... ])
        >>> t = tdl.TypeDefinition('non-mod-lex-item', conj)
        >>> print(format(t))
        non-mod-lex-item := lex-item &
          [ SYNSEM.LOCAL.CAT.HEAD.MOD < > ].
    """
    if isinstance(obj, TypeDefinition):
        return _format_typedef(obj, indent)
    elif isinstance(obj, Conjunction):
        return _format_conjunction(obj, indent)
    elif isinstance(obj, Term):
        return _format_term(obj, indent)
    elif isinstance(obj, _MorphSet):
        return _format_morphset(obj, indent)
    elif isinstance(obj, _Environment):
        return _format_environment(obj, indent)
    elif isinstance(obj, FileInclude):
        return _format_include(obj, indent)
    else:
        raise ValueError('cannot format object as TDL: {!r}'.format(obj))


def _format_term(term, indent):
    fmt = {
        TypeIdentifier: _format_id,
        String: _format_string,
        Regex: _format_regex,
        Coreference: _format_coref,
        AVM: _format_avm,
        ConsList: _format_conslist,
        DiffList: _format_difflist,
    }.get(term.__class__, None)

    if fmt is None:
        raise TdlError('not a valid term: {}'
                       .format(term.__class__.__name__))

    if term.docstring is not None:
        return '{}\n{}{}'.format(
            _format_docstring(term.docstring, indent),
            ' ' * indent,
            fmt(term, indent))
    else:
        return fmt(term, indent)


def _format_id(term, indent): return str(term)
def _format_string(term, indent): return '"{!s}"'.format(term)
def _format_regex(term, indent): return '^{!s}$'.format(term)
def _format_coref(term, indent): return '#{!s}'.format(term)


def _format_avm(avm, indent):
    lines = []
    for feat, val in avm.features():
        val = _format_conjunction(val, indent + len(feat) + 3)
        if not val.startswith('\n'):
            feat += ' '
        lines.append(feat + val)
    if not lines:
        return '[ ]'
    else:
        return '[ {} ]'.format((',\n' + ' ' * (indent + 2)).join(lines))


def _format_conslist(cl, indent):
    values = [_format_conjunction(val, indent + 2)  # 2 = len('< ')
              for val in cl.values()]
    end = ''
    if not cl.terminated:
        if values:
            end = ', ...'
        else:
            values = ['...']
    elif cl._avm is not None and cl[cl._last_path] is not None:
        end = ' . ' + values[-1]
        values = values[:-1]

    if not values:  # only if no values and terminated
        return '< >'
    elif (len(values) <= _max_inline_list_items and
          sum(len(v) + 2 for v in values) + 2 + indent <= _line_width):
        return '< {} >'.format(', '.join(values) + end)
    else:
        i = ' ' * (indent + 2)  # 2 = len('< ')
        lines = ['< {}'.format(values[0])]
        lines.extend(i + val for val in values[1:])
        return ',\n'.join(lines) + end + ' >'


def _format_difflist(dl, indent):
    values = [_format_conjunction(val, indent + 3)  # 3 == len('<! ')
              for val in dl.values()]
    if not values:
        return '<! !>'
    elif (len(values) <= _max_inline_list_items and
          sum(len(v) + 2 for v in values) + 4 + indent <= _line_width):
        return '<! {} !>'.format(', '.join(values))
    else:
        # i = ' ' * (indent + 3)  # 3 == len('<! ')
        return '<! {} !>'.format(
            (',\n' + ' ' * (indent + 3)).join(values))
        #     values[0])]
        # lines.extend(i + val for val in values[1:])
        # return ',\n'.join(lines) + ' !>'


def _format_conjunction(conj, indent):
    if isinstance(conj, Term):
        return _format_term(conj, indent)
    elif len(conj._terms) == 0:
        return ''
    else:
        tokens = []
        width = indent
        for term in conj._terms:
            tok = _format_term(term, width)
            flen = max(len(s) for s in tok.splitlines())
            width += flen + 3  # 3 == len(' & ')
            tokens.append(tok)
        lines = [tokens]  # all terms joined without newlines (for now)
        return (' &\n' + ' ' * indent).join(
            ' & '.join(line) for line in lines if line)


def _format_typedef(td, indent):
    i = ' ' * indent
    if hasattr(td, 'affix_type'):
        patterns = ' '.join('({} {})'.format(a, b) for a, b in td.patterns)
        body = _format_typedef_body(td, indent, indent + 2)
        return '{}{} {}\n%{} {}\n  {}.'.format(
            i, td.identifier, td._operator, td.affix_type, patterns, body)
    else:
        body = _format_typedef_body(
            td, indent, indent + len(td.identifier) + 4)
        return '{}{} {} {}.'.format(i, td.identifier, td._operator, body)


def _format_typedef_body(td, indent, offset):
    parts = [[]]
    for term in td.conjunction.terms:
        if isinstance(term, AVM) and len(parts) == 1:
            parts.append([])
        parts[-1].append(term)

    if parts[0] == []:
        parts = [parts[1]]
    assert len(parts) <= 2
    if len(parts) == 1:
        formatted_conj = _format_conjunction(td.conjunction, offset)
    else:
        formatted_conj = '{} &\n{}{}'.format(
            _format_conjunction(Conjunction(parts[0]), offset),
            ' ' * (_base_indent + indent),
            _format_conjunction(Conjunction(parts[1]), _base_indent + indent))

    if td.docstring is not None:
        docstring = '\n  ' + _format_docstring(td.docstring, 2)
    else:
        docstring = ''

    return formatted_conj + docstring


def _format_docstring(doc, indent):
    if doc is None:
        return ''
    lines = textwrap.dedent(doc).splitlines()
    if lines:
        if lines[0].strip() == '':
            lines = lines[1:]
        if lines[-1].strip() == '':
            lines = lines[:-1]
    ind = ' ' * indent
    contents = _escape_docstring(
        '\n{0}{1}\n{0}'.format(ind, ('\n' + ind).join(lines)))
    return '"""{}"""'.format(contents)


def _escape_docstring(s):
    cs = []
    cnt = 0
    lastindex = len(s) - 1
    for i, c in enumerate(s):
        if cnt == -1 or c not in '"\\':
            cnt = 0
        elif c == '"':
            cnt += 1
            if cnt == 3 or i == lastindex:
                cs.append('\\')
                cnt = 0
        elif c == '\\':
            cnt = -1
        cs.append(c)
    return ''.join(cs)


def _format_morphset(obj, indent):
    mstype = 'letter-set' if isinstance(obj, LetterSet) else 'wild-card'
    return '{}%({} ({} {}))'.format(
        ' ' * indent, mstype, obj.var, obj.characters)


def _format_environment(env, indent):
    status = ''
    if isinstance(env, TypeEnvironment):
        envtype = ':type'
    elif isinstance(env, InstanceEnvironment):
        envtype = ':instance'
        if env.status:
            status = ' :status ' + env.status

    contents = '\n'.join(format(obj, indent + 2) for obj in env.entries)
    if contents:
        contents += '\n'
    return '{0}:begin {1}{2}.\n{3}{0}:end {1}.'.format(
        ' ' * indent, envtype, status, contents)

def _format_include(fi, indent):
    return '{}:include "{}".'.format(' ' * indent, fi.path)
