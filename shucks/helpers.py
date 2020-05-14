import itertools


__all__ = ()


def prepend(generate, *values):

    yield from values
    yield from generate


def ellisplit(values):

    store = []
    cache = [store]

    def inform(value):
        for store in cache[:-1]:
            store.append(value)

    exhaust = True
    for value in values:
        if exhaust:
            yield store
            store = store.copy()
            cache.append(store)
            current = exhaust = False
        else:
            current = True
        store.append(value)
        if value is ...:
            exhaust = True
        elif current:
            inform(last)
        last = value

    if not exhaust:
        inform(value)

    yield store
