from scheduler.tui import format_status_summary


def test_format_status_summary_empty() -> None:
    summary = format_status_summary(
        last_scan=None,
        total_functions=0,
        runs_last_24h=0,
        failures_last_24h=0,
    )
    assert "Last scan: n/a" in summary
    assert "Functions: 0" in summary
    assert "Runs (24h): 0" in summary
    assert "Failures (24h): 0" in summary
