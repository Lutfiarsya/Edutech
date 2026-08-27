from typing import Any

from openai import APIConnectionError, APITimeoutError, RateLimitError
from pydantic import TypeAdapter

from ai_worker.bootstrap import build_learning_assistant
from ai_worker.celery_app import celery_app, settings
from ai_worker.models import AIJobRequest

job_adapter = TypeAdapter(AIJobRequest)


@celery_app.task(
    bind=True,
    name="ai_worker.process_job",
    autoretry_for=(APIConnectionError, APITimeoutError, RateLimitError),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": settings.openai_max_retries},
)
def process_ai_job(self: Any, raw_job: dict[str, Any]) -> dict[str, Any]:
    job = job_adapter.validate_python(raw_job)
    result = build_learning_assistant().process(job)
    return {
        "type": job.type.value,
        "data": result.model_dump(mode="json"),
    }
