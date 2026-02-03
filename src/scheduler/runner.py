from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path
import time

from scheduler.db import fetch_due_functions, record_run_log


@dataclass(frozen=True)
class RunResult:
    status: str
    error_message: str | None


def _load_callable(module_path: str, qualname: str):
    path = Path(module_path)
    module_name = f"run_{path.stem}_{abs(hash(module_path))}"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    target_name = qualname.split(".")[-1]
    return getattr(module, target_name)


def compute_next_run(now_epoch: int, previous_epoch: int | None, interval_seconds: int) -> int:
    base = now_epoch if previous_epoch is None or previous_epoch < now_epoch else previous_epoch
    return base + interval_seconds


def run_due(conn) -> int:
    now_epoch = int(time.time())
    due = fetch_due_functions(conn, now_epoch=now_epoch)
    run_count = 0
    for scheduled in due:
        started = int(time.time())
        try:
            func = _load_callable(scheduled.module_path, scheduled.qualname)
            func()
            result = RunResult(status="success", error_message=None)
        except Exception as exc:
            result = RunResult(status="failure", error_message=str(exc))
        finished = int(time.time())
        record_run_log(
            conn,
            scheduled_function_id=scheduled.id,
            started_at=started,
            finished_at=finished,
            status=result.status,
            error_message=result.error_message,
        )
        next_run = compute_next_run(now_epoch=now_epoch, previous_epoch=scheduled.next_run_at, interval_seconds=scheduled.interval_seconds)
        conn.execute(
            """
            UPDATE scheduled_functions
            SET last_run_at = ?, next_run_at = ?
            WHERE id = ?
            """,
            (finished, next_run, scheduled.id),
        )
        conn.commit()
        run_count += 1
    return run_count


def runner_loop(conn, poll_seconds: int) -> None:
    while True:
        run_due(conn)
        time.sleep(poll_seconds)
