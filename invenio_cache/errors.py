# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-Cache is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Invenio cache errors."""


class LockError(Exception):
    """Base error class for lock-related exceptions."""

    _description = "Base lock error."

    def __init__(self, lock, message=""):
        """Constructor, a lock can be passed to provide more details on the error."""
        self.lock = lock

    def __str__(self):
        """Return str(self)."""
        return f"Error on lock: {self.lock}: {self._description}"


class LockedError(LockError):
    """Lock is locked error."""

    _description = "Lock was not released yet."


class LockReleaseFailed(LockError):
    """Error when releasing the lock."""

    _description = "Lock failed to be released."


class LockAcquireFailed(LockError):
    """Error when acquiring the lock."""

    _description = "Lock failed to be acquired."


class LockRenewPermissionDenied(LockError):
    """Error when the renewal failed due to permissions."""

    _description = "Lock failed to be renewed due to lack of permissions."
