# scheduler

A lightweight scheduler service that discovers Python functions in configured folders, runs them on a `datetime.timedelta` interval, and stores run history in SQLite. It ships with a simple TUI to monitor schedules and recent runs.

## Use case

Use this when you have Python functions (in your app or utility folders) that must run on a fixed interval and you want a self-contained service you can run alongside your app on a VM or container. You decorate functions with `@schedule(timedelta(...))`, point the scheduler at the folders, and it handles discovery and execution.

## Quick start (local dev)

For local development, the default docker-compose setup bind-mounts your current directory to `/host` inside the container so the scheduler can scan your host files without rebuilds.

From the directory that contains your projects (for example, your home directory that contains `scheduler`, `data pipeline app`, and `models`):

```bash
cd ~
cd scheduler
sudo docker compose up --build
```

The default config scans `/host`, which is your current working directory on the host.

## Configuration

The scheduler reads a TOML config file. By default it looks for `scheduler.toml`, or you can pass `--config`.

Example (`scheduler.toml`):

```toml
scan_paths = ["/host"]
scan_interval_seconds = 60
runner_poll_seconds = 5
db_path = "/host/scheduler.db"
tui_refresh_seconds = 2
```

- `scan_paths`: list of folders to scan recursively for `.py` files.
- `scan_interval_seconds`: how often to rescan for new decorated functions.
- `runner_poll_seconds`: how often to check for due jobs.
- `db_path`: SQLite database file path.
- `tui_refresh_seconds`: TUI refresh interval.

### Pointing to folders

Put any scheduled functions under one of the configured `scan_paths`. The scanner walks subfolders. Example function:

```python
from datetime import timedelta
from scheduler.decorators import schedule

@schedule(timedelta(minutes=5))
def refresh_cache():
    print("refreshing cache")
```

If you use the default docker-compose setup, everything under your current working directory is visible inside the container at `/host`, and the example config already scans `/host`.

## Running the scheduler

If you're using Docker (recommended for local dev with the bind mount), run:

```bash
sudo docker run --rm -v "$PWD:/host" scheduler:local run --config /host/examples/scheduler.toml
```

If you've installed the package locally (for example `pip install -e .`), you can run:

```bash
scheduler run --config /path/to/scheduler.toml
```

This will scan paths, then run due functions in a loop. On startup it logs how many functions were discovered.

## Using the TUI

The TUI reads the SQLite database and shows:
- last scan time
- number of scheduled functions
- runs and failures in the last 24h
- next run time per function
- recent run history

Run it in another terminal. Docker:

```bash
sudo docker run --rm -v "$PWD:/host" scheduler:local tui --config /host/examples/scheduler.toml
```

If installed locally:

```bash
scheduler tui --config /path/to/scheduler.toml
```

If no functions have been discovered yet, the TUI shows a clear empty-state message.

## Notes

- The scheduler runs functions in-process; if a function blocks, it will delay subsequent runs.
- SQLite is the single source of truth for schedules and run logs.
- Run logs and discovery errors are stored in the database for inspection in the TUI.
- For production, mount only the specific directories you want scanned instead of `/host`.
