from scheduler.cli import build_parser


def test_build_parser_defines_subcommands() -> None:
    parser = build_parser()
    subparsers = parser._subparsers  # type: ignore[attr-defined]
    assert subparsers is not None
    assert set(subparsers._group_actions[0].choices.keys()) == {"run", "scan", "tui"}


def test_module_main_exposes_main() -> None:
    import scheduler.__main__ as module

    assert callable(module.main)


def test_parser_accepts_config_after_subcommand(tmp_path):
    parser = build_parser()
    config_path = tmp_path / "scheduler.toml"
    args = parser.parse_args(["scan", "--config", str(config_path)])
    assert args.config == config_path


def test_scan_command_prints_discovered_count(tmp_path, capsys) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    module_path = tasks_dir / "sample.py"
    module_path.write_text(
        "from datetime import timedelta\n"
        "from scheduler.decorators import schedule\n\n"
        "@schedule(timedelta(seconds=10))\n"
        "def job():\n"
        "    return None\n",
        encoding="utf-8",
    )
    config_path = tmp_path / "scheduler.toml"
    config_path.write_text(
        "\n".join(
            [
                f"scan_paths = [\"{tasks_dir}\"]",
                "scan_interval_seconds = 60",
                "runner_poll_seconds = 5",
                f"db_path = \"{tmp_path / 'scheduler.db'}\"",
                "tui_refresh_seconds = 2",
            ]
        ),
        encoding="utf-8",
    )

    from scheduler.cli import main

    main(["scan", "--config", str(config_path)])
    captured = capsys.readouterr()
    assert "discovered 1 scheduled function" in captured.out


def test_global_config_flag_after_subcommand(tmp_path, capsys):
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    module_path = tasks_dir / "sample.py"
    module_path.write_text(
        "from datetime import timedelta\n"
        "from scheduler.decorators import schedule\n\n"
        "@schedule(timedelta(seconds=10))\n"
        "def job():\n"
        "    return None\n",
        encoding="utf-8",
    )
    config_path = tmp_path / "scheduler.toml"
    config_path.write_text(
        "\n".join(
            [
                f"scan_paths = [\"{tasks_dir}\"]",
                "scan_interval_seconds = 60",
                "runner_poll_seconds = 5",
                f"db_path = \"{tmp_path / 'scheduler.db'}\"",
                "tui_refresh_seconds = 2",
            ]
        ),
        encoding="utf-8",
    )

    from scheduler.cli import main

    main(["run", "--config", str(config_path), "--once"])
    captured = capsys.readouterr()
    assert "discovered 1 scheduled function" in captured.out
