from ai_worker.application import LearningAssistant
from ai_worker.config import Settings, get_settings
from ai_worker.openai_adapter import OpenAITextGenerator


def build_learning_assistant(settings: Settings | None = None) -> LearningAssistant:
    settings = settings or get_settings()
    if settings.openai_api_key is None:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    generator = OpenAITextGenerator(
        api_key=settings.openai_api_key.get_secret_value(),
        model=settings.openai_model,
        timeout_seconds=settings.openai_timeout_seconds,
        max_output_tokens=settings.openai_max_output_tokens,
    )
    return LearningAssistant(generator)
