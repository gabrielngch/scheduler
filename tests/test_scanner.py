from pathlib import Path

from scheduler.db import init_db, list_scheduled_functions
from scheduler.scanner import scan_paths


def test_scan_paths_discovers_decorated_function(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    module_path = tasks_dir / "sample.py"
    module_path.write_text(
        "from datetime import timedelta\n"
        "from scheduler.decorators import schedule\n\n"
        "@schedule(timedelta(seconds=30))\n"
        "def job():\n"
        "    return 'ok'\n",
        encoding="utf-8",
    )

    db_path = tmp_path / "scheduler.db"
    conn = init_db(db_path)

    discovered = scan_paths(conn, [tasks_dir])

    scheduled = list_scheduled_functions(conn)
    assert len(scheduled) == 1
    assert scheduled[0].qualname.endswith("sample.job")
    assert scheduled[0].interval_seconds == 30
    assert discovered == 1
