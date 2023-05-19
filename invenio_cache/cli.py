# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2023 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Command Line Interface for invenio-cache."""

import click
from flask.cli import with_appcontext
from .proxies import current_cache

@click.group()
def cache():
    """Cache commands."""


@cache.command("clear")
@with_appcontext
def clear():
    """Clears cache."""
    current_cache.clear()
    click.secho('Cache cleared.', fg="green")

