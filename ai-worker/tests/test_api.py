from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from ai_worker import api
from ai_worker.models import TutorJob


def test_liveness() -> None:
    response = api.liveness()

    assert response.status == "ok"
    assert response.checks == {}


def test_enqueue_tutor_job(monkeypatch) -> None:
    def fake_apply_async(*, args, queue):
        assert args[0]["type"] == "tutor"
        assert queue == api.settings.celery_queue_name
        return SimpleNamespace(id="job-123")

    monkeypatch.setattr(api.process_ai_job, "apply_async", fake_apply_async)

    response = api.enqueue_job(
        TutorJob(
            type="tutor",
            user_id="student-1",
            message="Apa itu fotosintesis?",
        )
    )

    assert response.job_id == "job-123"
    assert response.status == "queued"


def test_invalid_job_is_rejected() -> None:
    with pytest.raises(ValidationError):
        api.job_adapter.validate_python(
            {"type": "report_analysis", "user_id": "student-1", "performance_data": {}}
        )


def test_completed_job_returns_validated_result(monkeypatch) -> None:
    task = SimpleNamespace(
        state="SUCCESS",
        result={
            "type": "tutor",
            "data": {"answer": "Fotosintesis membuat makanan.", "suggested_next_steps": []},
        },
    )
    monkeypatch.setattr(api.celery_app, "AsyncResult", lambda job_id: task)

    response = api.get_job("job-123")

    assert response.status == "succeeded"
    assert response.result is not None
    assert response.result.type == "tutor"


def test_failed_job_does_not_expose_internal_exception(monkeypatch) -> None:
    task = SimpleNamespace(state="FAILURE", result=RuntimeError("sensitive details"))
    monkeypatch.setattr(api.celery_app, "AsyncResult", lambda job_id: task)

    response = api.get_job("job-123")

    assert response.status == "failed"
    assert response.error_code == "job_failed"
