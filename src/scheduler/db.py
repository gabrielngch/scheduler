from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
import time
from typing import Iterable


@dataclass(frozen=True)
class ScheduledFunction:
    id: int
    module_path: str
    qualname: str
    interval_seconds: int
    last_discovered_at: int
    enabled: int
    last_run_at: int | None
    next_run_at: int


def init_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS scheduled_functions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_path TEXT NOT NULL,
            qualname TEXT NOT NULL,
            interval_seconds INTEGER NOT NULL,
            last_discovered_at INTEGER NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            last_run_at INTEGER,
            next_run_at INTEGER NOT NULL,
            UNIQUE(module_path, qualname)
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS run_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scheduled_function_id INTEGER NOT NULL,
            started_at INTEGER NOT NULL,
            finished_at INTEGER NOT NULL,
            status TEXT NOT NULL,
            error_message TEXT,
            FOREIGN KEY (scheduled_function_id) REFERENCES scheduled_functions(id)
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS scan_errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            error_type TEXT NOT NULL,
            error_message TEXT NOT NULL,
            occurred_at INTEGER NOT NULL
        );
        """
    )
    conn.commit()
    return conn


def upsert_scheduled_function(
    conn: sqlite3.Connection,
    module_path: str,
    qualname: str,
    interval_seconds: int,
) -> int:
    now = int(time.time())
    next_run_at = now + interval_seconds
    cursor = conn.execute(
        """
        INSERT INTO scheduled_functions
            (module_path, qualname, interval_seconds, last_discovered_at, enabled, last_run_at, next_run_at)
        VALUES
            (?, ?, ?, ?, 1, NULL, ?)
        ON CONFLICT(module_path, qualname) DO UPDATE SET
            interval_seconds=excluded.interval_seconds,
            last_discovered_at=excluded.last_discovered_at,
            next_run_at=excluded.next_run_at
        RETURNING id;
        """,
        (module_path, qualname, interval_seconds, now, next_run_at),
    )
    row = cursor.fetchone()
    if row is None:
        raise RuntimeError("failed to upsert scheduled function")
    conn.commit()
    return int(row[0])


def record_run_log(
    conn: sqlite3.Connection,
    scheduled_function_id: int,
    started_at: int,
    finished_at: int,
    status: str,
    error_message: str | None,
) -> None:
    conn.execute(
        """
        INSERT INTO run_logs (scheduled_function_id, started_at, finished_at, status, error_message)
        VALUES (?, ?, ?, ?, ?)
        """,
        (scheduled_function_id, started_at, finished_at, status, error_message),
    )
    conn.commit()


def record_scan_error(
    conn: sqlite3.Connection,
    file_path: str,
    error_type: str,
    error_message: str,
) -> None:
    conn.execute(
        """
        INSERT INTO scan_errors (file_path, error_type, error_message, occurred_at)
        VALUES (?, ?, ?, ?)
        """,
        (file_path, error_type, error_message, int(time.time())),
    )
    conn.commit()


def fetch_due_functions(conn: sqlite3.Connection, now_epoch: int) -> list[ScheduledFunction]:
    cursor = conn.execute(
        """
        SELECT id, module_path, qualname, interval_seconds, last_discovered_at,
               enabled, last_run_at, next_run_at
        FROM scheduled_functions
        WHERE enabled = 1 AND next_run_at <= ?
        ORDER BY next_run_at ASC;
        """,
        (now_epoch,),
    )
    return [ScheduledFunction(*row) for row in cursor.fetchall()]


def list_scheduled_functions(conn: sqlite3.Connection) -> list[ScheduledFunction]:
    cursor = conn.execute(
        """
        SELECT id, module_path, qualname, interval_seconds, last_discovered_at,
               enabled, last_run_at, next_run_at
        FROM scheduled_functions
        ORDER BY qualname ASC;
        """
    )
    return [ScheduledFunction(*row) for row in cursor.fetchall()]
