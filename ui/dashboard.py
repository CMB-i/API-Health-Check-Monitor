"""
ui/dashboard.py
===============
Rich-powered dashboard renderer.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from rich import box
from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _status_cell(is_up: bool, error: str | None) -> Text:
    """Return a coloured, decorated ``Text`` object for the *status* column."""
    if is_up:
        return Text("[  OK  ]  UP", style="bold green")
    if error and "timeout" in error.lower():
        return Text("[ WAIT ]  TIMEOUT", style="bold yellow")
    # ERROR or anything unexpected
    return Text("[ FAIL ]  DOWN", style="bold red")


def _latency_cell(latency_ms: float, is_up: bool) -> Text:
    """Colour-code latency: green < 300 ms, yellow < 1 000 ms, red otherwise."""
    if not is_up:
        return Text("—", style="dim")
    if latency_ms < 300:
        colour = "green"
    elif latency_ms < 1000:
        colour = "yellow"
    else:
        colour = "red"
    return Text(f"{latency_ms:>8.2f}", style=colour, justify="right")


def _http_code_cell(http_status: int | None) -> Text:
    """Render the raw HTTP status code or a dash when unavailable."""
    if http_status is None:
        return Text("—", style="dim")
    if 200 <= http_status < 300:
        return Text(str(http_status), style="green")
    if 300 <= http_status < 400:
        return Text(str(http_status), style="cyan")
    if 400 <= http_status < 500:
        return Text(str(http_status), style="yellow")
    return Text(str(http_status), style="red")


def _format_timestamp(iso_ts: str) -> str:
    """Convert a UTC ISO-8601 timestamp to a local HH:MM:SS string."""
    try:
        dt_utc = datetime.fromisoformat(iso_ts)
        dt_local = dt_utc.astimezone()  # Convert to local timezone
        return dt_local.strftime("%H:%M:%S")
    except ValueError:
        return iso_ts


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_table(results: list[dict[str, Any]], cycle: int) -> Table:
    """
    Build and return a ``rich.table.Table`` for health-check results.
    """
    # ── Table skeleton ──────────────────────────────────────────────────────
    table = Table(
        title=f"API Health Monitor  •  Cycle #{cycle}",
        title_style="bold bright_cyan",
        caption=f"Last refresh: {datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M:%S')}",
        caption_style="dim italic",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        show_lines=False,
        expand=False,
        highlight=True,
    )

    # ── Column definitions ───────────────────────────────────────────────────
    table.add_column("API Name", style="bold white", min_width=20, ratio=3)
    table.add_column("Status", min_width=16, ratio=2)
    table.add_column("HTTP Code", justify="center", min_width=10, ratio=1)
    table.add_column("Latency (ms)", justify="right", min_width=12, ratio=1)
    table.add_column("Checked At", justify="center", min_width=10, ratio=1)

    # ── Rows ─────────────────────────────────────────────────────────────────
    now_utc_iso = datetime.now(timezone.utc).isoformat()
    for result in results:
        table.add_row(
            result.get("name", "N/A"),
            _status_cell(result.get("is_up", False), result.get("error")),
            _http_code_cell(result.get("status_code")),
            _latency_cell(result.get("latency_ms", 0), result.get("is_up", False)),
            _format_timestamp(now_utc_iso),
        )

    return table


def build_startup_panel() -> Panel:
    """Return a simple 'starting up…' panel shown before the first check."""
    msg = Align.center(
        Text("Initialising... first check in progress", style="bold yellow"),
        vertical="middle",
    )
    return Panel(msg, border_style="yellow", title="API Health Monitor")


async def dashboard_loop(
    results_provider: Callable[[], Awaitable[list[dict[str, Any]]]],
    interval: int = 5,
) -> None:
    """
    results_provider: async function that returns results list
    interval: refresh time in seconds
    """
    cycle = 0
    with Live(
        build_startup_panel(),
        console=console,
        refresh_per_second=4,
        auto_refresh=True,
        vertical_overflow="crop",
    ) as live:
        while True:
            try:
                results = await results_provider()
                cycle += 1
                table = build_table(results, cycle)
                live.update(table)
            except Exception as e:
                error_table = Table(title="Dashboard Error", box=box.ROUNDED)
                error_table.add_column("Error")
                error_table.add_row(str(e))
                live.update(error_table)

            await asyncio.sleep(interval)