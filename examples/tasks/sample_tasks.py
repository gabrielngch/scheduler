from datetime import timedelta

from scheduler.decorators import schedule


@schedule(timedelta(seconds=10))
def hello_task() -> None:
    print("hello from scheduler")


@schedule(timedelta(seconds=15))
def second_task() -> None:
    print("second task ran")
