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

from invenio_cache import cached_unless_authenticated
from invenio_cache.decorators import cached_with_expiration


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
