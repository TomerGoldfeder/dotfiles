#!/usr/bin/env python3
"""Opens the tab-panes picker popup.

This is the command behind the `open` action declared in herdr-plugin.toml.
It does no UI work itself -- it just asks herdr to launch the `picker` pane
entrypoint, which is already declared with placement = "popup" in the
manifest. herdr resolves the current tab/pane context for the popup from
whatever pane is active when this runs, so no context needs to be passed
explicitly.
"""
import os
import subprocess
import sys


def main() -> int:
    herdr = os.environ.get("HERDR_BIN_PATH", "herdr")
    plugin_id = os.environ.get("HERDR_PLUGIN_ID", "tomer.tab-panes")

    result = subprocess.run(
        [
            herdr, "plugin", "pane", "open",
            "--plugin", plugin_id,
            "--entrypoint", "picker",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        sys.stderr.write(result.stderr or "failed to open tab-panes picker\n")
        return result.returncode or 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
