from pathlib import Path
import time

from scheduler.db import (
    init_db,
    upsert_scheduled_function,
    record_run_log,
    fetch_due_functions,
)


def test_db_upsert_and_due_query(tmp_path: Path) -> None:
    db_path = tmp_path / "scheduler.db"
    conn = init_db(db_path)

    scheduled_id = upsert_scheduled_function(
        conn,
        module_path="/tmp/example.py",
        qualname="example.task",
        interval_seconds=60,
    )
    assert scheduled_id is not None

    future_epoch = int(time.time()) + 120
    due = fetch_due_functions(conn, now_epoch=future_epoch)
    assert len(due) == 1
    assert due[0].id == scheduled_id

    record_run_log(
        conn,
        scheduled_function_id=scheduled_id,
        started_at=0,
        finished_at=1,
        status="success",
        error_message=None,
    )
