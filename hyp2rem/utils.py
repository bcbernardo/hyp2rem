# Copyright 2020 The Hyp2Rem Authors

# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.


"""Helper classes and functions for handling Hypothes.is to RemNote connection.
"""

from enum import Enum
from typing import Literal

from requests.auth import AuthBase


class HTTPBearerAuth(AuthBase):
    """Bearer authentication scheme for use with Requests package."""

    def __init__(self, key: str):
        self.key = key

    def __call__(self, r):
        r.headers.update({"Authorization": "Bearer " + self.key})
        return r


class UpdatePolicy(Enum):
    """Update policies to choose from.

    Attributes:
        ALL: All target Rems will be updated when there are changes in the
            associated annotations, as will also be their parent Rems and
            and "older siblings" (Rems that come before it in the same
            hierarchicall level).
        SAFE: Only Rems that have not been modified manually after last sync
            will be updated, as will be their parent Rems and older siblings.
        SAFESTRICT: Only Rems that have not been modified manually after last
            sync will be updated. Parent Rems and older siblings will be left
            unchanged, even if they are updatable.
        FORBID: Allow no updates at all.
    """

    ALL: Literal["all"] = "all"
    SAFE: Literal["safe"] = "safe"
    STRICT: Literal["strict"] = "strict"
    SAFESTRICT: Literal["safestrict"] = "safestrict"
    FORBID: Literal["forbid"] = "forbid"
