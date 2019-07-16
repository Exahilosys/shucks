import operator
import functools


__all__ = ('range', 'contain')


def range(lower, upper, left = True, right = True):

    def wrapper(value):

        sides = (left, right)

        operators = (operator.lt, operator.le)

        former, latter = map(operators.__getitem__, sides)

        if former(lower, value) and latter(value, upper):

            return

        raise shucks.Error('range', lower, upper)

    return wrapper


def contain(store, white = True):

    def wrapper(value):

        done = value in store

        if done if white else not done:

            return

        raise shucks.Error('contain', white)

    return wrapper
