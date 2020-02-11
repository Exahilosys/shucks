Installing
----------

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
    return letter in string.ascii_uppercase

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
        # not converted anymore
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
            # need 3 rgb values
            shucks.Opt('color'): And(
              And(
                int,
                shucks.range(0, 255)
              ),
              shucks.range(3, 3)
            )
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
            'color': (190, 200, 230)
        },
        {
            'name': 'Bow',
            # not float
            'price': 24,
            'color': (140, 160, 15)
        }
    ]
  }

  try:
    shucks.check(human, data, auto = True)
  except shucks.Error as error:
    # ex: instead of <class 'bool'>, show 'bool'
    def human(value):
      if callable(value):
        value = value.__name__
      return value
    print(error.show(alias = human))

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
