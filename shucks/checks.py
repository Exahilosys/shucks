import operator
import functools

from . import schema


__all__ = ('range', 'contain')


def range(lower, upper, left = True, right = True):

    """
    Check whether the value is between the lower and upper bounds.

    :param float lower:
        One of the bounds.
    :param float upper:
        One of the bounds.
    :param bool left:
        Use left inclusive.
    :param bool right:
        use right inclusive.

    .. code-block:: py

        >>> valid = range(0, 5.5, left = False) # (0, 5.5]
        >>> check(valid, 0) # fail, not included
    """

    def wrapper(value):

        sides = (left, right)

        operators = (operator.lt, operator.le)

        (former, latter) = map(operators.__getitem__, sides)

        if former(lower, value) and latter(value, upper):

            return

        raise schema.Error('range', lower, upper, left, right)

    return wrapper


def contain(store, white = True):

    """
    Check whether the value against the store.

    :param collections.abc.Container store:
        The store.
    :param bool white:
        Whether to check for presence or absence.

    .. code-block:: py

        >>> import string
        >>> valid = contain(string.ascii_lowercase)
        >>> check(valid, 'H') # fail, capital
    """

    def wrapper(value):

        done = value in store

        if done if white else not done:

            return

        raise schema.Error('contain', white)

    return wrapper
