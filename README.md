## Usage
```py
import shucks
import functools
import string

# custom check
def title(data):

    letter = data[0]

    if letter in string.ascii_uppercase:

      return

    # throw error if something's wrong
    raise shucks.Error('title', letter)

# schema
human = {
    'gold': int,
    'name': shucks.And(
        str,
        # prebuilt checks
        shucks.range(1, 32),
        # callables used with just data
        title
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
