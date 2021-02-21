# Copyright 2020 The Hyp2Rem Authors

# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""Exceptions for use in Hyp2Rem package and sub-packages."""


class ParentNotSyncedError(ValueError):
    """A Rem's parent is missing or is outdated."""

    def __init__(
        self,
        message: str = "Cannot create or update an annotation whose parent has"
        + "not been synced yet or is out-of-date.",
    ):
        self.message = message
        super().__init__(self.message)


class SiblingNotSyncedError(ValueError):
    """A Rem's older sibling is missing or outdated."""

    def __init__(
        self,
        message: str = "Cannot create or update an annotation whose older "
        + "sibling has not been synced yet or is out-of-date.",
    ):
        self.message = message
        super().__init__(self.message)


class MissingAuthorizationTokenError(TypeError):
    """Credentials for accessing a web service are not available."""

    def __init__(
        self,
        message: str = "Could not find one or more credentials required to"
        + "access the specified resource.",
    ):
        self.message = message
        super().__init__(self.message)
