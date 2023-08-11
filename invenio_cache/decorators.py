# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Decorators to help with caching."""

from __future__ import absolute_import, print_function

from functools import wraps

from flask import current_app

from .errors import LockedError
from .lock import CachedMutex
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


def lock_if_renew(lock_prefix, arg_name, lock_cls, timeout=None):
    """Decorator to execute a function if the lock can be renewed.

    This decorator is used to ensure that a function is executed only if a specific lock can be successfully renewed.
    The lock is identified by a combination of `lock_prefix` and a value retrieved from `kwargs` using `arg_name`.


    :param lock_prefix: The prefix of the lock ID. It is suffixed with `kwargs[arg_name]`.
    :param arg_name: The key to identify the lock. This key retrieves the value from ``kwargs``.
    :param lock_cls: The class of the lock. It must be an instance of ``Lock``.
    :param timeout: Timeout, in seconds, for the lock to be automatically released.

    .. note::

        This decorator is designed to be used with functions that perform operations requiring exclusive access to a resource.

    .. warning::

        It is important that the lock can be renewed by the current executing context. Otherwise, the lock could end up being overwritten my an undesired entity.
    """

    def decorator_builder(f):
        @wraps(f)
        def decorate(*args, **kwargs):
            lock_value = kwargs[arg_name]
            lock_id = f"{lock_prefix}.{lock_value}"
            assert lock_id

            # CachedMutex implements ``renew()`.`
            assert issubclass(lock_cls, CachedMutex)
            lock = lock_cls(lock_id)
            if lock.renew(timeout):
                f(*args, **kwargs)
                lock.release()
            else:
                current_app.logger.debug(
                    f"Resource with lock {lock.lock_id} can't be renewed."
                )
                raise LockedError(lock)

        return decorate

    return decorator_builder
