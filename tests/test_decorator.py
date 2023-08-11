# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from __future__ import absolute_import, print_function

import pytest

from invenio_cache import cached_unless_authenticated
from invenio_cache.decorators import lock_if_renew
from invenio_cache.errors import LockedError
from invenio_cache.lock import CachedMutex


def test_decorator(base_app, ext):
    """Test cached_unless_authenticated."""
    base_app.config["MYVAR"] = "1"
    ext.is_authenticated_callback = lambda: False

    @base_app.route("/")
    @cached_unless_authenticated()
    def my_cached_view():
        return base_app.config["MYVAR"]

    # Test when unauthenticated
    with base_app.test_client() as c:
        # Generate cache
        assert c.get("/").get_data(as_text=True) == "1"
        base_app.config["MYVAR"] = "2"
        # We are getting a cached version
        assert c.get("/").get_data(as_text=True) == "1"

    # Test for when authenticated
    base_app.config["MYVAR"] = "1"
    ext.is_authenticated_callback = lambda: True

    with base_app.test_client() as c:
        # Generate cache
        assert c.get("/").get_data(as_text=True) == "1"
        base_app.config["MYVAR"] = "2"
        # We are NOT getting a cached version
        assert c.get("/").get_data(as_text=True) == "2"


# Mocked CachedMutex class
class MockCachedMutex(CachedMutex):
    def _has_permission(self):
        return False  # Mock _has_permission to return False


def test_lock_if_renew_decorator_failure(app):
    """Test the decorator ``test_lock_if_renew`` using a lock without permissions."""

    # Test the decorator behavior when _has_permission is False
    # Example function using the decorator
    @lock_if_renew("test_lock", "resource_id", MockCachedMutex, timeout=60)
    def process_resource(resource_id=None):
        pass

    resource_id = "123"
    with pytest.raises(LockedError):
        process_resource(resource_id=resource_id)


def test_lock_if_renew_decorator(app):
    """Test the decorator ``test_lock_if_renew`` using a lock with permissions."""
    # Test the decorator behavior when _has_permission is False

    @lock_if_renew("test_lock", "resource_id", CachedMutex, timeout=60)
    def process_resource(resource_id=None):
        pass

    resource_id = "123"
    process_resource(resource_id=resource_id)

    lock = CachedMutex("test_lock.123")
    assert not lock.exists()
