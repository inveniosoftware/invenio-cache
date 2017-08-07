Installation
============

Invenio-Cache is on PyPI so all you need is:

.. code-block:: console

   $ pip install invenio-cache

Note, depending on which cache backend you plan yo use, you need to install
extra modules. For instance for Redis you need:

.. code-block:: console

   $ pip install redis

For memcached you need either pylibmc or python-memcached installed:

.. code-block:: console

  $ pip install pylibmc
  $ pip install python-memcached
