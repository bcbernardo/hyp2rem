# pylint: disable=redefined-outer-name

# Copyright 2020 The Hyp2Rem Authors

# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.


"""Test RemNote connection logic.

This module provides tests cases for RemNote API interfaces in hyp2rem
package.
"""

import os
from typing import Generator

import log  # type: ignore
import pytest

from hyp2rem import remnote

REM_KEY = os.environ["REM_KEY"]
REM_USER = os.environ["REM_USER"]

log.init(verbosity=4)


@pytest.fixture(scope="module")
def example_rem_id() -> Generator[str, None, None]:
    """Generate a Rem, yield its Id for use in other tests, and delete it."""
    rem_id = remnote.create_rem(
        REM_KEY, REM_USER, text="Testing:: create [[Rem]]", is_document=True
    )
    yield rem_id
    # !!!
    # BUG: won't work. '500 Internal server error'
    # remnote.delete_rem(REM_KEY, REM_USER, rem_id)


def test_get_rem_by_id(example_rem_id) -> None:
    """Test getting a Rem by its Id."""
    rem = remnote.get_rem_by_id(REM_KEY, REM_USER, example_rem_id)
    assert rem is not None
    print(rem.name_md + ":: " + rem.content_md)
    assert rem.name_md == "Testing"
    assert "create " in rem.content


def test_get_rem_by_name(example_rem_id) -> None:
    """Test getting a Rem by its Id."""
    rem = remnote.get_rem_by_name(REM_KEY, REM_USER, "Testing")
    assert rem is not None
    print(rem.name_md + ":: " + rem.content_md)
    # BUG: will fail when running test for the second time, as deletion is not
    # working. Must delete created Rems manually.
    assert rem.rem_id == example_rem_id
    assert "create " in rem.content


def test_update_rem(example_rem_id) -> None:
    """Test updating a Rem."""
    rem_id = remnote.update_rem(
        REM_KEY, REM_USER, example_rem_id, content="update [[Rem]]"
    )
    assert rem_id == example_rem_id
    rem = remnote.get_rem_by_id(REM_KEY, REM_USER, example_rem_id)
    assert rem is not None
    assert "update " in rem.content
