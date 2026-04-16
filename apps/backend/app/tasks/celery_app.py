from __future__ import annotations

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ops_agent",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.processing"],
)
celery_app.conf.task_default_queue = settings.task_queue_name
celery_app.conf.task_track_started = True

