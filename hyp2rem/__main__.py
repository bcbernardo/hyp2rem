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


from datetime import datetime
from enum import Enum
from typing import Literal, Optional

import log  # type: ignore
from dotenv import load_dotenv
from typer import Option, Typer, echo

from hyp2rem.hyp2rem import Bridge
from hyp2rem.hypothesis.clients import HypothesisV1Client
from hyp2rem.remnote.clients import RemNoteV0Client

app = Typer()


class SortOption(str, Enum):
    """Sorting options supported by Hypothes.is API."""

    CREATED: Literal["created"] = "created"
    UPDATED: Literal["updated"] = "updated"


@app.command()
def main(  # type: ignore
    group: Optional[str] = Option(  # TODO: Accept multiple groups
        None,
        help="Name of the Hypothes.is group where annotations are stored",
        show_default=False,
    ),
    sort: SortOption = Option(
        SortOption.UPDATED,
        help="Metric to sort results by",
        case_sensitive=False,
    ),
    after: Optional[datetime] = Option(
        None,
        help="Search for annotations created ou updated after the given date",
    ),
    uri: Optional[str] = Option(
        None,
        help="A web page address (URL) or a URN representing another kind "
        + "of resource whose annotations should be synced.",
        show_default=False,
    ),
    hyp_key: str = Option(
        ...,
        envvar="HYP_KEY",
        prompt=True,
        help="API key for Hypothes.is account",
        show_default=False,
    ),
    rem_user: str = Option(
        ...,
        envvar="REM_USER",
        prompt=True,
        help="User ID for RemNote account",
        show_default=False,
    ),
    rem_key: str = Option(
        ...,
        envvar="REM_KEY",
        prompt=True,
        help="API key for RemNote account",
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
    # pylint: disable=too-many-locals

    # set verbosity levels and initialize logs
    verbosity: int = 1  # Errors and warnings (WARN) - Default
    if quiet:
        verbosity = 0  # Only errors (ERROR)
    elif verbose:
        verbosity = 2  # Errors, warnings and information (INFO)
    elif debug:
        verbosity = 3  # All possible output (DEBUG)
    log.reset()
    log.init(verbosity=verbosity)

    # set up Hypothes.is and RemNote connections
    hyp_client: HypothesisV1Client = HypothesisV1Client(
        group_name=group,
        sort=sort,
        order="asc",
        search_after=after,
        uri=uri,
        key=hyp_key,
    )
    rem_client: RemNoteV0Client = RemNoteV0Client(
        key=rem_key,
        user_id=rem_user,
    )

    # set up Bridge object between fetched annotations and RemNote
    bridge: Bridge = Bridge(hyp_client, rem_client)
    bridge.sync_all()
    if verbosity > 1:
        echo(bridge.stats)


if __name__ == "__main__":
    load_dotenv()
    app(prog_name="hyp2rem")
