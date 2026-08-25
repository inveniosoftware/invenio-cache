# SPDX-FileCopyrightText: 2017-2018 CERN.
# SPDX-FileCopyrightText: 2025 Graz University of Technology.
# SPDX-FileCopyrightText: 2026 KTH Royal Institute of Technology.
# SPDX-License-Identifier: MIT

"""Configuration for Invenio-Cache module.

By default the module is configured to use a Redis database 0 on localhost.
The underlying Flask-Caching module however supports many other cahe backends.

For how to configure other cache backends please refer to the `Flask-Caching
<http://pythonhosted.org/Flask-Caching/#configuring-flask-caching>`_
documentation.
"""

CACHE_KEY_PREFIX = "cache::"
"""Cache key prefix."""

#: Sets the cache type.
CACHE_TYPE = "flask_caching.backends.RedisCache"
"""Cache type.

Please refer to Flask-Caching documentation for other cache types.
"""

CACHE_REDIS_URL = "redis://localhost:6379/0"
"""Redis location and database."""


CACHE_IS_AUTHENTICATED_CALLBACK = None
"""Import path to callback.

Callback is executed to determine if request is authenticated.
"""
