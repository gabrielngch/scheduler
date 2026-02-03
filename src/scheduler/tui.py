from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import sqlite3
import time
from typing import Iterable

from rich.console import Console
from rich.table import Table


@dataclass(frozen=True)
class Summary:
    last_scan: int | None
    total_functions: int
    runs_last_24h: int
    failures_last_24h: int


def format_status_summary(
    *,
    last_scan: int | None,
    total_functions: int,
    runs_last_24h: int,
    failures_last_24h: int,
) -> str:
    last_scan_text = "n/a" if last_scan is None else _format_epoch(last_scan)
    return (
        f"Last scan: {last_scan_text} | Functions: {total_functions} | "
        f"Runs (24h): {runs_last_24h} | Failures (24h): {failures_last_24h}"
    )


def _format_epoch(value: int) -> str:
    return datetime.fromtimestamp(value, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _fetch_summary(conn: sqlite3.Connection) -> Summary:
    last_scan_row = conn.execute("SELECT MAX(last_discovered_at) FROM scheduled_functions").fetchone()
    last_scan = int(last_scan_row[0]) if last_scan_row and last_scan_row[0] is not None else None
    total_functions_row = conn.execute("SELECT COUNT(*) FROM scheduled_functions").fetchone()
    total_functions = int(total_functions_row[0]) if total_functions_row else 0

    since = int(time.time()) - 24 * 60 * 60
    runs_row = conn.execute(
        "SELECT COUNT(*) FROM run_logs WHERE started_at >= ?",
        (since,),
    ).fetchone()
    failures_row = conn.execute(
        "SELECT COUNT(*) FROM run_logs WHERE started_at >= ? AND status = 'failure'",
        (since,),
    ).fetchone()
    runs_last_24h = int(runs_row[0]) if runs_row else 0
    failures_last_24h = int(failures_row[0]) if failures_row else 0
    return Summary(
        last_scan=last_scan,
        total_functions=total_functions,
        runs_last_24h=runs_last_24h,
        failures_last_24h=failures_last_24h,
    )


def _fetch_recent_runs(conn: sqlite3.Connection, limit: int = 10) -> list[tuple]:
    cursor = conn.execute(
        """
        SELECT run_logs.started_at, run_logs.status, scheduled_functions.qualname
        FROM run_logs
        JOIN scheduled_functions ON run_logs.scheduled_function_id = scheduled_functions.id
        ORDER BY run_logs.started_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    return cursor.fetchall()


def _fetch_functions(conn: sqlite3.Connection) -> list[tuple]:
    cursor = conn.execute(
        """
        SELECT qualname, next_run_at, last_run_at
        FROM scheduled_functions
        ORDER BY qualname ASC
        """
    )
    return cursor.fetchall()


def render_once(conn: sqlite3.Connection, console: Console) -> None:
    summary = _fetch_summary(conn)
    console.clear()
    console.print(format_status_summary(
        last_scan=summary.last_scan,
        total_functions=summary.total_functions,
        runs_last_24h=summary.runs_last_24h,
        failures_last_24h=summary.failures_last_24h,
    ))

    functions_table = Table(title="Scheduled Functions")
    functions_table.add_column("Function")
    functions_table.add_column("Next Run")
    functions_table.add_column("Last Run")
    for qualname, next_run, last_run in _fetch_functions(conn):
        next_text = _format_epoch(next_run) if next_run else "n/a"
        last_text = _format_epoch(last_run) if last_run else "n/a"
        functions_table.add_row(str(qualname), next_text, last_text)
    if summary.total_functions == 0:
        functions_table.add_row("No scheduled functions discovered yet", "", "")
    console.print(functions_table)

    runs_table = Table(title="Recent Runs")
    runs_table.add_column("When")
    runs_table.add_column("Status")
    runs_table.add_column("Function")
    for started_at, status, qualname in _fetch_recent_runs(conn):
        runs_table.add_row(_format_epoch(started_at), status, str(qualname))
    if summary.runs_last_24h == 0:
        runs_table.add_row("n/a", "n/a", "No runs yet")
    console.print(runs_table)


def run_tui(conn: sqlite3.Connection, refresh_seconds: int) -> None:
    console = Console()
    while True:
        render_once(conn, console)
        time.sleep(refresh_seconds)
