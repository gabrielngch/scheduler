from __future__ import annotations

from pathlib import Path
import importlib.util
import inspect
import sys

from scheduler.db import record_scan_error, upsert_scheduled_function


def _load_module_from_path(path: Path):
    module_name = f"scheduled_{path.stem}_{abs(hash(path))}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def scan_paths(conn, scan_paths: list[Path]) -> int:
    discovered = 0
    for root in scan_paths:
        for file_path in root.rglob("*.py"):
            try:
                module = _load_module_from_path(file_path)
                for _, func in inspect.getmembers(module, inspect.isfunction):
                    interval = getattr(func, "__scheduler_interval_seconds__", None)
                    if interval is None:
                        continue
                    qualname = f"{file_path.stem}.{func.__name__}"
                    upsert_scheduled_function(
                        conn,
                        module_path=str(file_path),
                        qualname=qualname,
                        interval_seconds=int(interval),
                    )
                    discovered += 1
            except Exception as exc:
                record_scan_error(
                    conn,
                    file_path=str(file_path),
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                )
    return discovered
