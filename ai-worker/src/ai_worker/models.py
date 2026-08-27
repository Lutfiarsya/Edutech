from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class JobType(StrEnum):
    TUTOR = "tutor"
    REPORT_ANALYSIS = "report_analysis"
    LEARNING_RECOMMENDATION = "learning_recommendation"


class ChatMessage(StrictModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8_000)


class TutorJob(StrictModel):
    type: Literal[JobType.TUTOR]
    user_id: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=8_000)
    subject: str | None = Field(default=None, max_length=120)
    education_level: str | None = Field(default=None, max_length=120)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)


class ReportAnalysisJob(StrictModel):
    type: Literal[JobType.REPORT_ANALYSIS]
    user_id: str = Field(min_length=1, max_length=128)
    report_title: str | None = Field(default=None, max_length=200)
    performance_data: dict[str, Any] = Field(min_length=1)
    notes: str | None = Field(default=None, max_length=8_000)


class LearningRecommendationJob(StrictModel):
    type: Literal[JobType.LEARNING_RECOMMENDATION]
    user_id: str = Field(min_length=1, max_length=128)
    performance_summary: str = Field(min_length=1, max_length=12_000)
    learning_goal: str | None = Field(default=None, max_length=1_000)
    preferences: list[str] = Field(default_factory=list, max_length=20)


AIJobRequest = Annotated[
    TutorJob | ReportAnalysisJob | LearningRecommendationJob,
    Field(discriminator="type"),
]


class TutorResult(StrictModel):
    answer: str
    suggested_next_steps: list[str]


class ReportAnalysisResult(StrictModel):
    summary: str
    strengths: list[str]
    areas_for_improvement: list[str]
    insights: list[str]


class RecommendationItem(StrictModel):
    title: str
    rationale: str
    priority: Literal["low", "medium", "high"]


class LearningRecommendationResult(StrictModel):
    overview: str
    recommendations: list[RecommendationItem]


class TutorJobResult(StrictModel):
    type: Literal[JobType.TUTOR]
    data: TutorResult


class ReportAnalysisJobResult(StrictModel):
    type: Literal[JobType.REPORT_ANALYSIS]
    data: ReportAnalysisResult


class LearningRecommendationJobResult(StrictModel):
    type: Literal[JobType.LEARNING_RECOMMENDATION]
    data: LearningRecommendationResult


AIJobResult = Annotated[
    TutorJobResult | ReportAnalysisJobResult | LearningRecommendationJobResult,
    Field(discriminator="type"),
]


class JobAccepted(StrictModel):
    job_id: str
    status: Literal["queued"] = "queued"


class JobStatus(StrictModel):
    job_id: str
    status: Literal["queued", "processing", "retrying", "succeeded", "failed"]
    result: AIJobResult | None = None
    error_code: str | None = None
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class HealthStatus(StrictModel):
    status: Literal["ok", "unavailable"]
    checks: dict[str, bool] = Field(default_factory=dict)
