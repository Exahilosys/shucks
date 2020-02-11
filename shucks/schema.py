import functools
import collections.abc

from . import helpers


__all__ = ('Error', 'Op', 'Nex', 'Or', 'And', 'Sig', 'Opt', 'Con', 'check')


class Error(Exception):

    """
    Raised upon check failure.

    :var gen chain:
        Yields all contributing errors.
    """

    __slots__ = ()

    @property
    def chain(self):

        while True:

            yield self

            self = self.__cause__

            if self is None:

                break

    def draw(self, alias = lambda value: value):

        (name, *values) = self.args

        data = tuple(map(alias, values))

        return (name, data)

    def show(self, **kwargs):

        """
        show(alias = None)

        Get simple json-friendly info about this error family.

        :param func alias:
            Used on every ``(name, value)``'s value; result used instead.
        """

        return tuple(error.draw(**kwargs) for error in self.chain)

    def __repr__(self):

        (code, *info) = self.args

        info = ', '.join(map(repr, info))

        return f'{self.__class__.__name__}({code}: {info})'

    def __str__(self):

        return self.__repr__()


class Op(tuple):

    """
    Represents a collection of operatable values.
    """

    __slots__ = ()

    def __new__(cls, *values):

        return super().__new__(cls, values)

    def __repr__(self):

        info = ','.join(map(repr, self))

        return f'{self.__class__.__name__}({info})'


class Nex(Op):

    """
    Represents the ``OR`` operator.

    Values will be checked in order. If none pass, the last error is raised.

    .. code-block:: py

        >>> def less(value):
        >>>     return value < 5:
        >>> def more(value):
        >>>     return value > 9
        >>> fig = Nex(int, less, more)
        >>> check(fig, 12)

    The above will pass, since ``12`` is greater than ``9``.
    """

    __slots__ = ()

    def __new__(cls, *values, any = False):

        if any:

            (value,) = values

            values = helpers.ellisplit(value)

            # tupple'ing it cause yields are live
            values = map(type(value), tuple(values))

        return super().__new__(cls, *values)



#: Alias of :class:`Nex`.
Or = Nex


class And(Op):

    """
    Represents the ``AND`` operator.

    Values will be checked in order. If one fails, its error is raised.

    .. code-block:: py

        >>> def less(value):
        >>>     return value < 5:
        >>> def more(value):
        >>>     return value > 9
        >>> fig = And(int, less, more)
        >>> check(fig, 12)

    The above will fail, since ``12`` is not less than ``5``.
    """

    __slots__ = ()


class Sig:

    """
    Represents an arbitrary value that's meant to be used in a specfic way.
    """

    __slots__ = ('value',)

    def __init__(self, value):

        self.value = value

    def __repr__(self):

        return f'{self.__class__.__name__}({self.value})'


class Opt(Sig):

    """
    Signals an optional value.

    .. code-block:: py

        >>> fig = {Opt('one'): int, 'two': int}
        >>> check(fig, {'two': 5})

    The above will pass since ``"one"`` is not required but ``"two"`` is.
    """

    __slots__ = ()


class Con(Sig):

    """
    Signals a conversion to the data before checking.

    .. code-block:: py

        >>> def less(value):
        >>>     return value < 8
        >>> fig = (str, Con(len, less))
        >>> check(fig, 'ganglioneuralgia')

    The above will fail since the length of... that is greater than ``8``.
    """

    __slots__ = ('change',)

    def __init__(self, change, *args):

        super().__init__(*args)

        self.change = change


__marker = object()


def _c_nex(figure, data, **extra):

    for figure in figure:

        try:

            check(figure, data, **extra)

        except Error as _error:

            error = _error

        else:

            break

    else:

        raise error


def _c_and(figure, data, **extra):

    for figure in figure:

        check(figure, data, **extra)


def _c_type(figure, data, **extra):

    cls = type(data)

    if not issubclass(cls, figure):

        raise Error('type', figure, cls)


def _c_object(figure, data, **extra):

    if figure == data:

        return

    raise Error('object', figure, data)


def _c_array(figure, data, **extra):

    limit = len(figure)

    figure_g = iter(figure)

    data_g = iter(enumerate(data))

    cache = __marker

    size = 0

    for figure in figure_g:

        multi = figure is ...

        if multi:

            limit -= 1

            figure = cache

        if figure is __marker:

            raise ValueError('got ellipsis before figure')

        for source in data_g:

            (index, data) = source

            try:

                check(figure, data, **extra)

            except Error as error:

                if multi and size < limit:

                    data_g = helpers.prepend(data_g, source)

                    break

                raise Error('index', index) from error

            if multi:

                continue

            size += 1

            break

        cache = figure

    if size < limit:

        raise Error('small', limit, size)

    try:

        next(data_g)

    except StopIteration:

        pass

    else:

        raise Error('large', limit)


def _c_dict(figure, data, **extra):

    for (figure_k, figure_v) in figure.items():

        optional = isinstance(figure_k, Opt)

        if optional:

            figure_k = figure_k.value

        try:

            data_v = data[figure_k]

        except KeyError:

            if optional:

                continue

            raise Error('key', figure_k) from None

        try:

            check(figure_v, data_v, **extra)

        except Error as error:

            raise Error('value', figure_k) from error


def _c_callable(figure, data, **extra):

    result = figure(data)

    if result:

        return

    raise Error('call', figure, data)


_select = (
    (
        _c_nex,
        lambda cls: (
            issubclass(cls, Nex)
        )
    ),
    (
        _c_and,
        lambda cls: (
            issubclass(cls, And)
        )
    ),
    (
        _c_dict,
        lambda cls: (
            issubclass(cls, collections.abc.Mapping)
        )
    ),
    (
        _c_array,
        lambda cls: (
            issubclass(cls, collections.abc.Iterable)
            and not issubclass(cls, (str, bytes))
        )
    ),
    (
        _c_callable,
        lambda cls: (
            issubclass(cls, collections.abc.Callable)
        )
    )
)


def check(figure, data, auto = False):

    """
    Validates data against the figure.

    :param any figure:
        Some object or class to validate against.
    :param any data:
        Some object or class to validate.
    :param bool auto:
        Whether to validate types.
    """

    if isinstance(figure, Con):

        data = figure.change(data)

        figure = figure.value

    if isinstance(figure, type):

        use = _c_type

    else:

        cls = type(figure)

        if auto:

            if not isinstance(figure, Op):

                _c_type(cls, data)

        for (use, accept) in _select:

            if accept(cls):

                break

        else:

            use = _c_object

    use(figure, data, auto = auto)
