from datetime import timedelta

from scheduler.decorators import schedule


@schedule(timedelta(seconds=10))
def hello_task() -> None:
    print("hello from scheduler")

