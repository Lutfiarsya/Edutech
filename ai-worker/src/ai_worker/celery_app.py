from celery import Celery

from ai_worker.config import get_settings
from ai_worker.logging_config import configure_logging

settings = get_settings()
configure_logging(settings.log_level)

celery_app = Celery(
    "edutech_ai_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["ai_worker.tasks"],
)
celery_app.conf.update(
    broker_connection_retry_on_startup=True,
    result_expires=settings.job_result_expires_seconds,
    task_default_queue=settings.celery_queue_name,
    task_acks_late=True,
    task_ignore_result=False,
    task_reject_on_worker_lost=True,
    task_serializer="json",
    task_soft_time_limit=settings.job_soft_time_limit_seconds,
    task_time_limit=settings.job_time_limit_seconds,
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    worker_prefetch_multiplier=1,
    timezone="UTC",
    enable_utc=True,
)
