import operator
import functools


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
    """

    def wrapper(value):

        sides = (left, right)

        operators = (operator.lt, operator.le)

        (former, latter) = map(operators.__getitem__, sides)

        if former(lower, value) and latter(value, upper):

            return

        raise shucks.Error('range', lower, upper)

    return wrapper


def contain(store, white = True):

    """
    Check whether the value against the store.

    :param collections.abc.Container store:
        The store.
    :param bool white:
        Whether to check for presence or absence.
    """

    def wrapper(value):

        done = value in store

        if done if white else not done:

            return

        raise shucks.Error('contain', white)

    return wrapper