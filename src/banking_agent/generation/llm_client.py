from typing import Protocol

from google import genai

from banking_agent.core.config import GEMINI_API_KEY, GEMINI_MODEL
from banking_agent.core.exceptions import GenerationError


class TextGenerator(Protocol):
    """Protocol for text generation clients."""

    def generate(self, prompt: str) -> str:
        """Generate text from a prompt."""
        ...


class GeminiTextGenerator:
    """Gemini client for generating final agent responses."""

    def __init__(self) -> None:
        if not GEMINI_API_KEY:
            raise GenerationError(
                "GEMINI_API_KEY is missing. Add it to your .env file."
            )

        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = GEMINI_MODEL

    def generate(self, prompt: str) -> str:
        """Generate text using Gemini."""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
        except Exception as error:
            raise GenerationError(f"Gemini generation failed: {error}") from error

        if not response.text:
            raise GenerationError("Gemini returned an empty response.")

        return response.text.strip()