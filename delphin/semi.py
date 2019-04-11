
"""
Semantic Interface (SEM-I)

Semantic interfaces (SEM-Is) describe the inventory of semantic
components in a grammar, including variables, properties, roles, and
predicates. This information can be used for validating semantic
structures or for filling out missing information in incomplete
representations.

.. seealso::
  - Wiki on SEM-I: http://moin.delph-in.net/SemiRfc

"""

import re
from os.path import dirname, join as pjoin
import warnings

from delphin.tfs import TypeHierarchy
from delphin.exceptions import (
    PyDelphinException,
    PyDelphinWarning
)


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
    r'(?P<role>[^ ]+) (?P<value>[^ ,.{\]]+)'
    r'(?:\s*\{\s*(?P<properties>[^ ]+ [^ ,}]+(?:, [^ ]+ [^ ,}]+)*)\s*\})?'
    r'(?(optional)\s*\])'
    r'(?:\s*(?:,\s*|$))',
    re.U
)


class SemIError(PyDelphinException):
    """
    Raised when loading an invalid SEM-I.
    """


class SemIWarning(PyDelphinWarning):
    """
    Warning class for questionable SEM-Is.
    """


def load(fn, encoding='utf-8'):
    """
    Read the SEM-I beginning at the filename *fn* and return the SemI.

    Args:
        fn: the filename of the top file for the SEM-I. Note: this must
            be a filename and not a file-like object.
        encoding (str): the character encoding of the file
    Returns:
        The SemI defined by *fn*
    """
    data = _read_file(fn, dirname(fn), encoding)
    return SemI(**data)


def _read_file(fn, basedir, encoding):
    data = {
        'variables': [],
        'properties': [],
        'roles': [],
        'predicates': {},
    }
    section = None

    for line in open(fn, 'r', encoding=encoding):
        line = line.lstrip()

        if not line or line.startswith(';'):
            continue

        match = re.match(r'(?P<name>[^: ]+):\s*$', line)
        if match is not None:
            name = match.group('name')
            if name not in _SEMI_SECTIONS:
                raise ValueError('Invalid SEM-I section: {}'.format(name))
            else:
                section = name
            continue

        match = re.match(r'include:\s*(?P<filename>.+)$', line, flags=re.U)
        if match is not None:
            include_fn = pjoin(basedir, match.group('filename').rstrip())
            include_data = _read_file(
                include_fn, dirname(include_fn), encoding)
            data['variables'].extend(include_data.get('variables', []))
            data['properties'].extend(include_data.get('properties', []))
            data['roles'].extend(include_data.get('roles', []))
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

        if section == 'variables':
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
                data['variables'].append((identifier, v))
            else:
                raise ValueError('Invalid entry: {}'.format(line))

        elif section == 'properties':
            # e.g. + < bool.
            match = _property_entry_re.match(line)
            if match is not None:
                _type = match.group('type')
                supertypes = match.group('parents') or []
                if supertypes:
                    supertypes = supertypes.split(' & ')
                data['properties'].append((_type, {'parents': supertypes}))
            else:
                raise ValueError('Invalid entry: {}'.format(line))

        elif section == 'roles':
            # e.g. + < bool.
            match = _role_entry_re.match(line)
            if match is not None:
                rargname, value = match.group('role'), match.group('value')
                data['roles'].append((rargname, {'value': value}))
            else:
                raise ValueError('Invalid entry: {}'.format(line))

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
                    data['predicates'][pred]['synopses'].append(roles)

    return data


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
        variables: mapping of variable types to property lists
        properties: set of valid property values
        roles: mapping of role names to allowed variable types
        predicates: mapping of predicate symbols to synopses
        type_hierarchy: unified :class:`~delphin.tfs.TypeHierarchy` of
            all types defined in the SEM-I
    """
    def __init__(self,
                 variables=None,
                 properties=None,
                 roles=None,
                 predicates=None):
        self.type_hierarchy = TypeHierarchy(TOP_TYPE)
        self.properties = set()
        self.variables = {}
        self.roles = {}
        self.predicates = {}
        # validate and normalize inputs
        self._init_properties(properties)
        self._init_variables(variables)
        self._init_roles(roles)
        self._init_predicates(predicates)


    def _init_properties(self, properties):
        subhier = {}
        for prop, data in dict(properties or []).items():
            prop = prop.lower()
            _add_to_subhierarchy(subhier, prop, data)
            self.properties.add(prop)
        self.type_hierarchy.update(subhier)

    def _init_variables(self, variables):
        subhier = {}
        for var, data in dict(variables or []).items():
            var = var.lower()
            _add_to_subhierarchy(subhier, var, data)
            self.variables[var] = proplist = []
            for k, v in data.get('properties', []):
                k, v = k.upper(), v.lower()
                if v not in self.properties:
                    raise SemIError('undefined property value: {}'.format(v))
                proplist.append((k, v))
        self.type_hierarchy.update(subhier)

    def _init_roles(self, roles):
        for role, data in dict(roles or []).items():
            role = role.upper()
            var = data['value'].lower()
            if not (var == STRING_TYPE or var in self.variables):
                raise SemIError('undefined variable type: {}'.format(var))
            self.roles[role] = var

    def _init_predicates(self, predicates):
        subhier = {}
        propcache = {var: dict(props) for var, props in self.variables.items()}
        for pred, data in dict(predicates or []).items():
            pred = pred.lower()
            _add_to_subhierarchy(subhier, pred, data)
            synopses = []
            for synopsis_data in data['synopses']:
                synopses.append(
                    self._init_synopsis(pred, synopsis_data, propcache))
            self.predicates[pred] = synopses
        self.type_hierarchy.update(subhier)

    def _init_synopsis(self, pred, synopsis_data, propcache):
        synopsis = []
        for d in synopsis_data:
            role = d['role'].upper()
            value = d['value'].lower()
            proplist = []
            if role not in self.roles:
                raise SemIError('{}: undefined role: {}'.format(pred, role))
            if value == STRING_TYPE:
                if d.get('properties', False):
                    raise SemIError('{}: strings cannot define properties'
                                    .format(pred))
            elif value not in self.variables:
                raise SemIError('{}: undefined variable type: {}'
                                .format(pred, value))
            else:
                props = {}
                for k, v in dict(d.get('properties', [])).items():
                    k, v = k.upper(), v.lower()
                    if v not in self.properties:
                        raise SemIError(
                            '{}: undefined property value: {}'
                            .format(pred, v))
                    if k not in propcache[value]:
                        # Just warn because of the current situation where
                        # 'i' variables are used for unexpressed 'x's
                        warnings.warn(
                            "{}: property '{}' not allowed on '{}'"
                            .format(pred, k, value),
                            SemIWarning)
                    else:
                        _v = propcache[value][k]
                        if not self.type_hierarchy.compatible(v, _v):
                            raise SemIError(
                                '{}: incompatible property values: {}, {}'
                                .format(pred, v, _v))
                    props[k] = v
            synopsis.append((role, value, props, d.get('optional', False)))
        return synopsis

    @classmethod
    def from_dict(cls, d):
        """Instantiate a SemI from a dictionary representation."""
        return cls(**d)

    def to_dict(self):
        """Return a dictionary representation of the SemI."""
        hier = self.type_hierarchy
        def parents(x):
            ps = hier[x]
            if ps == [TOP_TYPE]:
                return []
            return ps
        variables = {var: {'parents': parents(var),
                           'properties': [[k, v] for k, v in props]}
                     for var, props in self.variables.items()}
        properties = {prop: {'parents': parents(prop)}
                      for prop in self.properties}
        roles = {role: {'value': value} for role, value in self.roles.items()}
        predicates = {}
        _synopsis_fields = 'role value properties optional'.split()
        for pred, synopses in self.predicates.items():
            synopses = [[dict(zip(_synopsis_fields, d)) for d in synopsis]
                        for synopsis in synopses]
            predicates[pred] = {'parents': parents(pred), 'synopses': synopses}
        return {'variables': variables,
                'properties': properties,
                'roles': roles,
                'predicates': predicates}

    def subsumes(self, a, b):
        """
        Return True if *a* subsumes *b* in the type hierarchy.

        Type names *a* and *b* are case-normalized before checking the
        type hierarchy.

        Example:
            >>> smi.subsumes('existential_q', '_a_q')
            True
            >>> smi.subsumes('+', 'bool')
            False
        """
        return self.type_hierarchy.subsumes(a.lower(), b.lower())

    def compatible(self, a, b):
        """
        Return True if *a* is compatible with *b* in the type hierarchy.

        Type names *a* and *b* are case-normalized before checking the
        type hierarchy.

        Example:
            >>> smi.compatible('+', 'bool')
            True
            >>> smi.compatible('i', 'p')
            True
            >>> smi.compatible('past', 'pres')
            False
        """
        return self.type_hierarchy.compatible(a.lower(), b.lower())

    def find_synopsis(self, predicate, roles=None, variables=None):
        """
        Return the first matching synopsis for *predicate*.

        Synopses can be matched by a set of roles or an ordered list
        of variable types. If no condition is given, the first synopsis
        is returned.

        Args:
            predicate: predicate symbol whose synopsis will be returned
            roles: roles that all must be used in the synopsis
            variables: list of variable types (in order) that all must
                be used by roles in the synopsis
        Returns:
            matching synopsis as a `(role, value, properties, optional)`
            tuple
        Raises:
            :class:`SemIError`: if *predicate* is undefined or if no
                matching synopsis can be found
        Example:
            >>> smi.find_synopsis('_write_v_to')
            [('ARG0', 'e', [], False), ('ARG1', 'i', [], False),
             ('ARG2', 'p', [], True), ('ARG3', 'h', [], True)]
            >>> smi.find_synopsis('_write_v_to', variables='eii')
            [('ARG0', 'e', [], False), ('ARG1', 'i', [], False),
             ('ARG2', 'i', [], False)]
        """
        if predicate not in self.predicates:
            raise SemIError('undefined predicate: {}'.format(predicate))
        if roles is not None:
            roles = set(role.upper() for role in roles)
        if variables is not None:
            variables = [var.lower() for var in variables]
        found = False
        for synopsis in self.predicates[predicate]:
            if roles is not None and roles != set(d[0] for d in synopsis):
                continue
            if (variables is not None and (
                    len(synopsis) != len(variables) or
                    not all(self.subsumes(d[1], t)
                            for d, t in zip(synopsis, variables)))):
                continue
            found = synopsis
            break
        if found is False:
            raise SemIError('no valid synopsis for {}({})'
                            .format(predicate, ', '.join(variables)))
        return found


def _add_to_subhierarchy(subhier, typename, data):
    if data['parents']:
        parents = [parent.lower() for parent in data['parents']]
    else:
        parents = [TOP_TYPE]
    subhier[typename] = parents
