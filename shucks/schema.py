import functools
import collections.abc
import os

from . import helpers


__all__ = ('nil', 'Error', 'Op', 'Nex', 'Or', 'And', 'Not', 'Exc', 'Opt', 'Con',
           'Rou', 'If', 'check', 'trace', 'wrap')


__marker = object()


#: Used to signify nonexistance.
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

    def draw(self, alias = lambda pair: pair):

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

        return self.args[0]

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

    First data passing will be used for tracing.

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

    Last data passing will be used for tracing.

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

    Data will not be used for tracing.

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

    Data passing will be used for tracing.

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


#: Alias of :class:`Rou`.
If = Rou


class Not:

    """
    Represents the ``NOT`` operator.

    Data will be used for tracing.

    .. code-block:: py

        fig = Not(And(str, Con(len, lambda v: v > 5)))
        check(fig, 'pass1234')
    """

    __slots__ = ('figure',)

    def __init__(self, figure):

        self.figure = figure


class Exc:

    """
    Fail when exceptions are raised.

    Data will be used for tracing.

    .. code-block:: py

        fig = Exc(int, ValueError)
    """

    __slots__ = ('figure', 'exceptions')

    def __init__(self, figure, exceptions):

        self.figure = figure
        self.exceptions = exceptions


def _c_nex(figure, data, **extra):

    result = __marker

    for figure in figure:
        try:
            result = check(figure, data, **extra)
        except Error as _error:
            error = _error
        else:
            break
    else:
        raise error

    return result


def _c_and(figure, data, **extra):

    result = __marker

    for figure in figure:
        subresult = check(figure, data, **extra)
        if not subresult is __marker:
            result = subresult

    return result


def _c_not(figure, data, **extra):

    try:
        check(figure.figure, data, **extra)
    except Error:
        return data

    raise Error('not', figure.figure, data)


def _c_exc(figure, data, **extra):

    try:
        result = check(figure.figure, data, **extra)
    except figure.exceptions:
        raise Error('except', figure.figure, figure.exceptions, data)

    return result


def _c_type(figure, data, **extra):

    cls = type(data)

    if issubclass(cls, figure):
        return data

    raise Error('type', figure, cls)


def _c_object(figure, data, **extra):

    if figure == data:
        return data

    raise Error('object', figure, data)


def _c_array(figure, data, **extra):

    limit = len(figure)

    figure_g = iter(figure)
    data_g = iter(enumerate(data))

    cache = __marker

    result = []

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
                subresult = check(figure, data, **extra)
            except Error as error:
                if multi and size < limit:
                    data_g = helpers.prepend(data_g, source)
                    break
                raise Error('index', index) from error
            if not subresult is __marker:
                result.append(subresult)
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

    return result


def _c_dict(figure, data, **extra):

    result = {}

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
            subresult = check(figure_v, data_v, **extra)
        except Error as error:
            raise Error('value', figure_k) from error
        if not subresult is __marker:
            result[figure_k] = subresult

    return result


def _c_callable(figure, data, **extra):

    result = figure(data)

    if result is True:
        return __marker

    if result is False:
        raise Error('call', figure, data)

    return result


def _c_con(figure, data, **extra):

    data = figure.change(data)

    figure = figure.figure

    check(figure, data)

    return __marker


def _c_rou(figure, data, **extra):

    try:
        check(figure.figure, data, **extra)
    except Error:
        figure = figure.failure
    else:
        figure = figure.success

    return check(figure, data, **extra)


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
        _c_not,
        lambda cls: (
            issubclass(cls, Not)
        )
    ),
    (
        _c_exc,
        lambda cls: (
            issubclass(cls, Exc)
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
    ),
    (
        _c_con,
        lambda cls: (
            issubclass(cls, Con)
        )
    ),
    (
        _c_rou,
        lambda cls: (
            issubclass(cls, Rou)
        )
    )
)


def check(figure, data, auto = False, extra = []):

    """
    Validates data against the figure and returns a compliant copy.

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
        return use(*args, auto = auto, extra = extra)

    cls = type(figure)

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


#: Alias of :class:`check`.
trace = check


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
