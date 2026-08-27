from openai import OpenAI

from ai_worker.provider import OutputT


class OpenAITextGenerator:
    """OpenAI Responses adapter that always returns a validated Pydantic model."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float,
        max_output_tokens: int,
    ) -> None:
        self._client = OpenAI(api_key=api_key, timeout=timeout_seconds, max_retries=0)
        self._model = model
        self._max_output_tokens = max_output_tokens

    def generate(
        self,
        *,
        instructions: str,
        input_text: str,
        output_schema: type[OutputT],
    ) -> OutputT:
        schema: dict[str, object] = output_schema.model_json_schema()
        response = self._client.responses.create(
            model=self._model,
            instructions=instructions,
            input=input_text,
            max_output_tokens=self._max_output_tokens,
            store=False,
            text={
                "format": {
                    "type": "json_schema",
                    "name": output_schema.__name__,
                    "strict": True,
                    "schema": schema,
                }
            },
        )
        return output_schema.model_validate_json(response.output_text)
