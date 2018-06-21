
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
from collections import namedtuple

_SEMI_SECTIONS = (
    'variables',
    'properties',
    'roles',
    'predicates',
)

_variable_entry_re = re.compile(
    r'(?P<var>[^ <:.]+)'
    r'(?: < (?P<supertypes>[^ &:.]+(?: & [^ &:.]+)*))?'
    r'(?: : (?P<properties>[^ ]+ [^ ,.]+(?:, [^ ]+ [^ ,.]+)*))?'
    r'\s*\.\s*$',
    re.U
)

_property_entry_re = re.compile(
    r'(?P<type>[^ <.]+)'
    r'(?: < (?P<supertypes>[^ &.]+(?: & [^ &.]+)*))?'
    r'\s*\.\s*$',
    re.U
)

_role_entry_re = re.compile(
    r'(?P<role>[^ :]+) : (?P<value>[^ .]+)\s*\.\s*$',
    re.U
)

_predicate_entry_re = re.compile(
    r'(?P<pred>[^ <:.]+)'
    r'(?: < (?P<supertypes>[^ &:.]+(?: & [^ &:.]+)*))?'
    r'(?: : (?P<synposis>.*[^ .]))?'
    r'\s*\.\s*$',
    re.U
)

_synopsis_re = re.compile(
    r'\s*(?P<opt>\[\s*)?'
    r'(?P<role>[^ ]+) (?P<value>[^ ,.{\]]+)'
    r'(?:\s*\{\s*(?P<properties>[^ ]+ [^ ,}]+(?:, [^ ]+ [^ ,}]+)*)\s*\})?'
    r'(?(opt)\s*\])'
    r'(?:\s*(?P<end>,|$)\s*)',
    re.U
)

TOP = '*top*'


class Variable(namedtuple('Variable', ('type', 'supertypes', 'proplist'))):
    """An MRS variable description."""

    @property
    def properties(self):
        """Properties constrained by the Variable."""
        return dict(self.proplist)

    @classmethod
    def from_dict(cls, d):
        """Instantiate a Variable from a dictionary representation."""
        return cls(
            d['type'], tuple(d['parents']), list(d['properties'].items())
        )

    def to_dict(self):
        """Return a dictionary representation of the Variable."""
        return {
            'type': self.type,
            'parents': list(self.supertypes),
            'properties': self.properties
        }


class Role(namedtuple('Role', ('rargname', 'value', 'proplist', 'optional'))):
    """An MRS role description."""

    def __new__(cls, rargname, value, proplist=None, optional=False):
        if proplist is None: proplist = []
        return super(Role, cls).__new__(
            cls, rargname, value, proplist, optional
        )

    @property
    def properties(self):
        """Properties constrained by the Role."""
        return dict(self.proplist)

    @classmethod
    def from_dict(cls, d):
        """Instantiate a Role from a dictionary representation."""
        return cls(
            d['rargname'],
            d['value'],
            list(d.get('properties', {}).items()),
            d.get('optional', False)
        )

    def to_dict(self):
        """Return a dictionary representation of the Role."""
        d = {'rargname': self.rargname, 'value': self.value}
        if self.properties:
            d['properties'] = self.properties
        if self.optional:
            d['optional'] = self.optional
        return d


class Property(namedtuple('Property', ('type', 'supertypes'))):
    """An MRS morphosemantic property description."""

    @classmethod
    def from_dict(cls, d):
        """Instantiate a Property from a dictionary representation."""
        return cls(d['type'], tuple(d['parents']))

    def to_dict(self):
        """Return a dictionary representation of the Property."""
        return {'type': self.type, 'parents': list(self.supertypes)}


class Predicate(namedtuple('Predicate',
                           ('predicate', 'supertypes', 'synopses'))):
    """An MRS predicate description."""

    @classmethod
    def from_dict(cls, d):
        """Instantiate a Predicate from a dictionary representation."""
        synopses = [tuple(map(Role.from_dict, synopsis))
                    for synopsis in d.get('synopses', [])]
        return cls(d['predicate'], tuple(d['parents']), synopses)

    def to_dict(self):
        """Return a dictionary representation of the Predicate."""
        return {
            'predicate': self.predicate,
            'parents': list(self.supertypes),
            'synopses': [[role.to_dict() for role in synopsis]
                         for synopsis in self.synopses]
        }

# TOP = type('*top*', tuple(), {})
# _var_dict = {
#     'supertypes': lambda self: self.__bases__,
# }

def load(fn):
    """
    Read the SEM-I beginning at the filename *fn* and return the SemI.

    Args:
        fn: the filename of the top file for the SEM-I. Note: this must
            be a filename and not a file-like object.
    Returns:
        The SemI defined by *fn*
    """
    data = _load_file(fn)
    return SemI(**data)

def _load_file(fn):
    data = _read_file(fn, dirname(fn))
    data['predicates'] = [
        (pred, Predicate(pred, tuple(d['supertypes']), d['synopses']))
        for pred, d in data['predicates'].items()
    ]
    return data

def _read_file(fn, basedir):
    data = {
        'variables': [],
        'properties': [],
        'roles': [],
        'predicates': {},
    }
    section = None

    for line in open(fn, 'r'):
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
            include_data = _read_file(include_fn, dirname(include_fn))
            data['variables'].extend(include_data.get('variables', []))
            data['properties'].extend(include_data.get('properties', []))
            data['roles'].extend(include_data.get('roles', []))
            for pred, d in include_data['predicates'].items():
                if pred not in data['predicates']:
                    data['predicates'][pred] = {
                        'supertypes': [],
                        'synopses': []
                    }
                if d.get('supertypes'):
                    data['predicates'][pred]['supertypes'] = d['supertypes']
                if d.get('synopses'):
                    data['predicates'][pred]['synopses'].extend(d['synopses'])

        if section == 'variables':
            # e.g. e < i : PERF bool, TENSE tense.
            match = _variable_entry_re.match(line)
            if match is not None:
                identifier = match.group('var')
                supertypes = match.group('supertypes') or tuple()
                if supertypes:
                    supertypes = tuple(supertypes.split(' & '))
                properties = match.group('properties') or []
                if properties:
                    pairs = properties.split(', ')
                    properties = [tuple(pair.split()) for pair in pairs]
                v = Variable(identifier, supertypes, properties)
                # v = type(identifier, supertypes, d)
                data['variables'].append((identifier, v))
            else:
                raise ValueError('Invalid entry: {}'.format(line))

        elif section == 'properties':
            # e.g. + < bool.
            match = _property_entry_re.match(line)
            if match is not None:
                _type = match.group('type')
                supertypes = match.group('supertypes') or tuple()
                if supertypes:
                    supertypes = tuple(supertypes.split(' & '))
                p = Property(_type, supertypes)
                data['properties'].append((_type, p))
            else:
                raise ValueError('Invalid entry: {}'.format(line))

        elif section == 'roles':
            # e.g. + < bool.
            match = _role_entry_re.match(line)
            if match is not None:
                rargname, value = match.group('role'), match.group('value')
                r = Role(rargname, value)
                data['roles'].append((rargname, r))
            else:
                raise ValueError('Invalid entry: {}'.format(line))

        elif section == 'predicates':
            # e.g. _predicate_n_1 : ARG0 x { IND + }.
            match = _predicate_entry_re.match(line)
            if match is not None:
                pred = match.group('pred')
                if pred not in data['predicates']:
                    data['predicates'][pred] = {
                        'supertypes': [],
                        'synopses': []
                    }
                sups = match.group('supertypes')
                if sups:
                    data['predicates'][pred]['supertypes'] = sups.split(' & ')
                synposis = match.group('synposis')
                roles = []
                if synposis:
                    for rolematch in _synopsis_re.finditer(synposis):
                        d = rolematch.groupdict()
                        rprops = d['properties'] or []
                        if rprops:
                            pairs = rprops.split(', ')
                            rprops = [tuple(pair.split()) for pair in pairs]
                        roles.append(
                            Role(d['role'], d['value'], rprops, bool(d['opt']))
                        )
                    data['predicates'][pred]['synopses'].append(tuple(roles))

    return data

class SemI(object):
    """
    A semantic interface.

    SEM-Is describe the semantic inventory for a grammar. These include
    the variable types, valid properties for variables, valid roles
    for predications, and a lexicon of predicates with associated roles.

    Args:
        variables: a mapping of (var, Variable)
        properties: a mapping of (prop, Property)
        roles: a mapping of (role, Role)
        predicates: a mapping of (pred, Predicate)
    """
    def __init__(self,
                 variables=None,
                 properties=None,
                 roles=None,
                 predicates=None):
        self.variables = dict(variables) if variables is not None else {}
        self.properties = dict(properties) if properties is not None else {}
        self.roles = dict(roles) if roles is not None else {}
        self.predicates = dict(predicates) if predicates is not None else {}

    @classmethod
    def from_dict(cls, d):
        """Instantiate a SemI from a dictionary representation."""
        read = lambda cls: (lambda pair: (pair[0], cls.from_dict(pair[1])))
        return cls(
            variables=map(read(Variable), d.get('variables', {}).items()),
            properties=map(read(Property), d.get('properties', {}).items()),
            roles=map(read(Role), d.get('roles', {}).items()),
            predicates=map(read(Predicate), d.get('predicates', {}).items())
        )

    def to_dict(self):
        """Return a dictionary representation of the SemI."""
        make = lambda pair: (pair[0], pair[1].to_dict())
        return dict(
            variables=dict(make(v) for v in self.variables.items()),
            properties=dict(make(p) for p in self.properties.items()),
            roles=dict(make(r) for r in self.roles.items()),
            predicates=dict(make(p) for p in self.predicates.items())
        )
