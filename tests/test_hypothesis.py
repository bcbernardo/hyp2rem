# Copyright 2020 The Hyp2Rem Authors

# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.


"""Test Hypothes.is connection logic.

This module provides tests cases for Hypothes.is API interfaces in hyp2rem
package.
"""

import os
from typing import Any, Mapping, Sequence, Union

import log  # type: ignore

from hyp2rem import hypothesis as hyp

HYP_KEY = os.environ["HYP_KEY"]


log.init(verbosity=4)


def test_get_group_by_name() -> None:
    """Try to get a group by its name and check returned value.

    Note:
        You must have a group named `RemNote` (case-sensitive) in your account
        before running the test, for this to work.
    """
    group_name: str = "RemNote"
    remnote_group: Union[Mapping[str, Any], None] = hyp.get_group_by_name(
        HYP_KEY,
        group_name,
    )
    assert remnote_group["name"] == group_name  # type: ignore


def test_get_annotations() -> None:
    """Try to fetch public annotations for the Hypothes.is 'Quick Start Guide'."""
    quick_start_uri: str = "https://web.hypothes.is/help/quick-start-guide/"
    quick_start_annotations: Sequence[Mapping[str, Any]] = hyp.get_annotations(
        key=HYP_KEY,
        uri=quick_start_uri,
    )
    # NOTE: 7 is the number of annotations the page had in 2020-12-12
    assert len(quick_start_annotations) >= 7
    # OPTIONAL: print(quick_start_annotations)
