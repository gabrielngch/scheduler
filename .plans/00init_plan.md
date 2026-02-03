# Scheduler Service with Decorator-Based Discovery (ExecPlan)

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows `/home/gabe/repos/scheduler/.agents/PLANS.md` and must be maintained in accordance with it.

## Purpose / Big Picture

The goal is to deliver a Dockerized Python service that discovers scheduled functions in configured folders, runs them on a `datetime.timedelta` interval, stores run history and statistics in SQLite, and offers a simple terminal user interface (TUI) to monitor those logs. After this change, a developer can add a `@schedule(timedelta(...))` decorator to any function in a scanned folder, start the scheduler container, and see those functions run on schedule with visible outcomes in the TUI.

## Progress

- [x] (2026-02-03 00:00Z) Drafted initial ExecPlan for the scheduler service and TUI.
- [x] (2026-02-03 00:35Z) Created baseline Python package layout, CLI entry point, and configuration loader.
- [x] (2026-02-03 00:35Z) Implemented schedule decorator metadata and scanning logic for configured folders (decorator only so far).
- [ ] Implement SQLite schema, runner loop, and run logging.
- [x] (2026-02-03 00:55Z) Implemented TUI for monitoring schedules and run logs.
- [x] (2026-02-03 01:20Z) Added Dockerfile, sample config, and example scheduled tasks with validation steps.
- [x] (2026-02-03 01:20Z) Wrote and ran tests that demonstrate behavior before and after changes.

## Surprises & Discoveries

- Observation: Initial tests failed because the `src/` package path was not on `sys.path` during pytest collection.
  Evidence: `ModuleNotFoundError: No module named 'scheduler'` during `uv run --extra dev pytest -q`.
- Observation: `fetch_due_functions` returned no rows when `now_epoch=0` because new schedules set `next_run_at` using the current time.
  Evidence: `assert len(due) == 1` failed in `tests/test_db.py` until the test used a future epoch.


## Decision Log

- Decision: Use SQLite as the single source of truth for schedules and run logs and store it as a local file configured by `db_path`.
  Rationale: SQLite keeps the system lightweight while enabling a queryable history for the TUI and reliable persistence across restarts.
  Date/Author: 2026-02-03, Codex.

- Decision: Use a `datetime.timedelta`-style decorator and store the interval in seconds as a function attribute.
  Rationale: This matches the user request and keeps scanning simple without requiring a global registry at import time.
  Date/Author: 2026-02-03, Codex.

- Decision: Keep configuration in a small TOML file parsed with the Python 3.11 standard library (`tomllib`).
  Rationale: TOML supports simple lists and numeric values without adding dependencies; Python 3.11 includes TOML parsing.
  Date/Author: 2026-02-03, Codex.

## Outcomes & Retrospective

Not started. This will be updated after milestones complete.

## Context and Orientation

The repository currently contains only `README.md` and no source code. This plan will introduce a Python package under `src/scheduler`, a command-line interface to run the scheduler and TUI, a SQLite database file on disk, and a Dockerfile to run the service in a container. The scheduler will scan configured folders recursively for Python files, import them, and look for functions decorated with `@schedule(timedelta(...))`. A scan is an operation that discovers scheduled functions and updates the database. A run is a single execution of a scheduled function triggered by the scheduler when it is due. The TUI is a text-based interface that reads the SQLite database and renders status on a terminal.

## Plan of Work

First, establish a minimal Python package layout with a CLI entry point so the service can be invoked as `scheduler run`, `scheduler scan`, and `scheduler tui`. Add a configuration loader that reads a TOML file containing `scan_paths`, `scan_interval_seconds`, `runner_poll_seconds`, `db_path`, and `tui_refresh_seconds`. Create a scheduler decorator in `src/scheduler/decorators.py` that marks a function with a numeric interval in seconds, derived from a `datetime.timedelta` argument.

Next, implement a scanner in `src/scheduler/scanner.py` that walks the configured folders recursively, loads each Python module by file path with `importlib`, and inspects module-level functions for the decorator attribute. The scanner should upsert each discovered function into SQLite with module path, qualified name, and interval. Scan errors should be captured and recorded in a `scan_errors` table with file path, error type, and message so failures do not abort the scan.

Then, implement SQLite persistence and a runner loop. Create a `src/scheduler/db.py` that initializes the schema and provides helper functions to insert and query scheduled functions and run logs. The runner loop in `src/scheduler/runner.py` should poll for due functions, execute them in-process, record `run_logs` entries with timing and status, and compute the next run time by adding the interval to the previous scheduled time. To avoid catch-up storms after downtime, if a function is overdue, execute it once and set `next_run_at` forward from the current time.

After that, implement a TUI in `src/scheduler/tui.py` using `rich`. The TUI should render a header summary (last scan, total scheduled functions, runs and failures in the last 24 hours), a table of scheduled functions with next run time and last status, and a panel of the most recent run logs. It should refresh on a timer and degrade gracefully when the database is empty.

Finally, add a Dockerfile that runs the CLI `scheduler run` with a mounted config and database, and add an `examples/` folder with a minimal example scheduled task and a sample `scheduler.toml`. Provide tests under `tests/` that validate decorator marking, scanning discovery, and runner scheduling behavior using a temporary SQLite database and temporary example modules. Ensure there is a documented validation flow that a novice can run end to end.

## Concrete Steps

All commands below are run from `/home/gabe/repos/scheduler`.

1. Create project scaffolding. Add `pyproject.toml` with a `scheduler` console script entry point, add `src/scheduler/__init__.py`, and a `src/scheduler/cli.py` that wires `run`, `scan`, and `tui` subcommands using `argparse`.

2. Implement configuration loader in `src/scheduler/config.py` that reads a TOML file, validates required keys, and applies environment variable overrides. Ensure the default config path is `scheduler.toml` in the current working directory.

3. Implement the decorator in `src/scheduler/decorators.py` with signature `schedule(interval: datetime.timedelta) -> Callable`. The decorator should set an attribute like `__scheduler_interval_seconds__` on the function and return the function.

4. Implement SQLite initialization and helpers in `src/scheduler/db.py`. The schema must include `scheduled_functions`, `run_logs`, and `scan_errors` tables. Ensure the database file is created on first run and migrations are idempotent.

5. Implement scanning logic in `src/scheduler/scanner.py`. Walk each configured scan path, load `.py` files, and inspect module-level callables for the interval attribute. Upsert into `scheduled_functions` and record scan errors without stopping the scan.

6. Implement the runner loop in `src/scheduler/runner.py`. Poll for due functions based on `next_run_at`, execute them, update `run_logs`, and compute the next run time. Add a `runner_poll_seconds` sleep between polls. Capture exceptions in the log.

7. Implement the TUI in `src/scheduler/tui.py` using `rich`. Read from SQLite, render summary and recent runs, and refresh according to `tui_refresh_seconds`.

8. Add `examples/` with a sample module using `@schedule(timedelta(...))` and a `scheduler.toml` that points to the example folder. Add a `Dockerfile` that installs the package and runs `scheduler run` by default.

9. Write tests under `tests/` using `pytest` that verify decorator metadata, scanner discovery on a temporary module, and runner scheduling logic with a temporary SQLite database.

10. Run the tests and document expected output. Then run the scheduler against the example config and show how the TUI displays the runs.

Expected command transcripts should look like this (examples, not exact output):

    $ python -m pytest -v
    ...
    3 passed in 0.42s

    $ python -m scheduler scan --config examples/scheduler.toml
    INFO: discovered 1 scheduled function

    $ python -m scheduler run --config examples/scheduler.toml
    INFO: runner loop started

## Validation and Acceptance

Validation requires both automated tests and a manual end-to-end run. Run `python -m pytest -v` and expect all tests to pass. Then run `python -m scheduler scan --config examples/scheduler.toml` and verify the scan reports at least one scheduled function. Start the scheduler with `python -m scheduler run --config examples/scheduler.toml` and observe log lines indicating function execution. Finally, run `python -m scheduler tui --config examples/scheduler.toml` and confirm that the TUI shows the function, its next run time, and a recent run log entry with status `success`. Acceptance is achieved when a scheduled function in the example folder executes on its interval and is visible in the TUI without errors.

## Idempotence and Recovery

All steps are safe to repeat. The scanner and runner can be restarted without data loss because SQLite persists state. If the database file becomes corrupt or needs a reset, delete the SQLite file specified by `db_path` and rerun the scanner to rebuild schedules. If a scan fails due to a bad module import, fix the module and rescan; scan errors should not prevent other modules from being processed.

## Artifacts and Notes

Include small, focused transcripts and key excerpts in this section as the implementation proceeds. For example, keep a short example of the TUI output or a sample run log entry to show the system is working.

Recent test run:

    $ uv run --extra dev pytest -q
    .............                                                            [100%]

Example scan run:

    $ UV_CACHE_DIR=/tmp/uv-cache PYTHONPATH=src uv run --extra dev python -m scheduler scan --config examples/scheduler.toml
    INFO: discovered 1 scheduled function(s)

## Interfaces and Dependencies

Use Python 3.11 for `tomllib` and `datetime.timedelta`. Use `rich` for the TUI rendering. Provide a CLI entry point named `scheduler` via `pyproject.toml` so the following interfaces exist: `scheduler run`, `scheduler scan`, and `scheduler tui`. Define a decorator `scheduler.decorators.schedule(interval: datetime.timedelta)` that attaches `__scheduler_interval_seconds__` to functions. Define database helper functions in `scheduler.db` to initialize schema, upsert scheduled functions, and insert run logs. Keep the SQLite schema stable and explicitly versioned in code so migrations are idempotent.

Plan Update Notes

- 2026-02-03: Marked initial scaffolding, config loader, and decorator tasks complete; added test run evidence and first discovery about import path during pytest.

Plan Update Notes

- 2026-02-03: Adjusted due-function tests to use a future epoch and set scanner qualname to file stem for stable display in logs/TUI.

Plan Update Notes

- 2026-02-03: Added TUI summary formatting and render loop with rich tables; added TUI summary test and verified full test suite.

Plan Update Notes

- 2026-02-03: Added Dockerfile, example config and tasks, CLI scan logging, and validation transcript for example scan; updated tests and CLI parsing to allow --config after subcommand.
