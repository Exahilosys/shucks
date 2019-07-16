import functools
import collections.abc


__all__ = ('Error', 'Op', 'Nex', 'And', 'Sig', 'Opt', 'Con', 'check', 'Or')


class Error(Exception):

    __slots__ = ()

    @property
    def chain(self):

        while True:

            yield self

            self = self.__cause__

            if self is None:

                break

    def __repr__(self):

        (code, *info) = self.args

        info = ', '.join(map(repr, info))

        return f'{self.__class__.__name__}({code}: {info})'

    def __str__(self):

        return self.__repr__()


class Op(tuple):

    __slots__ = ()

    def __new__(cls, *values):

        return super().__new__(cls, values)

    def __repr__(self):

        info = ','.join(map(repr, self))

        return f'{self.__class__.__name__}({info})'


class Nex(Op):

    __slots__ = ()


class And(Op):

    __slots__ = ()


class Sig:

    __slots__ = ('value',)

    def __init__(self, value):

        self.value = value

    def __repr__(self):

        return f'{self.__class__.__name__}({self.value})'


class Opt(Sig):

    __slots__ = ()


class Con(Sig):

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


def _c_type(figure, data):

    cls = type(data)

    if not issubclass(cls, figure):

        raise Error('type', figure, cls)


def _c_object(figure, data):

    if figure == data:

        return

    raise Error('object', figure, data)


def _c_array(figure, data, **extra):

    length = len(figure)

    generate = iter(data)

    cache = __marker

    single = True

    index = 0

    for figure in figure:

        if figure is ...:

            length -= 1

            (figure, single) = (cache, False)

        if figure is __marker:

            raise ValueError('got ellipsis before figure')

        while True:

            try:

                data = next(generate)

            except StopIteration:

                if index < length:

                    raise Error('small', index, length)

                break

            try:

                check(figure, data, **extra)

            except Error as error:

                raise Error('index', index) from error

            index += 1

            if single:

                break

        cache = figure


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

            raise Error('key', figure_k) from error

        try:

            check(figure_v, data_v, **extra)

        except Error as error:

            raise Error('value', figure_k) from error


_overs = (
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
            issubclass(cls, collections.abc.Sequence)
            and not issubclass(
                cls,
                (str, bytes)
            )
        )
    )
)


def check(figure, data, auto = False):

    if isinstance(figure, Con):

        data = figure.change(data)

        figure = figure.value

    source = isinstance(figure, type)

    if not source and callable(figure):

        execute = figure

    else:

        if source:

            use = _c_type

        else:

            cls = type(figure)

            for (use, accept) in _overs:

                if accept(cls):

                    break

            else:

                use = None

            if not use:

                if auto:

                    _c_type(cls, data)

                use = _c_object

            else:

                use = functools.partial(use, auto = auto)

        execute = functools.partial(use, figure)

    execute(data)


Or = Nex
