Reference
=========

Quick schema validation.

.. toctree::
  :maxdepth: 2

.. automodule:: shucks.schema
  :members:
  :show-inheritance:

Errors
------

Type fails raise:

.. code-block:: py

  Error('type', expected_cls, given_cls)

Object equality fails raise:

.. code-block:: py

  Error('object', expected_val, given_val)

Array value check fails raise:

.. code-block:: py

  Error('index', index) from source_error

Arrays that are too small raise:

.. code-block:: py

  Error('small', expected_size, actual_size)

Arrays that have at least one additional value raise:

.. code-block:: py

  Error('large', exceeded_size)

.. note::

  Array checking is done in an iterator-exhausting fashion.

  Upon finishing, one more item is attempted to be generated for this error.

Missing mapping keys raise:

.. code-block:: py

  Error('key', expected_key)

Mapping value check fails raise:

.. code-block:: py

  Error('value', current_key) from source_error

Callables that don't return :code:`True` raise:

.. code-block:: py

  Error('call', used_func, current_data)

.. warn::

  :class:`ValueError` raises when neither :code:`True` or :code:`False` are
  returned.

Validators
----------

Some ready-made validators exist to make your life easier:

.. automodule:: shucks.checks
  :members:

Examples
========

All snippets assume:

.. code-block:: py

  import shucks as s

Basic
-----

.. _type:

Check if the data is a :class:`int` instance:

.. code-block:: py

  int

.. _solo:

Check if the data is :code:`4.5`:

.. code-block:: py

  4.5

.. _or:

Check if the data is :code:`4.5` or :code:`8`:

.. code-block:: py

  s.Or(4.5, 8)

.. _and:

Check if the data is a :class:`str` instance and :code:`'hello'`:

.. code-block:: py

  s.And(str, 'hello')

.. _con:

Check if the length of the data is :code:`10`:

.. code-block:: py

  s.Con(len, 10)

.. _range:

Check if the data is between incl :code:`1` and excl :code:`10`:

.. code-block:: py

  s.range(1, 10, right = False)

.. _basic_combo:

Check if the data is a :class:`str` instance and its length between incl
:code:`1` and incl :code:`10`:

.. code-block:: py

  s.And(str, s.Con(len, s.range(1, 10)))

.. _if:

Check further only if :code:`str`:

.. code-block:: py

  s.If(str, s.Con(len, s.range(1, 10)))

Check if :code:`10` characters when str, or convert and check otherwise.

.. code-block:: py

  _c_lr = s.Con(len, s.range(1, 10))

  s.If(str, _c_lr, s.Con(str, _c_lr))

.. _wrap:

Raise an error upon failure:

.. code-block:: py

  s.wrap(s.Con(len, s.range(1, 10)), 'phone', 'no more than 10 digits required')

.. _custom:

Check if the data is even:

.. code-block:: py

  even = lambda data: not data % 2

Check if every line in a file starts with :code:`_`:

.. code-block:: py

  def empty(data):
    with open(data) as file:
      lines = file.read().splitlines()
    for (index, line) in enumerate(lines):
        if not line.startswith('_'):
          raise s.Error('lines', index)
    return True # otherwise, 'call' error

.. note::

  Refer to the end of `Errors`_ for info about failing callables.

Array
-----

.. _exactly_two:

Check if the data has **two** values, both being :code:`0` or :code:`1`:

.. code-block:: py

  [s.Or(0, 1), s.Or(0, 1)]

.. _at_least_one:

Check if the data has *at least* **one** value of :code:`0` or :code:`1`:

.. code-block:: py

  [s.Or(0, 1), ...]

.. _any_amount:

Check if the data has *any amount* of :code:`0` or :code:`1`:

.. code-block:: py

  s.Or([], [s.Or(0, 1), ...])

.. tip::

  Since our schema will *probably* remain static, using :class:`tuple` instead
  of :class:`list` would have the same result and save us some memory.

.. _static:

Check if the data is a :class:`list` instance with *any amount* of :code:`0`
or :code:`1`:

.. code-block:: py

  s.And(list, s.Or((), (s.Or(0, 1), ...)))

.. _auto:

.. note::

  To enable auto type checks, simply pass :code:`auto = True` to :func:`check`.

.. _at_least_extra:

Check if the data has *at least* **one** of :code:`0` or :code:`1`, followed by
**one** value of :code:`2`:

.. code-block:: py

  [s.Or(0, 1), ..., 2]

.. _at_least_again:

Check if the data is empty or has at *at least* **one** of :code:`0` or
:code:`1`, followed by *at least* **one** value of :code:`2`:

.. code-block:: py

  s.Or([], [s.Or(0, 1), ..., 2, ...])

.. warning::

  This **does not** check if the data has *any amount* of :code:`0` or :code:`1`
  followed by *any amount* of :code:`2`

.. _at_least_redundant:

.. tip::

  To get the same effect as with :code:`s.Or([], [s.Or(0, 1), ...])`, checking
  for *any amount* for both :code:`s.Or(0, 1)` and :code:`2`,  have to do:

  .. code-block:: py

    s.Or([], [s.Or(0, 1), ...], [s.Or(0, 1), ..., 2, ...])

  :class:`~shucks.schema.Or` offers a way to eliminate this redundancy, the
  above is equal to:

  .. code-block:: py

    s.Or([s.Or(0, 1), ..., 2, ...], any = True)

  Nothing else other than one array should be used with with the ``any`` option.

  To emulate using more arguments for :class:`~shucks.schema.Or` with
  ``any``, nest them:

  .. code-block:: py

      s.Or(list, s.Or([s.Or(0, 1), ..., 2, ...], any = True))

.. _array_combo:

Check if the data is a :class:`tuple` or :class:`list` instance, with *any
amount* of :code:`0` or :code:`1` followed by *any amount* of :code:`2` and
ending with a :code:`3`:

.. code-block:: py

  s.And(s.Or(tuple, list), s.Or((), s.Or((s.Or(0, 1), ..., 2, ..., 3), any = True)))

Mapping
-------

.. _required:

Check if the data has *at least* **one** :code:`foo` key against :code:`bar`:

.. code-block:: py

  {'foo': 'bar'}

.. _optional:

Check if the data has *at most* **one** :code:`foo` key against :code:`bar`:

.. code-block:: py

  {s.Opt('foo'): 'bar'}

.. _terminology:

.. note::

  The whole "*at least*" and "*at most*" terminology might be confusing in this
  section.

  Consider "*required*" and "*optional*" respectively.

.. _mapping_combo:

Check if the data has a *required* :code:`tic` key against :code:`tac` or
:code:`toe`:

.. code-block:: py

  {'tic': s.Or('tac', 'toe')}

.. _alternative:

.. warning::

    Using :class:`~shucks.schema.Op`\s or :class:`~shucks.schema.Sig`\s other
    than :class:`~shucks.schema.Opt` for keys will lead to unexpected
    behaviour.

    Contained data is :code:`__getitem__`\'d from the root data, not checked
    sequentially for existence.

.. tip::

  To better validate key-value pairs, do:

  .. code-block:: py

    s.Con(dict.items, (('key', 'value'), ...))

.. _extra:

Extra
-----

Consider the follow classes:

.. code-block:: py

   class MyClass0:
      def __init__(self, v):
         self.v = v

   class MyClass1:
      def __init__(self, n):
         self.n = n

Create functions (``d_``) that conditionally return checkers (``c_``):

.. code-block:: py

   def c_0(figure, obj):
      shucks.check(int, obj.v)

   def c_0(figure, obj):
      shucks.check(str, obj.n)

   def d_0(figure):
      if isinstance(figure, MyClass0):
         return c_0
      if isinstance(figure, MyClass1):
         return c_1

   determinators = [d_0]

Now simply use :code:`extra = determinators` when your data includes objects of
such classes.

.. note::

   :code:`extra` accepts a list for adding and removing determinators
   accordingly.
