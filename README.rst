Installing
==========

.. code-block:: bash

  pip3 install shucks

Simple Usage
------------

.. code-block:: py

  import shucks
  import string

  # custom check
  def title(data):
    letter = data[0]
    if letter in string.ascii_uppercase:
        return
    raise shucks.Error('title', lower, upper)

  # schema
  human = {
    'gold': int,
    'name': shucks.And(
        str,
        # convert before checking
        shucks.Con(
          len,
          # prebuilt checks
          shucks.range(1, 32),
        ),
        # use pre-converted value
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
            'price': float,
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
            'price': 2.66,
            'color': 'silver'
        },
        {
            'name': 'Bow',
            # not float
            'price': 24,
            'color': 'brown'
        }
    ]
  }

  try:
    shucks.check(human, data, auto = True)
  except shucks.Error as error:
    # ex: instead of <class 'bool'>, show 'bool'
    print(error.show, alias = lambda value: value.__name__)

The above script will print the following:

.. code-block:: py

  >>> (
  >>>   ('value', ('items',)), # in the value of the "items" key
  >>>   ('index', (1,)), # at the 1st index of the array
  >>>   ('value', ('price',)), # in the value of the "price" key
  >>>   ('type', ('float', 'int')) # type expected float, got int
  >>> )

Links
-----

- `Documentation <https://shucks.readthedocs.io>`_
