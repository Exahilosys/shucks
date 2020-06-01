import collections
import operator
import functools

from . import schema


__all__ = ('range', 'contain')


class range(
        collections.namedtuple(
            'range',
            'lower upper left right',
            defaults = (True, True)
        )
    ):

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

    __slots__ = ()

    def __call__(self, value):

        sides = (self.left, self.right)
        operators = (operator.lt, operator.le)
        (former, latter) = map(operators.__getitem__, sides)
        if former(self.lower, value) and latter(value, self.upper):
            return

        raise schema.Error('range', self)


class contain(
        collections.namedtuple(
            'contain',
            'store white',
            defaults = (True,)
        )
    ):

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

    __slots__ = ()

    def __call__(self, value):

        if (value in self.store) is self.white:
            return

        raise schema.Error('contain', self)
