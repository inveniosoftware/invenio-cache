# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-Cache is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Invenio cache errors."""

from invenio_cache.lock import CachedMutex


class LockError(Exception):
    """Base error class for lock-related exceptions."""

    def __init__(self, lock):
        """Constructor, a lock can be passed to provide more details on the error."""
        self.lock = lock

    def __str__(self):
        """Return str(self)."""
        return f"Error on lock: {self.lock.lock_id}.  Created at: {self.lock.created}"


class LockedError(LockError):
    """Lock is locked error."""
