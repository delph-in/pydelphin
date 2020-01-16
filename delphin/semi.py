
"""
Semantic Interface (SEM-I)
"""

import re
from pathlib import Path
from operator import itemgetter
import warnings
from collections import abc
from itertools import zip_longest

from delphin.predicate import normalize as normalize_predicate
from delphin import hierarchy
from delphin.exceptions import (
    PyDelphinException,
    PyDelphinSyntaxError,
    PyDelphinWarning
)
# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401


TOP_TYPE = '*top*'
STRING_TYPE = 'string'


_SEMI_SECTIONS = (
    'variables',
    'properties',
    'roles',
    'predicates',
)

_variable_entry_re = re.compile(
    r'(?P<var>[^ .]+)'
    r'(?: < (?P<parents>[^ &:.]+(?: & [^ &:.]+)*))?'
    r'(?: : (?P<properties>[^ ]+ [^ ,.]+(?:, [^ ]+ [^ ,.]+)*))?'
    r'\s*\.\s*(?:;.*)?$',
    re.U
)

_property_entry_re = re.compile(
    r'(?P<type>[^ .]+)'
    r'(?: < (?P<parents>[^ &.]+(?: & [^ &.]+)*))?'
    r'\s*\.\s*(?:;.*)?$',
    re.U
)

_role_entry_re = re.compile(
    r'(?P<role>[^ ]+) : (?P<value>[^ .]+)\s*\.\s*(?:;.*)?$',
    re.U
)

_predicate_entry_re = re.compile(
    r'(?P<pred>[^ ]+)'
    r'(?: < (?P<parents>[^ &:.;]+(?: & [^ &:.;]+)*))?'
    r'(?: : (?P<synposis>.*[^ .;]))?'
    r'\s*\.\s*(?:;.*)?$',
    re.U
)

_synopsis_re = re.compile(
    r'\s*(?P<optional>\[\s*)?'
    r'(?P<name>[^ ]+) (?P<value>[^ ,.{\]]+)'
    r'(?:\s*\{\s*(?P<properties>[^ ]+ [^ ,}]+(?:, [^ ]+ [^ ,}]+)*)\s*\})?'
    r'(?(optional)\s*\])'
    r'(?:\s*(?:,\s*|$))',
    re.U
)


class SemIError(PyDelphinException):
    """Raised when loading an invalid SEM-I."""


class SemISyntaxError(PyDelphinSyntaxError):
    """Raised when loading an invalid SEM-I."""


class SemIWarning(PyDelphinWarning):
    """Warning class for questionable SEM-Is."""


def load(source, encoding='utf-8'):
    """
    Interpret and return the SEM-I defined at path *source*.

    Args:
        source: the path of the top file for the SEM-I. Note: this
            must be a path and not an open file.
        encoding (str): the character encoding of the file
    Returns:
        The SemI defined by *source*
    """
    path = Path(source).expanduser()
    data = _read_file(path, path.parent, encoding)
    return SemI(**data)


def _read_file(path, basedir, encoding):
    data = {
        'variables': {},
        'properties': {},
        'roles': {},
        'predicates': {},
    }
    section = None

    for lineno, line in enumerate(path.open(encoding=encoding), 1):
        line = line.lstrip()

        if not line or line.startswith(';'):
            continue

        match = re.match(r'(?P<name>[^: ]+):\s*$', line)
        if match is not None:
            name = match.group('name')
            if name not in _SEMI_SECTIONS:
                raise SemISyntaxError(
                    'invalid SEM-I section',
                    filename=str(path), lineno=lineno, text=line)
            else:
                section = name
            continue

        match = re.match(r'include:\s*(?P<filename>.+)$', line, flags=re.U)
        if match is not None:
            include = basedir.joinpath(match.group('filename').rstrip())
            include_data = _read_file(
                include, include.parent, encoding)
            for key, val in include_data['variables'].items():
                _incorporate(data['variables'], key, val, include)
            for key, val in include_data['properties'].items():
                _incorporate(data['properties'], key, val, include)
            for key, val in include_data['roles'].items():
                _incorporate(data['roles'], key, val, include)
            for pred, d in include_data['predicates'].items():
                if pred not in data['predicates']:
                    data['predicates'][pred] = {
                        'parents': [],
                        'synopses': []
                    }
                if d.get('parents'):
                    data['predicates'][pred]['parents'] = d['parents']
                if d.get('synopses'):
                    data['predicates'][pred]['synopses'].extend(d['synopses'])

        elif section == 'variables':
            # e.g. e < i : PERF bool, TENSE tense.
            match = _variable_entry_re.match(line)
            if match is not None:
                identifier = match.group('var')
                supertypes = match.group('parents') or []
                if supertypes:
                    supertypes = supertypes.split(' & ')
                properties = match.group('properties') or []
                if properties:
                    pairs = properties.split(', ')
                    properties = [pair.split() for pair in pairs]
                v = {'parents': supertypes, 'properties': properties}
                # v = type(identifier, supertypes, d)
                _incorporate(data['variables'], identifier, v, path)
            else:
                raise SemISyntaxError(
                    'invalid variable',
                    filename=str(path), lineno=lineno, text=line)

        elif section == 'properties':
            # e.g. + < bool.
            match = _property_entry_re.match(line)
            if match is not None:
                _type = match.group('type')
                supertypes = match.group('parents') or []
                if supertypes:
                    supertypes = supertypes.split(' & ')
                _incorporate(
                    data['properties'], _type, {'parents': supertypes}, path)
            else:
                raise SemISyntaxError(
                    'invalid property',
                    filename=str(path), lineno=lineno, text=line)

        elif section == 'roles':
            # e.g. + < bool.
            match = _role_entry_re.match(line)
            if match is not None:
                role, value = match.group('role'), match.group('value')
                _incorporate(data['roles'], role, {'value': value}, path)
            else:
                raise SemISyntaxError(
                    'invalid role',
                    filename=str(path), lineno=lineno, text=line)

        elif section == 'predicates':
            # e.g. _predicate_n_1 : ARG0 x { IND + }.
            match = _predicate_entry_re.match(line)
            if match is not None:
                pred = match.group('pred')
                if pred not in data['predicates']:
                    data['predicates'][pred] = {
                        'parents': [],
                        'synopses': []
                    }
                sups = match.group('parents')
                if sups:
                    data['predicates'][pred]['parents'] = sups.split(' & ')
                synposis = match.group('synposis')
                roles = []
                if synposis:
                    for rolematch in _synopsis_re.finditer(synposis):
                        d = rolematch.groupdict()
                        propstr = d['properties'] or ''
                        d['properties'] = dict(
                            pair.split() for pair in propstr.split(', ')
                            if pair.strip() != '')
                        d['optional'] = bool(d['optional'])
                        roles.append(d)
                    data['predicates'][pred]['synopses'].append(
                        {'roles': roles})

    return data


def _incorporate(d, key, val, path):
    if key in d:
        warnings.warn(f"'{key}' redefined in {path}", SemIWarning)
    d[key] = val


class SynopsisRole(tuple):
    """
    Role data associated with a SEM-I predicate synopsis.

    Args:
        name (str): the role name
        value (str): the role value (variable type or `"string"`)
        properties (dict): properties associated with the role's value
        optional (bool): a flag indicating if the role is optional
    Example:

    >>> role = SynopsisRole('ARG0', 'x', {'PERS': '3'}, False)
    """

    name = property(itemgetter(0), doc='The role name.')
    value = property(
        itemgetter(1), doc='The role value (variable type or "string"')
    properties = property(itemgetter(2), doc='Property-value map.')
    optional = property(itemgetter(3), doc="`True` if the role is optional.")

    def __new__(cls, name, value, properties=None, optional=False):
        if not properties:
            properties = {}
        else:
            properties = {prop.upper(): val.lower()
                          for prop, val in dict(properties).items()}
        return super().__new__(cls, ([name.upper(),
                                      value.lower(),
                                      properties,
                                      bool(optional)]))

    def __repr__(self):
        return 'SynopsisRole({}, {}, {}, {})'.format(
            self.name, self.value, self.properties, self.optional)

    def _to_dict(self):
        d = {"name": self.name, "value": self.value}
        if self.properties:
            d['properties'] = dict(self.properties)
        if self.optional:
            d['optional'] = True
        return d

    @classmethod
    def _from_dict(cls, d):
        return cls(d['name'],
                   d['value'],
                   d.get('properties', []),
                   d.get('optional', False))


class Synopsis(tuple):
    """
    A SEM-I predicate synopsis.

    A synopsis describes the roles of a predicate in a semantic
    structure, so it is no more than a tuple of roles as
    :class:`SynopsisRole` objects. The length of the synopsis is thus
    the arity of a predicate while the individual role items detail
    the role names, argument types, associated properties, and
    optionality.
    """

    def __repr__(self):
        return 'Synopsis([{}])'.format(', '.join(map(repr, self)))

    @classmethod
    def from_dict(cls, d):
        """
        Create a Synopsis from its dictionary representation.

        Example:

        >>> synopsis = Synopsis.from_dict({
        ...     'roles': [
        ...         {'name': 'ARG0', 'value': 'e'},
        ...         {'name': 'ARG1', 'value': 'x',
        ...          'properties': {'NUM': 'sg'}}
        ...     ]
        ... })
        ...
        >>> len(synopsis)
        2
        """
        return cls(SynopsisRole._from_dict(role)
                   for role in d.get('roles', []))

    def to_dict(self):
        """
        Return a dictionary representation of the Synopsis.

        Example:

        >>> Synopsis([
        ...     SynopsisRole('ARG0', 'e'),
        ...     SynopsisRole('ARG1', 'x', {'NUM': 'sg'})
        ... ]).to_dict()
        {'roles': [{'name': 'ARG0', 'value': 'e'},
                   {'name': 'ARG1', 'value': 'x',
                    'properties': {'NUM': 'sg'}}]}
        """

        return {'roles': [role._to_dict() for role in self]}

    def subsumes(self, args, variables=None):
        """
        Return `True` if the Synopsis subsumes *args*.

        The *args* argument is a description of MRS arguments. It may
        take two different forms:

        - a sequence (e.g., string or list) of variable types, e.g.,
          `"exh"`, which must be subsumed by the role values of the
          synopsis in order

        - a mapping (e.g., a dict) of roles to variable types which
          must match roles in the synopsis; the variable type may be
          `None` which matches any role value

        In both cases, the sequence or mapping must be a subset of the
        roles of the synopsis, and any missing must be optional roles,
        otherwise the synopsis does not subsume *args*.

        The *variables* argument is a variable hierarchy. If it is
        `None`, variables will be checked for strict equality.
        """
        if len(args) > len(self):
            return False  # some arg won't be in the synopsis
        # normalize input
        if isinstance(args, abc.Sequence):
            vartypes = (v.lower() if v else None for v in args)
            roleargs = list(zip_longest([], vartypes, self))
        elif isinstance(args, abc.Mapping):
            name_to_roles = {d.name: d for d in self}
            roleargs = []
            for role in set(args).union(name_to_roles):
                role = role.upper()
                v = args.get(role, '')
                v = v.lower() if v else None
                roleargs.append((role, v, name_to_roles.get(role)))
        else:
            raise TypeError(args.__class__.__name__)

        # per-role checks
        for role, arg, synrole in roleargs:
            if synrole is None:
                return False  # unmatched role in args
            elif role is None and arg is None and not synrole.optional:
                return False  # unmatched synopsis role
            # elif role is not None and role != synrole.name:
            #     return False  # invalid role in sequence
            elif arg is not None:
                if variables is not None:
                    if not variables.subsumes(synrole.value, arg):
                        return False
                elif synrole.value != arg:
                    return False
        # all tests passed
        return True


class SemI(object):
    """
    A semantic interface.

    SEM-Is describe the semantic inventory for a grammar. These include
    the variable types, valid properties for variables, valid roles
    for predications, and a lexicon of predicates with associated roles.

    Args:
        variables: a mapping of (var, {'parents': [...], 'properties': [...]})
        properties: a mapping of (prop, {'parents': [...]})
        roles: a mapping of (role, {'value': ...})
        predicates: a mapping of (pred, {'parents': [...], 'synopses': [...]})
    Attributes:
        variables: a :class:`~delphin.hierarchy.MultiHierarchy` of variables;
            node data contains the property lists
        properties: a :class:`~delphin.hierarchy.MultiHierarchy` of properties
        roles: mapping of role names to allowed variable types
        predicates: a :class:`~delphin.hierarchy.MultiHierarchy` of predicates;
            node data contains lists of synopses
    """

    def __init__(self,
                 variables=None,
                 properties=None,
                 roles=None,
                 predicates=None):
        self.properties = _new_hierarchy()
        self.variables = _new_hierarchy()
        self.roles = {}
        self.predicates = _new_hierarchy()
        # validate and normalize inputs
        if properties:
            self._init_properties(properties)
        if variables:
            self._init_variables(variables)
        if roles:
            self._init_roles(roles)
        if predicates:
            self._init_predicates(predicates)

    def _init_properties(self, properties):
        subhier = {prop: data.get('parents') or TOP_TYPE
                   for prop, data in properties.items()}
        self.properties.update(subhierarchy=subhier)

    def _init_variables(self, variables):
        subhier, data = {}, {}
        for var, var_data in variables.items():
            properties = []
            for k, v in var_data.get('properties', []):
                k, v = k.upper(), v.lower()
                if v not in self.properties:
                    raise SemIError(f'undefined property value: {v}')
                properties.append((k, v))
            subhier[var] = var_data.get('parents') or TOP_TYPE
            data[var] = properties
        self.variables.update(subhierarchy=subhier, data=data)

    def _init_roles(self, roles):
        for role, data in roles.items():
            role = role.upper()
            var = data['value'].lower()
            if not (var == STRING_TYPE or var in self.variables):
                raise SemIError(f'undefined variable type: {var}')
            self.roles[role] = var

    def _init_predicates(self, predicates):
        subhier, data = {}, {}
        propcache = {v: dict(props or [])
                     for v, props in self.variables.items()}
        for pred, pred_data in predicates.items():
            synopses = []
            for synopsis_data in pred_data.get('synopses', []):
                synopses.append(
                    self._init_synopsis(pred, synopsis_data, propcache))
            subhier[pred] = pred_data.get('parents') or TOP_TYPE
            data[pred] = synopses
        self.predicates.update(subhierarchy=subhier, data=data)

    def _init_synopsis(self, pred, synopsis_data, propcache):
        synopsis = Synopsis.from_dict(synopsis_data)
        for role in synopsis:
            if role.name not in self.roles:
                raise SemIError(f'{pred}: undefined role: {role.name}')
            if role.value == STRING_TYPE:
                if role.properties:
                    raise SemIError(
                        f'{pred}: strings cannot define properties')
            elif role.value not in self.variables:
                raise SemIError(
                    f'{pred}: undefined variable type: {role.value}')
            else:
                for k, v in role.properties.items():
                    if v not in self.properties:
                        raise SemIError(
                            f'{pred}: undefined property value: {v}')
                    if k not in propcache[role.value]:
                        # Just warn because of the current situation where
                        # 'i' variables are used for unexpressed 'x's
                        warnings.warn(
                            "{}: property '{}' not allowed on '{}'"
                            .format(pred, k, role.value),
                            SemIWarning)
                    else:
                        _v = propcache[role.value][k]
                        if not self.properties.compatible(v, _v):
                            raise SemIError(
                                '{}: incompatible property values: {}, {}'
                                .format(pred, v, _v))
        return synopsis

    @classmethod
    def from_dict(cls, d):
        """Instantiate a SemI from a dictionary representation."""
        return cls(**d)

    def to_dict(self):
        """Return a dictionary representation of the SemI."""

        def add_parents(d, ps):
            if ps and list(ps) != [TOP_TYPE]:
                d['parents'] = list(ps)

        variables = {}
        for var, data in self.variables.items():
            variables[var] = d = {}
            add_parents(d, self.variables.parents(var))
            if data:
                d['properties'] = list(map(list, data))

        properties = {}
        for prop in self.properties:
            properties[prop] = d = {}
            add_parents(d, self.properties.parents(prop))

        roles = {role: {'value': value} for role, value in self.roles.items()}

        predicates = {}
        for pred, data in self.predicates.items():
            predicates[pred] = d = {}
            add_parents(d, self.predicates.parents(pred))
            if data:
                d['synopses'] = [synopsis.to_dict() for synopsis in data]

        return {'variables': variables,
                'properties': properties,
                'roles': roles,
                'predicates': predicates}

    def find_synopsis(self, predicate, args=None):
        """
        Return the first matching synopsis for *predicate*.

        *predicate* will be normalized before lookup.

        Synopses can be matched by a description of arguments which is
        tested with :meth:`Synopsis.subsumes`. If no condition is
        given, the first synopsis is returned.

        Args:
            predicate: predicate symbol whose synopsis will be returned
            args: description of arguments that must be subsumable by
                the synopsis
        Returns:
            matching synopsis as a list of `(role, value, properties,
            optional)` role tuples
        Raises:
            :class:`SemIError`: if *predicate* is undefined or if no
                matching synopsis can be found
        Example:
            >>> smi.find_synopsis('_write_v_to')
            [('ARG0', 'e', [], False), ('ARG1', 'i', [], False),
             ('ARG2', 'p', [], True), ('ARG3', 'h', [], True)]
            >>> smi.find_synopsis('_write_v_to', args='eii')
            [('ARG0', 'e', [], False), ('ARG1', 'i', [], False),
             ('ARG2', 'i', [], False)]
        """

        predicate = normalize_predicate(predicate)
        if predicate not in self.predicates:
            raise SemIError(f'undefined predicate: {predicate}')
        found = False
        for synopsis in self.predicates[predicate]:
            if not args or synopsis.subsumes(args, self.variables):
                found = synopsis
                break
        if found is False:
            raise SemIError('no valid synopsis for {}({})'
                            .format(predicate, repr(args) if args else ''))
        return found


def _new_hierarchy():
    return hierarchy.MultiHierarchy(TOP_TYPE, normalize_identifier=str.lower)
