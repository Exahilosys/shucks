import functools
import collections.abc
import numbers
import types


__all__ = ()


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


class Or(Op):

    __slots__ = ()


class And(Op):

    __slots__ = ()


class Opt:

    __slots__ = ('value',)

    def __init__(self, value):

        self.value = value

    def __repr__(self):

        return f'{self.__class__.__name__}({self.value})'


__marker = object()


def c_or(schema, data, **extra):

    for schema in schema:

        try:

            validate(schema, data, **extra)

        except Error as _error:

            error = _error

        else:

            break

    else:

        raise error


def c_and(schema, data, **extra):

    for schema in schema:

        validate(schema, data, **extra)


def c_type(schema, data):

    cls = type(data)

    if not issubclass(cls, schema):

        raise Error('type', schema, cls)


def c_object(schema, data):

    if schema == data:

        return

    raise Error('object', schema, data)


def c_array(schema, data, **extra):

    length = len(schema)

    generate = iter(data)

    cache = __marker

    single = True

    index = 0

    for schema in schema:

        if schema is ...:

            (schema, single) = (cache, False)

        if schema is __marker:

            raise ValueError('got ellipsis before schema')

        while True:

            try:

                data = next(generate)

            except StopIteration:

                if index < length:

                    raise Error('small', index, length)

                break

            try:

                validate(schema, data, **extra)

            except Error as error:

                raise Error('index', index) from error

            index += 1

            if single:

                break

        cache = schema


def c_dict(schema, data, **extra):

    for (schema_k, schema_v) in schema.items():

        optional = isinstance(schema_k, Opt)

        if optional:

            schema_k = schema_k.value

        try:

            data_v = data[schema_k]

        except KeyError:

            if optional:

                continue

            raise Error('key', schema_k) from error

        try:

            validate(schema_v, data_v, **extra)

        except Error as error:

            raise Error('value', schema_k) from error


overs = (
    (
        c_or,
        lambda cls: (
            issubclass(cls, Or)
        )
    ),
    (
        c_and,
        lambda cls: (
            issubclass(cls, And)
        )
    ),
    (
        c_dict,
        lambda cls: (
            issubclass(cls, collections.abc.Mapping)
        )
    ),
    (
        c_array,
        lambda cls: (
            issubclass(cls, collections.abc.Sequence)
            and not issubclass(
                cls,
                (str, bytes)
            )
        )
    )
)


def validate(schema, data, auto = False):

    creator = isinstance(schema, type)

    if not creator and callable(schema):

        execute = schema

    else:

        if creator:

            check = c_type

        else:

            cls = type(schema)

            for (check, use) in overs:

                if use(cls):

                    break

            else:

                check = None

            if not check:

                if auto:

                    c_type(cls, data)

                check = c_object

            else:

                check = functools.partial(check, auto = auto)

        execute = functools.partial(check, schema)

    execute(data)
