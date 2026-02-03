from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import tomllib


@dataclass(frozen=True)
class Config:
    scan_paths: list[Path]
    scan_interval_seconds: int
    runner_poll_seconds: int
    db_path: Path
    tui_refresh_seconds: int


_REQUIRED_KEYS = {
    "scan_paths",
    "scan_interval_seconds",
    "runner_poll_seconds",
    "db_path",
    "tui_refresh_seconds",
}


def _apply_env_overrides(data: dict) -> dict:
    overrides = {
        "SCAN_PATHS": "scan_paths",
        "SCAN_INTERVAL_SECONDS": "scan_interval_seconds",
        "RUNNER_POLL_SECONDS": "runner_poll_seconds",
        "DB_PATH": "db_path",
        "TUI_REFRESH_SECONDS": "tui_refresh_seconds",
    }
    for env_key, config_key in overrides.items():
        if env_key in os.environ:
            value = os.environ[env_key]
            if config_key == "scan_paths":
                data[config_key] = [Path(p) for p in value.split(":") if p]
            elif config_key == "db_path":
                data[config_key] = Path(value)
            else:
                data[config_key] = int(value)
    return data


def load_config(path: Path) -> Config:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    raw = _apply_env_overrides(raw)
    missing = sorted(_REQUIRED_KEYS - raw.keys())
    if missing:
        raise ValueError("missing required config keys: " + ", ".join(missing))

    scan_paths = [Path(p) for p in raw["scan_paths"]]
    return Config(
        scan_paths=scan_paths,
        scan_interval_seconds=int(raw["scan_interval_seconds"]),
        runner_poll_seconds=int(raw["runner_poll_seconds"]),
        db_path=Path(raw["db_path"]),
        tui_refresh_seconds=int(raw["tui_refresh_seconds"]),
    )
