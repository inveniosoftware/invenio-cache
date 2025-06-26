# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
# Copyright (C) 2025 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from __future__ import absolute_import, print_function

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


@patch("builtins.__import__")
def test_callback_no_login(mock_import):
    """Test callback factory (no flask-login)."""

    # Mock ImportError when trying to import flask_login
    def side_effect(name, *args, **kwargs):
        if name == "flask_login":
            raise ImportError("No module named 'flask_login'")
        return __import__(name, *args, **kwargs)

    mock_import.side_effect = side_effect
    assert _callback_factory(None)() is False
