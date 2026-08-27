from typing import Protocol, TypeVar

from pydantic import BaseModel

OutputT = TypeVar("OutputT", bound=BaseModel)


class AITextGenerator(Protocol):
    """Internal seam for validated AI generation."""

    def generate(
        self,
        *,
        instructions: str,
        input_text: str,
        output_schema: type[OutputT],
    ) -> OutputT: ...
