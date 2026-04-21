from __future__ import annotations

from collections.abc import Callable
from functools import update_wrapper
from types import SimpleNamespace
from typing import Any

try:
    from celery import Celery
except ModuleNotFoundError:
    Celery = None  # type: ignore[assignment]

from app.core.config import get_settings

settings = get_settings()

if Celery is None:

    class DeferredTask:
        def __init__(self, func: Callable[..., Any]) -> None:
            self.func = func
            update_wrapper(self, func)

        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            return self.func(*args, **kwargs)

        def delay(self, *_args: Any, **_kwargs: Any) -> Any:
            raise RuntimeError("Celery is not installed in this Python environment.")

    class DeferredCeleryApp:
        conf = SimpleNamespace(task_default_queue=None, task_track_started=False)

        def task(self, *_args: Any, **_kwargs: Any) -> Callable[[Callable[..., Any]], DeferredTask]:
            return DeferredTask

    celery_app = DeferredCeleryApp()
else:
    celery_app = Celery(
        "ops_agent",
        broker=settings.redis_url,
        backend=settings.redis_url,
        include=["app.tasks.processing"],
    )
    celery_app.conf.task_default_queue = settings.task_queue_name
    celery_app.conf.task_track_started = True
