#!/usr/bin/env python3
"""Tab Panes picker.

Runs inside a herdr popup (see herdr-plugin.toml, entrypoint "picker").
Left column: every pane in the current tab. Right column: a live,
periodically-refreshed preview of whichever pane is selected.

Talks to herdr over its local Unix socket directly (newline-delimited JSON),
stdlib only -- no dependencies, matching herdr-bar's approach.

Keys:
  up/down, j/k     move pane selection (list focus) or scroll preview (preview focus)
  tab, right, l    focus preview pane
  left, h          focus pane list
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
PREVIEW_FETCH_LINES = 2000  # pane.read recent cap (~999 lines returned)
SOCKET_TIMEOUT_S = 2.0

FOCUS_LIST = "list"
FOCUS_PREVIEW = "preview"


# --------------------------------------------------------------------------
# herdr socket client
# --------------------------------------------------------------------------

class HerdrError(RuntimeError):
    pass


class HerdrClient:
    """Minimal newline-delimited JSON client for herdr's local socket.

    Herdr serves one request per connection and closes after the response
    (events.subscribe is the exception). Open a fresh socket per call.
    """

    def __init__(self) -> None:
        sock_path = os.environ.get("HERDR_SOCKET_PATH")
        if not sock_path:
            raise HerdrError("HERDR_SOCKET_PATH is not set -- not running inside herdr?")
        self._sock_path = sock_path
        self._req_id = 0

    def call(self, method: str, params: dict | None = None) -> dict:
        self._req_id += 1
        req_id = str(self._req_id)
        payload = (json.dumps({
            "id": req_id,
            "method": method,
            "params": params or {},
        }) + "\n").encode("utf-8")

        line = b""
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(SOCKET_TIMEOUT_S)
        try:
            sock.connect(self._sock_path)
            sock.sendall(payload)
            with sock.makefile("rb") as reader:
                line = reader.readline()
        except BrokenPipeError as exc:
            raise HerdrError(
                f"{method}: herdr closed the socket before responding "
                f"(errno {exc.errno})"
            ) from exc
        except OSError as exc:
            raise HerdrError(f"{method}: {exc}") from exc
        finally:
            sock.close()

        if not line:
            raise HerdrError(f"no response from herdr for {method}")
        resp = json.loads(line)
        if "error" in resp:
            raise HerdrError(f"{method}: {resp['error'].get('message', resp['error'])}")
        return resp.get("result", {})

    def close(self) -> None:
        return


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


def layout_description(result: dict) -> dict:
    """layout.export returns {type: layout_export, layout: LayoutDescription}."""
    layout = result.get("layout")
    if isinstance(layout, dict):
        return layout
    return result


def fetch_tab_panes(client: HerdrClient, tab_id: str) -> list[PaneRow]:
    result = client.call("layout.export", {"tab_id": tab_id})
    layout = layout_description(result)
    root = layout.get("root")
    focused_pane_id = layout.get("focused_pane_id")
    rows: list[PaneRow] = []
    _walk_layout(root, rows, focused_pane_id)
    return rows


def preview_text(result: dict) -> str:
    """pane.read returns {type: pane_read, read: {text: ...}}."""
    read = result.get("read")
    if isinstance(read, dict):
        return str(read.get("text") or "")
    return str(result.get("text") or "")


def fetch_line_budget(body_height: int, preview_width: int) -> int:
    """Enough scrollback lines to fill the preview after wrapping."""
    return min(PREVIEW_FETCH_LINES, max(body_height * 3, 120))


def wrap_text_lines(lines: list[str], width: int) -> list[str]:
    """Hard-wrap logical lines to the preview column width."""
    if width <= 0:
        return list(lines)
    wrapped: list[str] = []
    for line in lines:
        if not line:
            wrapped.append("")
            continue
        for start in range(0, len(line), width):
            wrapped.append(line[start:start + width])
    return wrapped


def pad_viewport(rows: list[str], height: int) -> list[str]:
    """Bottom-align short previews so the panel is always filled."""
    if height <= 0:
        return []
    if len(rows) >= height:
        return rows[:height]
    return [""] * (height - len(rows)) + rows


def read_pane_preview(
    client: HerdrClient,
    pane_id: str,
    lines: int,
    *,
    source: str = "recent_unwrapped",
) -> list[str]:
    try:
        result = client.call("pane.read", {
            "pane_id": pane_id,
            "source": source,
            "lines": lines,
        })
    except HerdrError as exc:
        return [f"(preview unavailable: {exc})"]
    text = preview_text(result)
    return text.splitlines() if text else ["(empty)"]


def preview_scroll_max(line_count: int, viewport: int) -> int:
    return max(0, line_count - viewport)


def clamp_preview_scroll(scroll: int, line_count: int, viewport: int) -> int:
    return max(0, min(scroll, preview_scroll_max(line_count, viewport)))


def was_at_bottom(scroll: int, line_count: int, viewport: int) -> bool:
    return scroll >= preview_scroll_max(line_count, viewport)


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

def safe_addstr(win: "curses._CursesWindow", y: int, x: int, text: str, attr: int = 0) -> None:
    """Clip writes. curses raises if a write touches the bottom-right cell."""
    height, width = win.getmaxyx()
    if y < 0 or x < 0 or y >= height or x >= width or not text:
        return
    max_len = width - x
    if y == height - 1:
        max_len -= 1
    if max_len <= 0:
        return
    try:
        win.addstr(y, x, text[:max_len], attr)
    except curses.error:
        return


def hold_until_escape(stdscr: "curses._CursesWindow", lines: list[str]) -> None:
    """Leave the popup up. Timeout makes getch() return -1; only Escape closes."""
    stdscr.nodelay(False)
    stdscr.timeout(REFRESH_MS)
    while True:
        height, width = stdscr.getmaxyx()
        stdscr.erase()
        for i, line in enumerate(lines):
            if i >= height - 1:
                break
            safe_addstr(stdscr, i, 0, line, curses.A_BOLD if i == 0 else 0)
        if height > 0:
            safe_addstr(stdscr, height - 1, 0, "Press escape to close.", curses.A_DIM)
        stdscr.refresh()
        try:
            ch = stdscr.getch()
        except curses.error:
            ch = -1
        if ch == 27:
            return


def drain_input(stdscr: "curses._CursesWindow") -> None:
    """Drop keys already queued by the prefix chord, so Escape does not close immediately."""
    stdscr.nodelay(True)
    try:
        while True:
            ch = stdscr.getch()
            if ch == -1:
                return
    except curses.error:
        return
    finally:
        stdscr.nodelay(False)
        stdscr.timeout(REFRESH_MS)


def run(stdscr: "curses._CursesWindow") -> None:
    curses.curs_set(0)
    stdscr.nodelay(False)
    stdscr.timeout(REFRESH_MS)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)    # accent / selection
    curses.init_pair(2, curses.COLOR_BLACK, -1)   # muted (approx via dim)
    curses.init_pair(3, curses.COLOR_GREEN, -1)   # focused marker
    drain_input(stdscr)

    client = HerdrClient()
    tab_id = current_tab_id()

    try:
        panes = fetch_tab_panes(client, tab_id)
    except HerdrError as exc:
        hold_until_escape(stdscr, [
            "tab-panes failed to list panes",
            f"tab {tab_id}",
            str(exc),
        ])
        client.close()
        return
    if not panes:
        hold_until_escape(stdscr, [
            "No panes found in this tab.",
            f"tab {tab_id}",
        ])
        client.close()
        return

    selected = 0
    focus_area = FOCUS_LIST
    preview_lines: list[str] = []
    preview_scroll = 0
    preview_follow_bottom = True
    last_list_sync = time.monotonic()
    last_preview_pane: str | None = None
    last_preview_refresh = 0.0
    error_msg: str | None = None

    def load_preview_raw(
        body_height: int,
        preview_width: int,
        *,
        full_scrollback: bool,
        stick_bottom: bool,
    ) -> None:
        nonlocal preview_lines, preview_scroll, preview_follow_bottom
        nonlocal last_preview_pane, last_preview_refresh
        pane_id = panes[selected].pane_id
        old_wrapped = wrap_text_lines(preview_lines, preview_width)
        at_bottom = was_at_bottom(preview_scroll, len(old_wrapped), body_height)
        line_budget = (
            PREVIEW_FETCH_LINES
            if full_scrollback
            else fetch_line_budget(body_height, preview_width)
        )
        preview_lines = read_pane_preview(client, pane_id, line_budget)
        wrapped = wrap_text_lines(preview_lines, preview_width)
        if stick_bottom or at_bottom or preview_follow_bottom:
            preview_scroll = preview_scroll_max(len(wrapped), body_height)
            preview_follow_bottom = True
        else:
            preview_scroll = clamp_preview_scroll(preview_scroll, len(wrapped), body_height)
        last_preview_pane = pane_id
        last_preview_refresh = time.monotonic()

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

        pane_changed = selected_pane.pane_id != last_preview_pane
        if pane_changed:
            preview_follow_bottom = True
            load_preview_raw(
                body_height,
                preview_width,
                full_scrollback=(focus_area == FOCUS_PREVIEW),
                stick_bottom=True,
            )
        elif now - last_preview_refresh > REFRESH_MS / 1000:
            load_preview_raw(
                body_height,
                preview_width,
                full_scrollback=(focus_area == FOCUS_PREVIEW),
                stick_bottom=False,
            )

        wrapped_preview = wrap_text_lines(preview_lines, max(1, preview_width))
        if focus_area == FOCUS_LIST or preview_follow_bottom:
            preview_scroll = preview_scroll_max(len(wrapped_preview), body_height)
        else:
            preview_scroll = clamp_preview_scroll(
                preview_scroll, len(wrapped_preview), body_height,
            )
        visible_preview = pad_viewport(
            wrapped_preview[preview_scroll:preview_scroll + max(0, body_height)],
            body_height,
        )

        # ---- draw ----
        stdscr.erase()
        list_attr = curses.A_BOLD if focus_area == FOCUS_LIST else curses.A_DIM
        safe_addstr(stdscr, 0, 0, f" panes ({len(panes)}) {tab_id} ", list_attr)

        for i, pane in enumerate(panes):
            row = 1 + i
            if row >= height - 1 or row >= body_height + 1:
                break
            marker = "*" if pane.focused else " "
            text = f"{marker} {i + 1}. {pane.display_name}"
            attr = curses.A_NORMAL
            if focus_area == FOCUS_LIST and i == selected:
                attr = curses.A_REVERSE
            elif pane.focused:
                attr |= curses.color_pair(3)
            safe_addstr(stdscr, row, 0, text.ljust(max(1, list_width - 1)), attr)

        divider_attr = curses.A_BOLD if focus_area == FOCUS_PREVIEW else curses.A_DIM
        for r in range(max(0, min(body_height + 1, height - 1))):
            safe_addstr(stdscr, r, list_width, "|", divider_attr)

        scroll_hint = ""
        if focus_area == FOCUS_PREVIEW and len(wrapped_preview) > body_height:
            top = preview_scroll + 1
            bottom = min(preview_scroll + body_height, len(wrapped_preview))
            scroll_hint = f" {top}-{bottom}/{len(wrapped_preview)} "
        preview_header = f" preview{scroll_hint} {selected_pane.pane_id} "
        preview_header_attr = curses.color_pair(1) | curses.A_BOLD
        if focus_area == FOCUS_PREVIEW:
            preview_header_attr |= curses.A_REVERSE
        safe_addstr(stdscr, 0, list_width + 1, preview_header, preview_header_attr)
        for i, line in enumerate(visible_preview):
            safe_addstr(stdscr, 1 + i, list_width + 1, line)

        if focus_area == FOCUS_PREVIEW:
            footer = " j/k scroll · h/list · enter focus · q close "
        else:
            footer = " j/k panes · tab/l preview · enter focus · q close "
        if error_msg:
            footer = f" ! {error_msg} "
        safe_addstr(stdscr, height - 1, 0, footer, curses.A_DIM)

        stdscr.refresh()

        # ---- input ----
        try:
            ch = stdscr.getch()
        except curses.error:
            ch = -1

        if ch in (ord('q'), 27):  # q, esc
            break
        elif ch in (9, curses.KEY_RIGHT, ord('l')):  # tab, right, l
            if focus_area != FOCUS_PREVIEW:
                focus_area = FOCUS_PREVIEW
                preview_follow_bottom = True
                load_preview_raw(
                    body_height, preview_width,
                    full_scrollback=True, stick_bottom=True,
                )
                error_msg = None
        elif ch in (curses.KEY_LEFT, ord('h')):
            if focus_area == FOCUS_PREVIEW:
                focus_area = FOCUS_LIST
                preview_follow_bottom = True
                load_preview_raw(
                    body_height, preview_width,
                    full_scrollback=False, stick_bottom=True,
                )
                error_msg = None
        elif ch in (curses.KEY_UP, ord('k')):
            if focus_area == FOCUS_PREVIEW:
                wrapped_count = len(wrap_text_lines(preview_lines, max(1, preview_width)))
                preview_scroll = clamp_preview_scroll(
                    preview_scroll - 1, wrapped_count, body_height,
                )
                preview_follow_bottom = was_at_bottom(
                    preview_scroll, wrapped_count, body_height,
                )
            else:
                selected = (selected - 1) % len(panes)
            error_msg = None
        elif ch in (curses.KEY_DOWN, ord('j')):
            if focus_area == FOCUS_PREVIEW:
                wrapped_count = len(wrap_text_lines(preview_lines, max(1, preview_width)))
                preview_scroll = clamp_preview_scroll(
                    preview_scroll + 1, wrapped_count, body_height,
                )
                preview_follow_bottom = was_at_bottom(
                    preview_scroll, wrapped_count, body_height,
                )
            else:
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


def _run_guarded(stdscr: "curses._CursesWindow") -> None:
    try:
        run(stdscr)
    except Exception as exc:
        hold_until_escape(stdscr, [
            "tab-panes crashed",
            f"{type(exc).__name__}: {exc}",
        ])


def main() -> int:
    try:
        curses.wrapper(_run_guarded)
    except Exception as exc:
        sys.stderr.write(f"tab-panes: {exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
