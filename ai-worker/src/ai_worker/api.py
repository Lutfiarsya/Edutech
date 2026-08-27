from contextlib import closing
from typing import Any

from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException, status
from pydantic import TypeAdapter, ValidationError
from redis import Redis
from redis.exceptions import RedisError

from ai_worker.celery_app import celery_app
from ai_worker.config import get_settings
from ai_worker.logging_config import configure_logging
from ai_worker.models import (
    AIJobRequest,
    AIJobResult,
    HealthStatus,
    JobAccepted,
    JobStatus,
)
from ai_worker.tasks import job_adapter, process_ai_job

settings = get_settings()
configure_logging(settings.log_level)
result_adapter = TypeAdapter(AIJobResult)

app = FastAPI(
    title="Edutech AI Worker",
    version="0.1.0",
    description="Queues and tracks asynchronous AI learning jobs.",
)


@app.get("/health/live", response_model=HealthStatus, tags=["health"])
def liveness() -> HealthStatus:
    return HealthStatus(status="ok")


@app.get("/health/ready", response_model=HealthStatus, tags=["health"])
def readiness() -> HealthStatus:
    checks = {
        "openai_configured": settings.openai_api_key is not None,
        "redis": _redis_is_ready(),
    }
    if not all(checks.values()):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=HealthStatus(status="unavailable", checks=checks).model_dump(),
        )
    return HealthStatus(status="ok", checks=checks)


@app.post(
    "/v1/jobs",
    response_model=JobAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["jobs"],
)
def enqueue_job(job: AIJobRequest) -> JobAccepted:
    payload = job_adapter.dump_python(job, mode="json")
    task = process_ai_job.apply_async(
        args=[payload],
        queue=settings.celery_queue_name,
    )
    return JobAccepted(job_id=task.id)


@app.get("/v1/jobs/{job_id}", response_model=JobStatus, tags=["jobs"])
def get_job(job_id: str) -> JobStatus:
    task: AsyncResult = celery_app.AsyncResult(job_id)
    state = task.state

    if state == "SUCCESS":
        try:
            result = result_adapter.validate_python(task.result)
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="invalid_job_result",
            ) from exc
        return JobStatus(job_id=job_id, status="succeeded", result=result)

    if state in {"FAILURE", "REVOKED"}:
        return JobStatus(job_id=job_id, status="failed", error_code="job_failed")

    mapped_state = {
        "STARTED": "processing",
        "RETRY": "retrying",
    }.get(state, "queued")
    return JobStatus(job_id=job_id, status=mapped_state)


def _redis_is_ready() -> bool:
    try:
        client: Redis[Any] = Redis.from_url(
            settings.celery_broker_url,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        with closing(client):
            return bool(client.ping())
    except RedisError:
        return False
