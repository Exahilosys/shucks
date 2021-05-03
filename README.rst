Installing
----------

.. code-block:: bash

  pip3 install shucks

Simple Usage
------------

Validating a login form accepting email or phone and a password.

.. code-block:: py

  import shucks
  import math

  schema = shucks.And(
    dict,
    {
      'id': shucks.If(
        shucks.And(str, lambda v: '@' in v),
        shucks.Con(
          lambda v: v.split('@', 1)[1],
          shucks.contain({'gmail.com', 'hotmail.com', 'yahoo.com'})
        ),
        shucks.And(
          shucks.Or(str, int),
          shucks.Con(str, shucks.Con(len, shucks.range(10, 10)))
        )
      ),
      'password': shucks.And(
        str,
        shucks.Con(len, shucks.And(shucks.range(8, math.inf))),
        shucks.wrap(shucks.Not(lambda v: 'logo' in v), 'logo')
      ),
      shucks.Opt('remember'): bool
    }
  )

  data = {
    'id': 1234567890
    'password': 'logo1234'
  }

  shucks.check(schema, data)

Links
-----

- `Documentation <https://shucks.readthedocs.io>`_
