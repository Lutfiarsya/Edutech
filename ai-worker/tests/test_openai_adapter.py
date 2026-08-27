from types import SimpleNamespace

from ai_worker.models import TutorResult
from ai_worker.openai_adapter import OpenAITextGenerator


def test_openai_adapter_requests_and_validates_structured_output() -> None:
    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            output_text='{"answer":"Gunakan contoh konkret.","suggested_next_steps":[]}'
        )

    generator = OpenAITextGenerator(
        api_key="test-key",
        model="test-model",
        timeout_seconds=1,
        max_output_tokens=200,
    )
    generator._client = SimpleNamespace(responses=SimpleNamespace(create=fake_create))

    result = generator.generate(
        instructions="Bantu siswa.",
        input_text="Jelaskan pecahan.",
        output_schema=TutorResult,
    )

    assert result.answer == "Gunakan contoh konkret."
    assert captured["store"] is False
    assert captured["text"]["format"]["type"] == "json_schema"
    assert captured["text"]["format"]["strict"] is True
