import json
from dataclasses import dataclass
from typing import Generic

from pydantic import BaseModel

from ai_worker.models import (
    AIJobRequest,
    LearningRecommendationJob,
    LearningRecommendationResult,
    ReportAnalysisJob,
    ReportAnalysisResult,
    TutorJob,
    TutorResult,
)
from ai_worker.provider import AITextGenerator, OutputT

BASE_INSTRUCTIONS = """
Anda adalah asisten pembelajaran Edutech. Jawab dalam Bahasa Indonesia yang jelas,
ramah, dan sesuai tingkat pendidikan pengguna. Jangan mengarang data yang tidak
diberikan. Jika data kurang, sebutkan keterbatasannya. Jangan memberikan diagnosis
medis/psikologis atau keputusan berisiko tinggi. Kembalikan hanya data yang sesuai
dengan schema keluaran.
""".strip()


@dataclass(frozen=True)
class GenerationSpec(Generic[OutputT]):
    instructions: str
    input_text: str
    output_schema: type[OutputT]


class LearningAssistant:
    """Processes every supported learning job through one small interface."""

    def __init__(self, generator: AITextGenerator) -> None:
        self._generator = generator

    def process(self, job: AIJobRequest) -> BaseModel:
        spec = build_generation_spec(job)
        return self._generator.generate(
            instructions=spec.instructions,
            input_text=spec.input_text,
            output_schema=spec.output_schema,
        )


def build_generation_spec(job: AIJobRequest) -> GenerationSpec:
    if isinstance(job, TutorJob):
        context = {
            "subject": job.subject,
            "education_level": job.education_level,
            "history": [message.model_dump() for message in job.history],
            "latest_message": job.message,
        }
        return GenerationSpec(
            instructions=(
                f"{BASE_INSTRUCTIONS}\n\n"
                "Bertindak sebagai tutor. Bimbing pengguna memahami konsep dengan penjelasan "
                "bertahap. Jangan langsung mengambil alih pekerjaan pengguna."
            ),
            input_text=_as_json(context),
            output_schema=TutorResult,
        )

    if isinstance(job, ReportAnalysisJob):
        context = {
            "report_title": job.report_title,
            "performance_data": job.performance_data,
            "notes": job.notes,
        }
        return GenerationSpec(
            instructions=(
                f"{BASE_INSTRUCTIONS}\n\n"
                "Analisis laporan pembelajaran berdasarkan data yang tersedia. Bedakan temuan "
                "yang didukung data dari keterbatasan data. Fokus pada pola yang dapat "
                "ditindaklanjuti."
            ),
            input_text=_as_json(context),
            output_schema=ReportAnalysisResult,
        )

    if isinstance(job, LearningRecommendationJob):
        context = {
            "performance_summary": job.performance_summary,
            "learning_goal": job.learning_goal,
            "preferences": job.preferences,
        }
        return GenerationSpec(
            instructions=(
                f"{BASE_INSTRUCTIONS}\n\n"
                "Buat rekomendasi belajar yang spesifik, realistis untuk MVP, dan diurutkan "
                "berdasarkan dampak. Jelaskan alasan setiap rekomendasi."
            ),
            input_text=_as_json(context),
            output_schema=LearningRecommendationResult,
        )

    raise ValueError(f"Unsupported job type: {type(job).__name__}")


def _as_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)
