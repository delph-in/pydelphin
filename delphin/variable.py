# -*- coding: utf-8 -*-

"""
Functions for working with MRS variables.

This module contains functions to inspect the type and identifier of
variables (:func:`split`, :func:`sort`, :func:`id`) and check if a
variable string is well-formed (:func:`is_valid`). It additionally has
constants for the standard variable types (:data:`UNKNOWN`,
:data:`INDIVIDUAL`, :data:`INSTANCE_OR_HANDLE`, :data:`EVENTUALITY`,
:data:`INSTANCE`, and :data:`HANDLE`) and hierarchy
(:data:`hierarchy`). Finally, the :class:`VariableFactory` class may
be useful for tasks like DMRS to MRS conversion for managing the
creation of new variables.

Variables in MRS
----------------

Variables are a concept in Minimal Recursion Semantics coming from
formal semantics. Consider this logical form for a sentence like
"the dog barks"::

    ∃x(dog(x) ^ bark(x))

Here *x* is a variable that represents an entity that has the
properties that it is a dog and it is barking. Davidsonian semantics
introduce variables for events as well::

    ∃e∃x(dog(x) ^ bark(e, x))

MRS uses variables in a similar way to Davidsonian semantics, except
that events are not explicitly quantified. That might look like the
following (if we ignore quantifier scope underspecification)::

    the(x4) [dog(x4)] {bark(e2, x4)}

"Variables" are also used for scope handles and labels, as in this
minor modification that indicates the scope handles::

    h3:the(x4) [h6:dog(x4)] {h1:bark(e2, x4)}

There is some confusion of terminology here. Sometimes "variable" is
contrasted with "handle" to mean an instance (`x`) or eventuality
(`e`) variable, but in this module "variable" means the identifiers
used for instances, eventualities, handles, and their supertypes.

The form of MRS variables is the concatenation of a variable *type*
(also called a *sort*) with a variable *id*. For example, the variable
type `e` and id `2` form the variable `e2`. Generally in MRS the
variable ids, regardless of the type, are unique, so for instance one
would not see `x2` and `e2` in the same structure.
"""

import re

from delphin import tfs

### Default variable types

hierarchy = tfs.TypeHierarchy(
    '*top*',
    {'u': '*top*',
     'i': 'u',
     'p': 'u',
     'h': 'p',
     'e': 'i',
     'x': ('i', 'p')})

UNKNOWN            = 'u' # also 'unspecific' or 'unbound'
INDIVIDUAL         = 'i'
INSTANCE_OR_HANDLE = 'p'
EVENTUALITY        = 'e'
INSTANCE           = 'x'
HANDLE             = 'h'

### Functions

variable_re = re.compile(r'^([-\w]*[^\s\d])(\d+)$')


def split(var):
    """
    Split a valid variable string into its variable sort and id.

    Examples:
        >>> variable.split('h3')
        ('h', '3')
        >>> variable.split('ref-ind12')
        ('ref-ind', '12')
    """
    match = variable_re.match(var)
    if match is None:
        raise ValueError('Invalid variable string: {}'.format(str(var)))
    else:
        return match.groups()


def sort(var):
    """
    Return the sort (i.e., type) of a valid variable string.

    Examples:
        >>> variable.sort('h3')
        'h'
        >>> variable.sort('ref-ind12')
        'ref-ind'
    """
    return split(var)[0]


def id(var):
    """
    Return the integer id of a valid variable string.

    Examples:
        >>> variable.id('h3')
        3
        >>> variable.id('ref-ind12')
        12
    """
    return int(split(var)[1])


def is_valid(var):
    """
    Return `True` if *var* is a valid variable string.

    Examples:
        >>> variable.is_valid('h3')
        True
        >>> variable.is_valid('ref-ind12')
        True
        >>> variable.is_valid('x')
        False
    """
    return variable_re.match(var) is not None


class VariableFactory(object):
    """
    Simple class to produce variables by incrementing the variable id.

    This class is intended to be used when creating an MRS from a
    variable-less representation like DMRS where the variable types
    are known but no variable id is assigned.

    Args:
        starting_vid (int): the id of the first variable
    Attributes:
        vid (int): the id of the next variable produced by :meth:`new`
        index (dict): a mapping of ids to variables
        store (dict): a mapping of variables to associated properties
    """

    def __init__(self, starting_vid=1):
        self.vid = starting_vid
        self.index = {}  # to map vid to created variable
        self.store = {}  # to recall properties from varstrings

    def new(self, sort, properties=None):
        """
        Create a new variable for the given *sort*.

        Args:
            sort (str): the type of the variable to produce
            properties (list): properties to associate with the variable
        Returns:
            A (variable, properties) tuple
        """
        if sort is None:
            sort = UNKNOWN
        # find next available vid
        vid, index = self.vid, self.index
        while vid in index:
            vid += 1
        varstring = '{}{}'.format(sort, vid)
        index[vid] = varstring
        if properties is None:
            properties = []
        self.store[varstring] = properties
        self.vid = vid + 1
        return (varstring, properties)