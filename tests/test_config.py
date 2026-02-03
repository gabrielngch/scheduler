from pathlib import Path

import pytest

from scheduler.config import Config, load_config


def test_load_config_reads_toml(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "tasks"
    db_path = tmp_path / "scheduler.db"
    config_path = tmp_path / "scheduler.toml"
    config_path.write_text(
        "\n".join(
            [
                "scan_paths = [\"%s\"]" % tasks_dir,
                "scan_interval_seconds = 60",
                "runner_poll_seconds = 5",
                "db_path = \"%s\"" % db_path,
                "tui_refresh_seconds = 2",
                "",
            ]
        ),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert isinstance(config, Config)
    assert config.scan_paths == [tasks_dir]
    assert config.scan_interval_seconds == 60
    assert config.runner_poll_seconds == 5
    assert config.db_path == db_path
    assert config.tui_refresh_seconds == 2


def test_load_config_requires_all_keys(tmp_path: Path) -> None:
    config_path = tmp_path / "scheduler.toml"
    config_path.write_text("scan_paths = []\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required config keys"):
        load_config(config_path)
