#!/usr/bin/env python3
"""Tab Panes picker.

Runs inside a herdr popup (see herdr-plugin.toml, entrypoint "picker").
Left column: every pane in the current tab. Right column: a live,
periodically-refreshed preview of whichever pane is selected.

Talks to herdr over its local Unix socket directly (newline-delimited JSON),
stdlib only -- no dependencies, matching herdr-bar's approach.

Keys:
  up/down, j/k     move selection
  enter            focus that pane in herdr, close the popup
  q, esc, ctrl+c   close the popup, change nothing
"""
from __future__ import annotations

import curses
import json
import os
import socket
import sys
import time
from dataclasses import dataclass, field

REFRESH_MS = 500          # how often the preview re-reads the selected pane
LIST_RESYNC_MS = 4000     # how often we re-fetch the tab's pane list
SOCKET_TIMEOUT_S = 2.0


# --------------------------------------------------------------------------
# herdr socket client
# --------------------------------------------------------------------------

class HerdrError(RuntimeError):
    pass


class HerdrClient:
    """Minimal newline-delimited JSON client for herdr's local socket."""

    def __init__(self) -> None:
        sock_path = os.environ.get("HERDR_SOCKET_PATH")
        if not sock_path:
            raise HerdrError("HERDR_SOCKET_PATH is not set -- not running inside herdr?")
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sock.settimeout(SOCKET_TIMEOUT_S)
        self._sock.connect(sock_path)
        self._buf = self._sock.makefile("rwb")
        self._req_id = 0

    def call(self, method: str, params: dict | None = None) -> dict:
        self._req_id += 1
        req = {"id": str(self._req_id), "method": method, "params": params or {}}
        self._buf.write((json.dumps(req) + "\n").encode("utf-8"))
        self._buf.flush()
        line = self._buf.readline()
        if not line:
            raise HerdrError(f"no response from herdr for {method}")
        resp = json.loads(line)
        if "error" in resp:
            raise HerdrError(f"{method}: {resp['error'].get('message', resp['error'])}")
        return resp.get("result", {})

    def close(self) -> None:
        try:
            self._sock.close()
        except OSError:
            pass


# --------------------------------------------------------------------------
# Data model
# --------------------------------------------------------------------------

@dataclass
class PaneRow:
    pane_id: str
    label: str | None
    cwd: str | None
    command: list[str] = field(default_factory=list)
    focused: bool = False

    @property
    def display_name(self) -> str:
        if self.label:
            return self.label
        if self.cwd:
            return os.path.basename(self.cwd.rstrip("/")) or self.cwd
        if self.command:
            return " ".join(self.command)
        return self.pane_id


def current_tab_id() -> str:
    tab_id = os.environ.get("HERDR_TAB_ID")
    if tab_id:
        return tab_id
    # Fallback: parse the fuller context blob if the env var is ever absent.
    ctx_raw = os.environ.get("HERDR_PLUGIN_CONTEXT_JSON")
    if ctx_raw:
        try:
            ctx = json.loads(ctx_raw)
            tab = ctx.get("tab") or {}
            tid = tab.get("tab_id") or ctx.get("tab_id")
            if tid:
                return tid
        except (json.JSONDecodeError, AttributeError):
            pass
    raise HerdrError("could not determine the current tab (no HERDR_TAB_ID)")


def _walk_layout(node: dict, out: list[PaneRow], focused_pane_id: str | None) -> None:
    """Recursively collect leaf pane nodes from a layout.export BSP tree."""
    if node is None:
        return
    node_type = node.get("type")
    if node_type == "pane":
        pane_id = node.get("pane_id")
        if pane_id:
            out.append(PaneRow(
                pane_id=pane_id,
                label=node.get("label"),
                cwd=node.get("cwd"),
                command=node.get("command") or [],
                focused=(pane_id == focused_pane_id),
            ))
    elif node_type == "split":
        _walk_layout(node.get("first"), out, focused_pane_id)
        _walk_layout(node.get("second"), out, focused_pane_id)


def fetch_tab_panes(client: HerdrClient, tab_id: str) -> list[PaneRow]:
    result = client.call("layout.export", {"tab_id": tab_id})
    root = result.get("root")
    focused_pane_id = result.get("focused_pane_id")
    rows: list[PaneRow] = []
    _walk_layout(root, rows, focused_pane_id)
    return rows


def read_pane_preview(client: HerdrClient, pane_id: str, lines: int) -> list[str]:
    try:
        result = client.call("pane.read", {
            "pane_id": pane_id,
            "source": "visible",
            "lines": lines,
        })
    except HerdrError as exc:
        return [f"(preview unavailable: {exc})"]
    if isinstance(result.get("lines"), list):
        return [str(l) for l in result["lines"]]
    text = result.get("text", "")
    return text.splitlines() if text else ["(empty)"]


def focus_pane(client: HerdrClient, pane_id: str) -> str | None:
    """Best-effort absolute focus. Returns an error string on failure, else None."""
    try:
        client.call("pane.focus", {"pane_id": pane_id})
        return None
    except HerdrError as exc:
        return str(exc)


# --------------------------------------------------------------------------
# UI
# --------------------------------------------------------------------------

def run(stdscr: "curses._CursesWindow") -> None:
    curses.curs_set(0)
    stdscr.nodelay(False)
    stdscr.timeout(REFRESH_MS)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)    # accent / selection
    curses.init_pair(2, curses.COLOR_BLACK, -1)   # muted (approx via dim)
    curses.init_pair(3, curses.COLOR_GREEN, -1)   # focused marker

    client = HerdrClient()
    tab_id = current_tab_id()

    panes = fetch_tab_panes(client, tab_id)
    if not panes:
        stdscr.addstr(0, 0, "No panes found in this tab.")
        stdscr.addstr(2, 0, "Press any key to close.")
        stdscr.refresh()
        stdscr.getch()
        return

    selected = 0
    preview_lines: list[str] = []
    last_list_sync = time.monotonic()
    last_preview_pane: str | None = None
    error_msg: str | None = None

    while True:
        height, width = stdscr.getmaxyx()
        list_width = max(24, min(40, width * 35 // 100))
        preview_width = width - list_width - 1
        body_height = height - 2  # leave room for header + footer

        # Periodic list resync (panes may open/close while popup is open).
        now = time.monotonic()
        if now - last_list_sync > LIST_RESYNC_MS / 1000:
            try:
                fresh = fetch_tab_panes(client, tab_id)
                if fresh:
                    current_id = panes[selected].pane_id if panes else None
                    panes = fresh
                    if current_id:
                        ids = [p.pane_id for p in panes]
                        selected = ids.index(current_id) if current_id in ids else 0
            except HerdrError as exc:
                error_msg = str(exc)
            last_list_sync = now

        selected = max(0, min(selected, len(panes) - 1))
        selected_pane = panes[selected]

        # Refresh preview when selection changed or on the refresh tick.
        if selected_pane.pane_id != last_preview_pane:
            preview_lines = read_pane_preview(client, selected_pane.pane_id, body_height)
            last_preview_pane = selected_pane.pane_id

        # ---- draw ----
        stdscr.erase()
        header = f" Tab panes ({len(panes)}) "
        stdscr.addstr(0, 0, header[:width], curses.A_BOLD)

        for i, pane in enumerate(panes):
            row = 1 + i
            if row >= body_height + 1:
                break
            marker = "●" if pane.focused else " "
            text = f"{marker} {i + 1}. {pane.display_name}"[:list_width - 1]
            attr = curses.A_REVERSE if i == selected else curses.A_NORMAL
            if pane.focused and i != selected:
                attr |= curses.color_pair(3)
            stdscr.addstr(row, 0, text.ljust(list_width - 1), attr)

        for r in range(body_height + 1):
            if r < height:
                stdscr.addstr(r, list_width, "│")

        preview_header = f" preview — {selected_pane.pane_id} "
        stdscr.addstr(0, list_width + 1, preview_header[:preview_width], curses.color_pair(1) | curses.A_BOLD)
        for i, line in enumerate(preview_lines[:body_height]):
            stdscr.addstr(1 + i, list_width + 1, line[:preview_width])

        footer = " ↑↓/jk move · enter focus · q close "
        if error_msg:
            footer = f" ! {error_msg} "[: width]
        stdscr.addstr(height - 1, 0, footer[:width], curses.A_DIM)

        stdscr.refresh()

        # ---- input ----
        try:
            ch = stdscr.getch()
        except curses.error:
            ch = -1

        if ch in (ord('q'), 27):  # q, esc
            break
        elif ch in (curses.KEY_UP, ord('k')):
            selected = (selected - 1) % len(panes)
            error_msg = None
        elif ch in (curses.KEY_DOWN, ord('j')):
            selected = (selected + 1) % len(panes)
            error_msg = None
        elif ch in (10, 13, curses.KEY_ENTER):
            err = focus_pane(client, selected_pane.pane_id)
            if err:
                error_msg = f"focus failed: {err}"
                continue
            break
        elif ch == 3:  # ctrl+c
            break

    client.close()


def main() -> int:
    try:
        curses.wrapper(run)
    except HerdrError as exc:
        sys.stderr.write(f"tab-panes: {exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
