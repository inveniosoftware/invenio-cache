# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

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
    src = os.path.join(os.path.dirname(__file__), 'template.html')
    dst = os.path.join(instance_path, 'templates/template.html')
    os.makedirs(os.path.dirname(dst))
    shutil.copy(src, dst)
    return os.path.dirname(dst)


@pytest.fixture()
def cache_config():
    """Generate cache configuration."""
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')
    config = {'CACHE_TYPE': CACHE_TYPE}

    if CACHE_TYPE == 'simple':
        pass
    elif CACHE_TYPE == 'redis':
        config.update(
            CACHE_REDIS_URL=os.environ.get(
                'CACHE_REDIS_URL', 'redis://localhost:6379/0')
        )
    elif CACHE_TYPE == 'memcached':
        config.update(
            CACHE_MEMCACHED_SERVERS=os.environ.get(
                'CACHE_MEMCACHED_SERVERS', 'localhost:11211').split(',')
        )
    return config


@pytest.fixture()
def base_app(instance_path, template_folder, cache_config):
    """Flask application fixture."""
    app_ = Flask(
        'testapp',
        instance_path=instance_path,
        template_folder=template_folder,
    )
    app_.config.update(
        SECRET_KEY='SECRET_KEY',
        TESTING=True,
    )
    print(cache_config)
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
    return base_app.extensions['invenio-cache']
