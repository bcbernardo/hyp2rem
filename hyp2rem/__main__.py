# Copyright 2020 The Hyp2Rem Authors

# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.


"""Command line interface to sync Hypothes.is and RemNote.

This module provides a command line utility that retrieves newly created or
updated annotations in a Hypothes.is group, compares them to existing Rem's in
a RemNote account, and uploads them.

Note:
    For this module to work, it is recommended that you store your credentials
    as environment variables. See the package documentation for more
    information.
"""


import json
from datetime import datetime
from enum import Enum
from typing import Optional

import log  # type: ignore
from typer import Option, Typer, echo

from hyp2rem import hypothesis as hyp

app = Typer()


class SortOption(str, Enum):
    """Sorting options supported by Hypothes.is API."""

    created: str = "created"
    updated: str = "updated"


@app.command()
def main(  # type: ignore
    hyp_group: Optional[str] = Option(
        None,
        help="Name of the Hypothes.is group where annotations are stored",
        show_default=False,
    ),
    sort: SortOption = Option(
        SortOption.created, help="Metric to sort results by"
    ),
    after: Optional[datetime] = Option(
        None,
        help="Search for annotations created ou updated after the given date",
    ),
    hyp_key: str = Option(
        ...,
        envvar="HYP_KEY",
        prompt=True,
        help="API key for Hypothes.is account",
        show_default=False,
    ),
    # rem_user: str = Option(
    #     ...,
    #     envvar="REM_USERID",
    #     prompt=True,
    #     help="User ID for RemNote account",
    #     show_default=False,
    # ),
    # rem_key: str = Option(
    #     ...,
    #     envvar="REM_KEY",
    #     prompt=True,
    #     help="API key for RemNote account",
    #     show_default=False,
    # ),
    uri: Optional[str] = Option(
        None,
        help="A web page address (URL) or a URN representing another kind "
        + "of resource such as DOI (Digital Object Identifier) or a PDF "
        + "fingerprint.",
        show_default=False,
    ),
    quiet: bool = Option(
        False,
        help="Silences the output printed to the terminal.",
    ),
    verbose: bool = Option(
        False,
        help="Increases the output printed to the terminal.",
    ),
    debug: bool = Option(
        False,
        help="Print every step to the terminal, for debugging purposes.",
    ),
):
    """
    Sync Hypothes.is annotations with Rem's in a RemNote account.
    """
    if quiet:
        verbosity: int = 0  # Only errors (ERROR)
    elif verbose:
        verbosity = 2  # Errors, warnings and information (INFO)
    elif debug:
        verbosity = 3  # All possible output (DEBUG)
    else:
        verbosity = 1  # Errors and warnings (WARN) - Default
    log.reset()
    log.init(verbosity=verbosity)
    # get group id, if a group name was provided
    group_id = None
    if hyp_group is not None:
        group = hyp.get_group_by_name(key=hyp_key, name=hyp_group)
        if group is not None:
            group_id = group["id"]
        else:
            log.error(
                "Group name was set, but not found in server. Cannot proceed."
            )
            raise ValueError
    # `after` option back to ISO string
    if isinstance(after, datetime):
        after = after.isoformat()  # type: ignore
    # fetch relevant annotations
    annotations = hyp.get_annotations(
        key=hyp_key,
        group=group_id,
        sort=sort,
        order="asc",
        search_after=after,
        uri=uri,
    )
    if verbosity > 2:
        echo(json.dumps(annotations))


if __name__ == "__main__":
    app(prog_name="hyp2rem")
