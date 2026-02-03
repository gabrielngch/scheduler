from __future__ import annotations

from datetime import timedelta
from typing import Callable, TypeVar

TFunc = TypeVar("TFunc", bound=Callable[..., object])


def schedule(interval: timedelta) -> Callable[[TFunc], TFunc]:
    seconds = int(interval.total_seconds())

    def decorator(func: TFunc) -> TFunc:
        setattr(func, "__scheduler_interval_seconds__", seconds)
        return func

    return decorator
