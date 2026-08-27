from typing import Any

from pydantic import BaseModel

from ai_worker.application import LearningAssistant
from ai_worker.models import (
    LearningRecommendationJob,
    LearningRecommendationResult,
    ReportAnalysisJob,
    ReportAnalysisResult,
    TutorJob,
    TutorResult,
)


class FakeGenerator:
    def __init__(self, responses: dict[type[BaseModel], BaseModel]) -> None:
        self.responses = responses
        self.last_call: dict[str, Any] | None = None

    def generate(
        self,
        *,
        instructions: str,
        input_text: str,
        output_schema: type[BaseModel],
    ) -> BaseModel:
        self.last_call = {
            "instructions": instructions,
            "input_text": input_text,
            "output_schema": output_schema,
        }
        return self.responses[output_schema]


def test_tutor_job_uses_tutor_schema() -> None:
    expected = TutorResult(answer="Pecah masalahnya menjadi dua langkah.", suggested_next_steps=[])
    generator = FakeGenerator({TutorResult: expected})

    result = LearningAssistant(generator).process(
        TutorJob(type="tutor", user_id="student-1", message="Jelaskan pecahan")
    )

    assert result == expected
    assert generator.last_call is not None
    assert generator.last_call["output_schema"] is TutorResult
    assert "Jelaskan pecahan" in generator.last_call["input_text"]


def test_report_analysis_job_uses_report_schema() -> None:
    expected = ReportAnalysisResult(
        summary="Nilai meningkat.",
        strengths=["Konsisten"],
        areas_for_improvement=["Aljabar"],
        insights=["Latihan rutin berkorelasi dengan kenaikan nilai"],
    )
    generator = FakeGenerator({ReportAnalysisResult: expected})

    result = LearningAssistant(generator).process(
        ReportAnalysisJob(
            type="report_analysis",
            user_id="student-1",
            performance_data={"math": 78},
        )
    )

    assert result == expected
    assert generator.last_call is not None
    assert generator.last_call["output_schema"] is ReportAnalysisResult


def test_recommendation_job_uses_recommendation_schema() -> None:
    expected = LearningRecommendationResult(overview="Fokus pada aljabar.", recommendations=[])
    generator = FakeGenerator({LearningRecommendationResult: expected})

    result = LearningAssistant(generator).process(
        LearningRecommendationJob(
            type="learning_recommendation",
            user_id="student-1",
            performance_summary="Aljabar masih lemah.",
        )
    )

    assert result == expected
    assert generator.last_call is not None
    assert generator.last_call["output_schema"] is LearningRecommendationResult
