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

"""Cache module for Invenio."""

from __future__ import absolute_import, print_function

import pkg_resources
from flask_caching import Cache
from werkzeug.utils import import_string

from . import config
from ._compat import string_types


class InvenioCache(object):
    """Invenio-Cache extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        self.cache = Cache(app)
        self.is_authenticated_callback = _callback_factory(
            app.config['CACHE_IS_AUTHENTICATED_CALLBACK'])
        app.extensions['invenio-cache'] = self

    def init_config(self, app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith('CACHE_'):
                app.config.setdefault(k, getattr(config, k))


def _callback_factory(callback_imp):
    """Factory for creating a is authenticated callback."""
    if callback_imp is None:
        try:
            pkg_resources.get_distribution('flask-login')
            from flask_login import current_user
            return lambda: current_user.is_authenticated
        except pkg_resources.DistributionNotFound:
            return lambda: False
    elif isinstance(callback_imp, string_types):
        return import_string(callback_imp)
    else:
        return callback_imp
