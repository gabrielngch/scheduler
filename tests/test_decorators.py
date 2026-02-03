from datetime import timedelta

from scheduler.decorators import schedule


def test_schedule_sets_interval_seconds() -> None:
    @schedule(timedelta(hours=1, minutes=2))
    def sample_task() -> None:
        return None

    assert getattr(sample_task, "__scheduler_interval_seconds__") == 3720
