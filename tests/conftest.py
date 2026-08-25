# SPDX-FileCopyrightText: 2017-2018 CERN.
# SPDX-FileCopyrightText: 2026 KTH Royal Institute of Technology.
# SPDX-License-Identifier: MIT

"""Pytest configuration."""

from __future__ import absolute_import, print_function

import os
import shutil
import tempfile

import pytest
from flask import Flask

from invenio_cache import InvenioCache, current_cache, current_cache_ext


@pytest.yield_fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.fixture()
def template_folder(instance_path):
    """Temporary instance path."""
    src = os.path.join(os.path.dirname(__file__), "template.html")
    dst = os.path.join(instance_path, "templates/template.html")
    os.makedirs(os.path.dirname(dst))
    shutil.copy(src, dst)
    return os.path.dirname(dst)


@pytest.fixture()
def cache_config():
    """Generate cache configuration."""
    CACHE_TYPE = os.environ.get("CACHE_TYPE", "SimpleCache")
    config = {"CACHE_TYPE": CACHE_TYPE}

    if CACHE_TYPE == "SimpleCache":
        pass
    elif CACHE_TYPE == "RedisCache":
        config.update(
            CACHE_REDIS_URL=os.environ.get(
                "CACHE_REDIS_URL", "redis://localhost:6379/0"
            )
        )
    elif CACHE_TYPE == "MemcachedCache":
        config.update(
            CACHE_MEMCACHED_SERVERS=os.environ.get(
                "CACHE_MEMCACHED_SERVERS", "localhost:11211"
            ).split(",")
        )
    return config


@pytest.fixture()
def base_app(instance_path, template_folder, cache_config):
    """Flask application fixture."""
    app_ = Flask(
        "testapp",
        instance_path=instance_path,
        template_folder=template_folder,
    )
    app_.config.update(
        SECRET_KEY="SECRET_KEY",
        TESTING=True,
    )
    app_.config.update(cache_config)
    InvenioCache(app_)
    return app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app


@pytest.fixture()
def ext(base_app):
    """Extension."""
    return base_app.extensions["invenio-cache"]
