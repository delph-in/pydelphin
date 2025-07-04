"""
Functions for working with MRS variables.
"""

import re
from collections.abc import Iterable
from typing import Optional

# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401

UNSPECIFIC         = 'u'  # also 'unbound'; previously 'unknown'
INDIVIDUAL         = 'i'
INSTANCE_OR_HANDLE = 'p'
EVENTUALITY        = 'e'
INSTANCE           = 'x'
HANDLE             = 'h'


# Functions

_variable_re = re.compile(r'^([-\w]*[^\s\d])(\d+)$')


def split(var: str) -> tuple[str, str]:
    """
    Split a valid variable string into its variable type and id.

    Note that, unlike :func:`id`, the id is returned as a string.

    Examples:
        >>> variable.split('h3')
        ('h', '3')
        >>> variable.split('ref-ind12')
        ('ref-ind', '12')
    """
    match = _variable_re.match(var)
    if match is None:
        raise ValueError(f'Invalid variable string: {var!s}')
    else:
        return match.group(1), match.group(2)


def type(var: str) -> str:
    """
    Return the type (i.e., sort) of a valid variable string.

    :func:`sort` is an alias for :func:`type`.

    Examples:
        >>> variable.type('h3')
        'h'
        >>> variable.type('ref-ind12')
        'ref-ind'
    """
    return split(var)[0]


sort = type  #: :func:`sort` is an alias for :func:`type`.


def id(var: str) -> int:
    """
    Return the integer id of a valid variable string.

    Examples:
        >>> variable.id('h3')
        3
        >>> variable.id('ref-ind12')
        12
    """
    return int(split(var)[1])


def is_valid(var: str) -> bool:
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
    return _variable_re.match(var) is not None


class VariableFactory:
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

    vid: int
    index: dict[int, str]  # vid: var
    store: dict[str, list[tuple[str, str]]]  # var: [(prop, val)]

    def __init__(self, starting_vid: int = 1):
        self.vid = starting_vid
        self.index = {}
        self.store = {}

    def new(
        self,
        type: Optional[str],
        properties: Optional[Iterable[tuple[str, str]]] = None,
    ) -> str:
        """
        Create a new variable for the given *type*.

        Args:
            type (str): the type of the variable to produce
            properties (list): properties to associate with the variable
        Returns:
            A (variable, properties) tuple
        """
        if type is None:
            type = UNSPECIFIC
        # find next available vid
        vid, index = self.vid, self.index
        while vid in index:
            vid += 1
        varstring = f'{type}{vid}'
        index[vid] = varstring
        if properties is None:
            properties = []
        self.store[varstring] = list(properties)
        self.vid = vid + 1
        return varstring
