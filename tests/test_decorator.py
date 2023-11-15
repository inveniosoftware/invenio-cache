# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2023 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

import hashlib
import time

import pytest
from flask import g

from invenio_cache import cached_unless_authenticated
from invenio_cache.decorators import cache_in_g, cached_with_expiration


def test_decorator_cached_unless_authenticated(base_app, ext):
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


def test_decorator_cached_with_expiration(mocker):
    """Test cached_with_expiration decorator."""
    one_hour = 3600

    @cached_with_expiration
    def get_cached_only_args(arg1):
        return arg1

    @cached_with_expiration
    def get_cached_only_kwargs(kwarg1="test"):
        return kwarg1

    @cached_with_expiration
    def get_cached_args_kwargs(arg1, kwarg1="test"):
        return arg1 + kwarg1

    # reset
    get_cached_only_args.cache_clear()

    # hit/miss tests without default TTL and no entropy
    assert get_cached_only_args("value1", cache_entropy=False) == "value1"
    hits, misses = get_cached_only_args.cache_info()
    assert hits == 0
    assert misses == 1
    assert get_cached_only_args("value1", cache_entropy=False) == "value1"
    hits, misses = get_cached_only_args.cache_info()
    assert hits == 1
    assert misses == 1

    expired = time.time() + one_hour + 10
    with mocker.patch("time.time", return_value=expired):
        # cache miss because it expired
        assert get_cached_only_args("value1") == "value1"
        hits, misses = get_cached_only_args.cache_info()
        assert hits == 1
        assert misses == 2

    # tests args/kwargs
    assert get_cached_only_args("value1") == "value1"
    assert get_cached_only_args((1, 2)) == (1, 2)
    assert get_cached_only_kwargs(kwarg1="value2") == "value2"
    assert get_cached_only_kwargs(kwarg1=(1, 2)) == (1, 2)
    assert get_cached_args_kwargs((1, 2), kwarg1=(3, 4)) == (1, 2, 3, 4)

    with pytest.raises(TypeError):  # TypeError: unhashable type:
        get_cached_only_args([1, 3])
        get_cached_only_kwargs(kwarg1=[1, 3])

    # reset
    get_cached_only_args.cache_clear()

    # test entropy
    now = time.time()

    assert get_cached_only_args("value1") == "value1"
    hits, misses = get_cached_only_args.cache_info()
    assert hits == 0
    assert misses == 1

    still_valid = now + one_hour
    with mocker.patch("time.time", return_value=still_valid):
        assert get_cached_only_args("value1") == "value1"
        hits, misses = get_cached_only_args.cache_info()
        assert hits == 1
        assert misses == 1

    entropy = int(hashlib.md5(str(("value1",)).encode()).hexdigest(), 16) % 100
    still_valid_with_entropy = still_valid + entropy - 1  # -1 sec to be still valid
    with mocker.patch("time.time", return_value=still_valid_with_entropy):
        assert get_cached_only_args("value1") == "value1"
        hits, misses = get_cached_only_args.cache_info()
        assert hits == 2
        assert misses == 1

    expired = still_valid + entropy
    with mocker.patch("time.time", return_value=expired):
        assert get_cached_only_args("value1") == "value1"
        hits, misses = get_cached_only_args.cache_info()
        assert hits == 2
        assert misses == 2


def test_cache_in_g_with_custom_key(app):
    """Test cache_in_g decorator with a custom key."""

    side_effect = []

    @cache_in_g(cache_key="custom_key")
    def dummy_function(arg1, arg2, kwarg1=None):
        result = arg1 + arg2
        side_effect.append(result)  # Simulating a side effect
        return result

    # First call, not in cache
    result1 = dummy_function(1, 2)
    assert result1 == 3
    assert side_effect == [3]
    assert g._cache.get("custom_key") == 3

    # Second call with the same arguments, should be retrieved from cache
    result2 = dummy_function(1, 2)
    assert result2 == 3
    # Check that the side effect did not occur again (indicating the result was retrieved from the cache)
    assert side_effect == [3]


def test_cache_in_g_with_fallback_key(app):
    """Test cache_in_g decorator without a custom key."""

    side_effect = []

    @cache_in_g()
    def dummy_function(arg1, arg2, kwarg1=None):
        result = arg1 + arg2
        side_effect.append(result)  # Simulating a side effect
        return result

    # First call, not in cache
    result1 = dummy_function(1, 2)
    assert result1 == 3
    assert side_effect == [3]
    assert len(g._cache.values()) == 1
    assert list(g._cache.values())[0] == 3

    # Second call with the same arguments, should be retrieved from cache
    result2 = dummy_function(1, 2)
    assert result2 == 3
    # Check that the side effect did not occur again (indicating the result was retrieved from the cache)
    assert side_effect == [3]


def test_cache_in_g_with_fallback_key_and_kwarg(app):
    """Test cache_in_g decorator with a custom key and with kwargs."""

    side_effect = []

    @cache_in_g()
    def dummy_function(arg1, arg2, kwarg1=None):
        result = arg1 + arg2 + (kwarg1 or 0)
        side_effect.append(result)  # Simulating a side effect
        return result

    # First call, not in cache
    result1 = dummy_function(1, 2, kwarg1=3)
    assert result1 == 6
    assert side_effect == [6]
    assert len(g._cache.values()) == 1
    assert list(g._cache.values())[0] == 6

    # Second call with the same arguments, should be retrieved from cache
    result2 = dummy_function(1, 2, kwarg1=3)
    assert result2 == 6
    # Check that the side effect did not occur again (indicating the result was retrieved from the cache)
    assert side_effect == [6]
