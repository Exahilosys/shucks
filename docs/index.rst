Reference
=========

Quick schema validation.

.. toctree::
  :maxdepth: 2

.. automodule:: shucks.schema
  :members:
  :show-inheritance:

Validators
----------

Some pre-made callable validators exist to make your life easier:

.. automodule:: shucks.checks
  :members:

Examples
========

``4`` is equal to ``3``?

.. code-block:: py

  >>> valid = 3
  >>> check(valid, 4) # fail

:class:`math.inf` is :class:`float`?

.. code-block:: py

  >>> valid = float
  >>> check(valid, math.inf) # pass

:class:`tuple` has only ``1`` or ``0``\s?

.. code-block:: py

  >>> valid = (Or(1, 0), ...)
  >>> check(valid, (1, 0, 0, 0 1, 1, 0)) # pass

Password is :class:`str` and long enough?

.. code-block:: py

  >>> def long(data)
  >>>   if len(data) < 10:
  >>>     raise Error('short', data)
  >>> valid = And(str, Con(len, long))
  >>> check(valid, 'admin1234') # fail

Request has proper headers?

.. code-block:: py

  >>> valid = {'Authorization': str, Opt('X-Optional'): str}
  >>> check(valid, {'Authorization': 'nice'}) # pass

Backend returning proper schema?

.. code-block:: py

  >>> valid = {
  >>>   'users': [
  >>>     {
  >>>       'name': str,
  >>>       'phone': int,
  >>>       'address': {
  >>>         'number': int,
  >>>         'street': str,
  >>>         Opt('post'): str
  >>>       }
  >>>     },
  >>>     ...
  >>>   ],
  >>>   'settings': {
  >>>     'display': [
  >>>       int,
  >>>       int
  >>>     ],
  >>>     Opt('secret'): And(
  >>>       str,
  >>>       Con(
  >>>         len,
  >>>         checks.range(0, 32)
  >>>       )
  >>>     ),
  >>>     'session_id': Or(None, str)
  >>>   }
  >>> }
  >>> check(valid, data) # you get the point
