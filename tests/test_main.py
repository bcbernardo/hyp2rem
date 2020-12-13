# Copyright 2020 The Hyp2Rem Authors

# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.


"""Test the Hypothes.is to RemNote Command Line Interface.

This module provides test cases for the command line utility that syncs
Hypothes.is and RemNote web apps.
"""

import log  # type: ignore
from typer.testing import CliRunner

from hyp2rem.__main__ import app

log.init(verbosity=3)

runner = CliRunner()


def test_app() -> None:
    """Test CLI basic functionality.

    Note:
        This test considers that you have already added your Hypothes-is and
        RemNote credentials to your environment (see documentation) and also
        that you have an annotation group called "RemNote" (case-sensitive)
        with some annotations on it.
    """
    result = runner.invoke(
        app,
        [
            "--hyp-group",
            "RemNote",
            "--debug",
        ],
    )
    assert result.exit_code == 0
    assert '"id": "' in result.stdout
