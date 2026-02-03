from pathlib import Path
import time

from scheduler.db import init_db, upsert_scheduled_function, fetch_due_functions
from scheduler.runner import compute_next_run


def test_compute_next_run_advances_from_now_when_overdue() -> None:
    next_run = compute_next_run(now_epoch=100, previous_epoch=0, interval_seconds=30)
    assert next_run == 130


def test_runner_marks_due_function(tmp_path: Path) -> None:
    db_path = tmp_path / "scheduler.db"
    conn = init_db(db_path)
    scheduled_id = upsert_scheduled_function(
        conn,
        module_path="/tmp/example.py",
        qualname="example.task",
        interval_seconds=60,
    )

    future_epoch = int(time.time()) + 120
    due = fetch_due_functions(conn, now_epoch=future_epoch)
    assert [row.id for row in due] == [scheduled_id]
