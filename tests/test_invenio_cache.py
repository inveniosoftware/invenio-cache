# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from __future__ import absolute_import, print_function

import pkg_resources
import pytest
from flask import Flask
from mock import patch

from invenio_cache import (
    InvenioCache,
    cached_unless_authenticated,
    current_cache,
    current_cache_ext,
)
from invenio_cache.ext import _callback_factory


def test_version():
    """Test version import."""
    from invenio_cache import __version__

    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask("testapp")
    app.config.update(CACHE_TYPE="simple")
    ext = InvenioCache(app)
    assert "invenio-cache" in app.extensions

    app = Flask("testapp")
    app.config.update(CACHE_TYPE="simple")
    ext = InvenioCache()
    assert "invenio-cache" not in app.extensions
    ext.init_app(app)
    assert "invenio-cache" in app.extensions


def test_cache(app):
    """Test current cache proxy."""
    current_cache.set("mykey", "myvalue")
    assert current_cache.get("mykey") == "myvalue"


def test_current_cache(app):
    """Test current cache proxy."""
    current_cache.set("mykey", "myvalue")
    assert current_cache.get("mykey") == "myvalue"


def test_current_cache_ext(app):
    """Test current cache proxy."""
    assert app.extensions["invenio-cache"] == current_cache_ext._get_current_object()


def test_callback():
    """Test callback factory."""
    # Default (current_user from flask-login)
    assert _callback_factory(None) is not None
    # Custom callable
    assert _callback_factory(lambda: "custom")() == "custom"
    # Import string
    assert (
        _callback_factory("invenio_cache.cached_unless_authenticated")
        == cached_unless_authenticated
    )


@patch("pkg_resources.get_distribution")
def test_callback_no_login(get_distribution):
    """Test callback factory (no flask-login)."""
    get_distribution.side_effect = pkg_resources.DistributionNotFound
    assert _callback_factory(None)() is False


@pytest.mark.parametrize(
    "configs, db, expected_url",
    [
        (
            {
                "KV_CACHE_HOST": "testhost",
                "KV_CACHE_PORT": "6379",
                "KV_CACHE_PASSWORD": "testpassword",
                "KV_CACHE_PROTOCOL": "redis",
            },
            2,
            "redis://:testpassword@testhost:6379/2",
        ),
        (
            {
                "KV_CACHE_HOST": "testhost",
                "KV_CACHE_PORT": "6379",
                "KV_CACHE_PROTOCOL": "redis",
            },
            1,
            "redis://testhost:6379/1",
        ),
        (
            {"BROKER_URL": "redis://localhost:6379/0"},
            None,
            "redis://localhost:6379/0",
        ),
        (
            {"KV_CACHE_URL": "redis://localhost:6379/3"},
            3,
            "redis://localhost:6379/3",
        ),
        (
            {},
            4,
            "redis://localhost:6379/4",
        ),
    ],
)
def test_build_redis_url(configs, db, expected_url):
    """Test building Redis URL."""
    app = Flask("test_app")
    assert "CACHE_REDIS_URL" not in app.config
    app.config.update(configs)
    InvenioCache(app)
    assert app.config["CACHE_REDIS_URL"] == expected_url
