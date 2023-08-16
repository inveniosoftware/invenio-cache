# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-Cache is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Lock mechanisms."""


from datetime import datetime

from flask import current_app

from invenio_cache.errors import (
    LockAcquireFailed,
    LockReleaseFailed,
    LockRenewPermissionDenied,
)
from invenio_cache.proxies import current_cache


class Lock:
    """Base Lock class."""

    def __init__(self, lock_id):
        """Initialises the lock instance.

        It does not grant access to the lock itself. To access the lock, call ``lock.acquire``.
        The lock can be used in two ways:

        1) inside a context:

        .. code-block:: python

            with lock(lock_id) as lock:
                lock.acquire()
                f()

        2) manually calling each block / unblock mechanism:

        .. code-block:: python

            lock = lock(lock_id)
            try:
                lock.acquire()
                f()
                lock.release()
            except LockAcquireFailed:
                pass

        :param lock_id: id of the lock.
        :type lock_id: str
        """
        self.lock_id = lock_id
        self._created = datetime.utcnow()

    def __enter__(self):
        """Entering the context."""
        return self

    def __exit__(self, exc_type, *args):
        """Releases the lock."""
        # Release the lock only when acquired the lock
        if exc_type is not LockAcquireFailed:
            self.release()

    @property
    def created(self):
        """Lock creation date time."""
        return self._created

    def acquire(self, **kwargs):
        """Attempts to acquire the lock.

        .. warning:

            The method to adcquire the lock must be atomic.

        """
        raise NotImplementedError

    def release(self):
        """Attempts to release the lock."""
        raise NotImplementedError

    def exists(self):
        """Checks if the lock exists."""
        raise NotImplementedError

    def __repr__(self):
        """Lock string representation."""
        return f"<Lock {self.lock_id}>"


class CachedMutex(Lock):
    """Implements a Mutex using CacheLib API.

    This lock will set a key in a cache when the lock is acquired, and delete the key when
    the lock is to be deleted.
    This mechanism is based on the principle that the desired cache's backend provides an atomic
    write operation (e.g. "write if not exists").
    """

    _cache = current_cache

    def acquire(self, timeout):
        """Attempts to acquire the lock.

        The method to adcquire the lock must be atomic.

        If an error occurred with the backend, the exception is logged and re-raised.
        If the lock was not released, a ``LockReleaseFailed`` exception is raised.

        :returns: ``True`` if the lock was acquired, ``False`` otherwise .
        :rtype: boolean
        :param timeout: lock key timeout.
        :type timeout: int
        :raises: Exception, LockReleaseFailed
        """
        success = False
        try:
            # Atomic operation to get the lock
            success = self._cache.add(self.lock_id, True, timeout=timeout)
        except:
            # Unexpected error with the cache, we just log it and re-raise
            current_app.logger.error(
                f"Unexpected backend failure when acquiring lock {self.lock_id}."
            )
            raise

        if not success:
            raise LockAcquireFailed(self)

        return success

    def release(self):
        """Attempts to release the lock.

        If an error occurred with the backend, the exception is logged and re-raised.
        If the lock was not released, a ``LockReleaseFailed`` exception is raised.

        :returns: ``True`` if the lock was released, ``False`` otherwise .
        :rtype: boolean
        :raises: Exception, LockReleaseFailed
        """
        success = False
        try:
            success = self._cache.delete(self.lock_id)
        except:
            # Unexpected error with the cache, we just log it and re-raise
            current_app.logger.error(
                f"Unexpected backend failure when releasing lock {self.lock_id}."
            )
            raise

        if not success:
            raise LockReleaseFailed(self)

        return success

    def exists(self):
        """Checks if the lock exists.

        :return: ``True``if the lock exists, ``False``otherwise.
        :rtype: bool
        :raises: Exception
        """
        exists = False
        try:
            # ``has``is a cheaper operation than ``get``
            exists = self._cache.has(self.lock_id)
        except:
            # Unexpected error with the cache, we just log it and re-raise
            current_app.logger.error(
                f"Unexpected backend failure when releasing lock {self.lock_id}."
            )
            raise
        return exists

    def _has_permission(self):
        """Whether the current lock instance has permission on the physical lock.

        It is empty for now as it may be needed in the future when locks should be "shared" between contexts.
        """
        return True

    def acquire_or_renew(self, timeout):
        """Attempts to acquire the lock. If not possible, renews its timeout.

        The lock's timeout is updated in the cache, effectively prolonging the lock's duration.

        .. note::

            This method requires that the caller has the necessary permission.

        .. warning::

            If the lock didn't exist before renewing, it will be created with the new timeout.

        :param timeout: New timeout, in seconds.
        :type timeout: int
        :raises: Exception, LockAcquireFailed, LockRenewPermissionDenied
        """
        success = False
        if not self._has_permission():
            raise LockRenewPermissionDenied(self)

        # Overwrites previous timeout. If it didn't exist, the lock is created.
        try:
            success = self.acquire(timeout=timeout)
        except LockAcquireFailed:
            # Renew the lock if it already existed before
            success = self._cache.set(self.lock_id, True, timeout)
        except:
            # Unexpected error with the cache, we just log it and re-raise
            current_app.logger.error(
                f"Unexpected backend failure when releasing lock {self.lock_id}."
            )
            raise

        if not success:
            raise LockAcquireFailed(self)

        return success
