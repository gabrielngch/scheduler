from pathlib import Path

from scheduler.config import load_config


def test_example_config_points_to_examples(tmp_path: Path) -> None:
    config_text = (
        "scan_paths = [\"examples/tasks\"]\n"
        "scan_interval_seconds = 60\n"
        "runner_poll_seconds = 5\n"
        "db_path = \"scheduler.db\"\n"
        "tui_refresh_seconds = 2\n"
    )
    config_path = tmp_path / "scheduler.toml"
    config_path.write_text(config_text, encoding="utf-8")

    config = load_config(config_path)

    assert Path("examples/tasks") in config.scan_paths
