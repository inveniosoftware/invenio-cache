# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2023 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Decorators to help with caching."""

import hashlib
import threading
import time
from functools import wraps

from .proxies import current_cache, current_cache_ext


def cached_unless_authenticated(timeout=50, key_prefix="default"):
    """Cache anonymous traffic."""

    def caching(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cache_fun = current_cache.cached(
                timeout=timeout,
                key_prefix=key_prefix,
                unless=lambda: current_cache_ext.is_authenticated_callback(),
            )
            return cache_fun(f)(*args, **kwargs)

        return wrapper

    return caching


def cached_with_expiration(f):
    """In-process cache function results, with optional expiration and entropy.

    This decorator caches function results in-process and not in a distributed
    cache, allowing for optional expiration.
    Entries are based on function arguments and can include entropy to prevent
    multiple keys from expiring simultaneously.
    This implementation is highly inspired by the native functools.lru_cache. This
    func can be replaced if/when lru_cache will accept an expiration time.

    To tune cache ttl and entropy, the decorated function should have the following
    kwargs:
    :param cache_ttl (int): Expiration time in seconds. Default is 3600 seconds.
    :param cache_entropy (bool): Add entropy to cache expiration. Default is True.
    """
    cache = {}
    cache_lock = threading.Lock()
    hits = misses = 0

    @wraps(f)
    def wrapper(*args, **kwargs):
        """Wrapper."""
        nonlocal hits, misses
        cache_ttl = kwargs.pop("cache_ttl", 3600)
        with_entropy = kwargs.pop("cache_entropy", True)

        # Create a hashable key that includes args and the sorted kwargs
        key = (args) + tuple(sorted(kwargs.items()))

        entropy = 0
        if with_entropy:
            # calculate entropy
            key_str = str(key)
            # calculate 2-digits int from args/kwargs to prevent keys created
            # at the same time from expiring simultaneously
            entropy = int(hashlib.md5(key_str.encode()).hexdigest(), 16) % 100

        now = time.time()
        with cache_lock:
            cache_hit = (
                key in cache and now - cache[key][1] < cache_ttl
            )  # exists and not expired
            if cache_hit:
                hits += 1
                return cache[key][0]
            else:
                result = f(*args, **kwargs)
                cache[key] = (result, now + entropy)
                misses += 1
                return result

    def cache_info():
        """Report cache statistics."""
        nonlocal hits, misses
        with cache_lock:
            return (hits, misses)

    def cache_clear():
        """Clear the cache."""
        nonlocal hits, misses
        with cache_lock:
            cache.clear()
            hits = misses = 0

    wrapper.cache_clear = cache_clear
    wrapper.cache_info = cache_info
    return wrapper
