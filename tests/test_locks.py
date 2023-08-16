# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-cache is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Test locks."""
import pytest

from invenio_cache.errors import LockAcquireFailed
from invenio_cache.lock import CachedMutex


def test_cached_mutex(app):
    """Tests two lock objects trying to acquire/release the same lock."""
    lock_id = "test_cache_123"

    # Attempt to retrieve the lock again
    lock = CachedMutex(lock_id)

    # Acquire lock for ever (0 means no timeout)
    assert lock.acquire(timeout=0)

    # Second lock can't acquire the lock
    second_lock = CachedMutex(lock_id)
    with pytest.raises(LockAcquireFailed):
        not second_lock.acquire(timeout=1)

    # Release lock
    lock.release()

    # Second lock can acquire the lock now and release it in the end
    assert second_lock.acquire(timeout=1)
    assert second_lock.exists()
    assert second_lock.release()


def test_cached_mutex_context(app):
    """Tests the CachedMutex context manager."""
    lock_id = "test_cache_123"

    with CachedMutex(lock_id) as lock:
        assert lock.acquire(timeout=5)

    # Lock was released on __exit__ so it can be acquired again
    with CachedMutex(lock_id) as lock:
        lock.acquire(timeout=1)

    # Acquire the lock and try to acquire it again : should throw an error
    with CachedMutex(lock_id) as lock:
        lock.acquire(timeout=1)

        # Throws if asecond caller tries to acquire the lock
        with pytest.raises(LockAcquireFailed):
            with CachedMutex(lock_id) as second_lock:
                second_lock.acquire(timeout=2)


def test_cached_mutex_renew(app):
    """Tests the renewal of a cached lock."""
    lock_id = "test_cache_123"

    lock = CachedMutex(lock_id)

    # First caller acquires lock and renews it
    assert lock.acquire(timeout=1)
    assert lock.acquire_or_renew(100)

    # Second caller can renew the lock
    second_lock = CachedMutex(lock_id)
    assert second_lock.acquire_or_renew(100)
    assert second_lock.exists()


def test_cache_failure(app, monkeypatch):
    """Tests the lock behavior when the cache fails unexpectedly."""

    # Mock the cache backend to simulate a failure
    def mock_raise_exc(*args, **kwargs):
        raise Exception("Cache backend failure")

    # Monkeypatch 'add', 'delete' and 'has' methods from cache API.
    monkeypatch.setattr(app.extensions["invenio-cache"].cache, "add", mock_raise_exc)
    monkeypatch.setattr(app.extensions["invenio-cache"].cache, "delete", mock_raise_exc)
    monkeypatch.setattr(app.extensions["invenio-cache"].cache, "has", mock_raise_exc)

    lock = CachedMutex("test_123")
    with pytest.raises(Exception):
        lock.acquire(timeout=60)

    with pytest.raises(Exception):
        lock.release()

    with pytest.raises(Exception):
        lock.exists()
