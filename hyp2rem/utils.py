# Copyright 2020 The Hyp2Rem Authors

# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or athy
# https://opensource.org/licenses/MIT.


"""Helper functions for Hypothes.is to RemNote connection logic.

This module provides helper functions for syncing Hypothes.is annotations and
RemNote Rems.
"""

from typing import Any, Mapping

import log  # type: ignore

from hyp2rem import remnote as rem
from hyp2rem.remnote import Rem


def document_for_source(
    rem_key: str,
    rem_user: str,
    annotation: Mapping[str, Any],
) -> Rem:
    """Fetch or create a document-level Rem for a annotated webpage or file."""
    source_base_uri = annotation["target"][0]["source"]
    source_uri = (
        "https://hyp.is/go?url="
        + source_base_uri
        + "&group="
        + annotation["group"]
    )
    source_title = annotation["document"]["title"][0]
    log.debug(
        "Checking whether there is already a document Rem for "
        + f"<{source_base_uri}>..."
    )
    document_rem = rem.get_rem_by_source(rem_key, rem_user, source_uri)
    if document_rem is None:
        log.debug("No existing Rem was found. Creating it...")
        document_rem_id = rem.create_rem(
            rem_key,
            rem_user,
            source=source_uri,
            text=source_title,
            is_document=True,
        )
        document_rem = rem.get_rem_by_id(rem_key, rem_user, document_rem_id)
        assert document_rem is not None
    log.debug(f"Retrieved document Rem with id '{document_rem.rem_id}'...")
    return document_rem
