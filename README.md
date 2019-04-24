## Usage
```py
import shucks
import functools

# custom check
def lengthy(min, max, data):

    length = len(data)

    if min <= length <= max:

        return

    code = 'length'

    # throw error if something's wrong
    raise shucks.Error(code, min, max)

# schema
human = {
    'gold': int,
    'name': shucks.And(
        str,
        # callables used with just data
        functools.partial(lengthy, 1, 16)
    ),
    'animal': shucks.Or(
        'dog',
        'horse',
        'cat'
    ),
    'sick': bool,
    'items': [
        {
            'name': str,
            'worth': float,
            # optional key
            shucks.Opt('color'): str
        },
        # infinitely check values with last schema
        ...
    ]
}

data = {
    'gold': 100,
    'name': 'Merida',
    'animal': 'horse',
    'sick': False,
    'items': [
        {
            'name': 'Arrow',
            'worth': 2.66,
            'color': 'silver'
        },
        {
            'name': 'Bow',
            # not float
            'worth': 24,
            'color': 'brown'
        }
    ]
}

try:

    shucks.validate(human, data, auto = True)

except shucks.Error as error:

    for error in error.chain:

        print(error)
```
```py
>>> Error(value: 'items') # in the value of the "items" key
>>> Error(index: 1) # on the first entry of the array
>>> Error(value: 'worth') # on the value of the "worth" key
>>> Error(type: <class 'float'>, <class 'int'>) # expected float but got int
```
## Installing
```
python3 -m pip install shucks
```
