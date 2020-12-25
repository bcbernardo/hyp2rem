# Copyright 2020 The Hyp2Rem Authors

# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.


"""Test Hypothes.is to RemNote helper functions.

This module provides tests cases for syncing Hypothes.is annotations and
RemNote Rems.
"""

import json
import os

import log  # type: ignore

import hyp2rem.utils
from hyp2rem import hypothesis as hyp

HYP_KEY = os.environ["HYP_KEY"]
REM_KEY = os.environ["REM_KEY"]
REM_USER = os.environ["REM_USER"]

log.reset()
log.init(verbosity=3)


def test_document_for_source():
    """Test creating/getting RemNote documents for Hypothes.is source URIs."""
    group_id = hyp.get_group_by_name(HYP_KEY, "RemNote")["id"]
    annotations = hyp.get_annotations(HYP_KEY, group=group_id)
    for annotation in annotations:
        document_rem = hyp2rem.utils.document_for_source(
            REM_KEY,
            REM_USER,
            annotation=annotation,
        )
        log.debug(
            "Retrived document:" + json.dumps(document_rem.source, indent=4)
        )
        assert (
            annotation["target"][0]["source"] in document_rem.source[0]["url"]
        )
