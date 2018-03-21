..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

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
