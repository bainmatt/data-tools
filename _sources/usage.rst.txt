.. 
    A documentation landing page containing README-style information
    including a representative use case for each module.

Usage
=====

.. __installation:

Installation
------------

To use data-tools, first install it using pip:

.. code-block:: console

   (.venv) $ pip install "git+https://github.com/bainmatt/data-tools.git#egg=datopy"


.. a placeholder example illustrating a function use case

inspection
---------------

..
    To retrieve a list of random ingredients,
    you can use the ``lumache.get_random_ingredients()`` function:

    .. autofunction:: lumache.get_random_ingredients

    Return a list of random ingredients as strings.

        >>> import lumache
        >>> lumache.get_random_ingredients()
        ['shells', 'gorgonzola', 'parsley']

    The ``kind`` parameter should be either ``"meat"``, ``"fish"``,
    or ``"veggies"``. Otherwise, :py:func:`lumache.get_random_ingredients`
    will raise an exception.

    .. autoexception:: lumache.InvalidKindError