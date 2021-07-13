import collections
import operator
import functools
import math

from . import schema


__all__ = ('range', 'contain')


def range(a, b = None, left = True, right = True):

    """
    Check whether the value is between the lower and upper bounds.

    :param float a:
        Lower or upper bound.
    :param float b:
        Upper bound.
    :param bool left:
        Whether lower bound is inclusive.
    :param bool right:
        Whether upper bound is inclusive.

    .. code-block:: py

        >>> figure = range(5.5, left = False) # (0, 5.5]
        >>> check(figure, 0) # fail, not included
    """

    (min, max) = (0, a) if b is None else (a, b)

    sides = (left, right)

    operators = (operator.lt, operator.le)

    (former, latter) = map(operators.__getitem__, sides)

    def check(value):
        return former(min, value) and latter(value, max)

    result = schema.wrap(check, 'range', a, b, left, right)

    return result


def contain(store, white = True):

    """
    Check the membership of the value against the store.

    :param collections.abc.Container store:
        The store.
    :param bool white:
        Whether to check for presence or absence.

    .. code-block:: py

        >>> import string
        >>> figure = contain(string.ascii_lowercase)
        >>> check(figure, 'H') # fail, capital
    """

    def check(value):
        return (value in store) is white

    result = schema.wrap(check, 'contain', store, white)

    return result
