from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from scheduler.config import load_config
from scheduler.db import init_db
from scheduler.runner import runner_loop
from scheduler.scanner import scan_paths
from scheduler.tui import run_tui


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scheduler")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("run", "Run the scheduler loops"),
        ("scan", "Scan for scheduled functions"),
        ("tui", "Launch the TUI"),
    ):
        subparser = subparsers.add_parser(name, help=help_text)
        subparser.add_argument(
            "--config",
            type=Path,
            default=Path("scheduler.toml"),
            help="Path to scheduler TOML config",
        )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config(args.config)
    conn = init_db(config.db_path)
    if args.command == "scan":
        discovered = scan_paths(conn, config.scan_paths)
        print(f"INFO: discovered {discovered} scheduled function(s)")
    elif args.command == "run":
        discovered = scan_paths(conn, config.scan_paths)
        print(f"INFO: discovered {discovered} scheduled function(s)")
        print("INFO: runner loop started")
        runner_loop(conn, config.runner_poll_seconds)
    elif args.command == "tui":
        run_tui(conn, config.tui_refresh_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
