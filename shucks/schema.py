import functools
import collections.abc
import os

from . import helpers


__all__ = ('nil', 'Error', 'Op', 'Nex', 'Or', 'And', 'Opt', 'Con', 'Rou', 'If',
           'check', 'wrap')


__marker = object()


"""
Used to signify nonexistance.
"""
nil = object()


class Error(Exception):

    """
    Thrown when something goes wrong.

    :var str `code`:
        Means of identification.
    :var list[str] info:
        Additional details used.
    :var gen chain:
        Yields all contributing errors.
    """

    __slots__ = ('_code', '_info')

    def __init__(self, code, *info, message = None):
        if not message:
            message = str(code)
            if info:
                message = f'{message}: ' + ', '.join(map(repr, info))
        super().__init__(message)

        self._code = code
        self._info = info

    @property
    def code(self):

        return self._code

    @property
    def info(self):

        return self._info

    @property
    def chain(self):

        while True:
            yield self
            self = self.__cause__
            if self is None:
                break

    def draw(self, alias = lambda code, info: (code, info)):

        data = tuple(map(alias, self._info))

        return (self.code, data)

    def show(self,
             use = lambda code, info: f'{code}: {info}',
             sep = os.linesep):

        """
        Get simple json-friendly info about this error family.

        :param func use:
            Used on every ``(code, info)`` for each back-error and should return
            :class:`str`.
        :param str sep:
            Used to join all parts together.
        """

        apply = lambda error: use(error.code, error.info)
        parts = map(apply, self.chain)

        value = sep.join(parts)

        return value

    def __repr__(self):

        info = ', '.join(map(repr, self._info))

        return f'{self._code}: {info}'

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


"""
Alias of :class:`Nex`.
"""
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


class Opt:

    """
    Signals an optional value.

    .. code-block:: py

        >>> fig = {Opt('one'): int, 'two': int}
        >>> check(fig, {'two': 5})

    The above will pass since ``"one"`` is not required but ``"two"`` is.
    """

    __slots__ = ('value',)

    def __init__(self, value):

        self.value = value

    def __repr__(self):

        return f'{self.__class__.__name__}({self.value})'


class Con:

    """
    Signals a conversion to the data before checking.

    .. code-block:: py

        >>> def less(value):
        >>>     return value < 8
        >>> fig = (str, Con(len, less))
        >>> check(fig, 'ganglioneuralgia')

    The above will fail since the length of... that is greater than ``8``.
    """

    __slots__ = ('change', 'figure')

    def __init__(self, change, figure):

        self.change = change
        self.figure = figure


class Rou:

    """
    Routes validation according to a condition.

    .. code-block:: py

        >>> fig = And(
        >>>     str,
        >>>     If(
        >>>         lambda data: '@' in data,
        >>>         email_fig, # true
        >>>         Con(int, phone_fig) # false
        >>>     )
        >>> )
        >>> check(fig, 'admin@domain.com')
        >>> check(fig, '0123456789')
    """

    __slots__ = ('figure', 'success', 'failure')

    def __init__(self, figure, success, failure = nil):

        self.figure = figure

        self.success = success
        self.failure = failure


"""
Alias of :class:`.Rou`.
"""
If = Rou


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

    if issubclass(cls, figure):
        return

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

    if result is True:
        return

    if result is False:
        raise Error('call', figure, data)

    raise TypeError(f'unexpected callable result {result} from {figure}')


_group_c = (
    (
        _c_type,
        lambda cls: (
            issubclass(cls, type)
        )
    ),
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
        _c_callable,
        lambda cls: (
            issubclass(cls, collections.abc.Callable)
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
    )
)


def _s_con(figure, data, **extra):

    data = figure.change(data)

    figure = figure.figure

    return (figure, data)


def _s_rou(figure, data, **extra):

    try:
        check(figure.figure, data, **extra)
    except Error:
        figure = figure.failure
    else:
        figure = figure.success

    return (figure, data)


_group_s = (
    (
        _s_con,
        lambda cls: (
            issubclass(cls, Con)
        )
    ),
    (
        _s_rou,
        lambda cls: (
            issubclass(cls, Rou)
        )
    )
)


def check(figure, data, auto = False, extra = []):

    """
    Validates data against the figure.

    :param any figure:
        Some object or class to validate against.
    :param any data:
        Some object or class to validate.
    :param bool auto:
        Whether to validate types.
    :param list[func] extra:
        Called with ``figure`` and should return :var:`.nil` or a figure.
    """

    use = check

    def execute(*args):
        use(*args, auto = auto, extra = extra)
        return True # so _c_callable compliant

    cls = type(figure)

    try:
        sub = helpers.select(_group_s, cls)
    except helpers.SelectError:
        pass
    else:
        (figure, data) = sub(figure, data)
        return execute(figure, data)

    if figure is nil:
        return

    for get in extra:
        figure = get(figure)
        if figure is nil:
            continue
        return execute(figure, data)

    try:
        use = helpers.select(_group_c, cls)
    except helpers.SelectError:
        use = _c_object

    if auto and not figure is _c_next:
        _c_type(cls, data)

    return execute(figure, data)


def wrap(figure, *parts, **kwargs):

    """
    Use ``parts`` when an error is raised against this ``figure``.

    ``kwargs`` gets passed to :func:`.check` automatically.

    .. code-block:: py

        >>> fig = wrap(
        >>>     shucks.range(4, math.inf, left = False),
        >>>     'cannot be over 4'
        >>> )
        >>> data = ...
        >>> check(fig, data)
    """

    def wrapper(data):
        try:
            value = check(figure, data, **kwargs)
        except Error as error:
            raise Error(*parts)
        return value

    return wrapper
