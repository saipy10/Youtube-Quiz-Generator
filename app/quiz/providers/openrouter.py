import json
import re
from typing import Any, Dict
import httpx
from app.config.settings import settings
from app.quiz.models import Quiz
from app.quiz.prompts import SYSTEM_PROMPT, create_user_prompt
from app.utils.logger import setup_logger, mask_secret

logger = setup_logger(__name__)


class LLMProvider:
    """Base interface for LLM providers."""
    def generate_quiz(self, video_title: str, transcript_text: str) -> Quiz:
        raise NotImplementedError


class OpenRouterProvider(LLMProvider):
    """OpenRouter API client for structured quiz generation."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float = 60.0,
    ):
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.model = model or settings.OPENROUTER_MODEL
        self.base_url = (base_url or settings.OPENROUTER_BASE_URL).rstrip("/")
        self.timeout = timeout

        if not self.api_key:
            logger.warning("OpenRouter API key is not configured!")
        else:
            logger.info(f"OpenRouter initialized with model '{self.model}' and key {mask_secret(self.api_key)}")

    def _clean_json_response(self, text: str) -> str:
        """Strips markdown code fences, preambles, and thinking traces to extract pure JSON."""
        text = text.strip()
        # 1. Try extracting from markdown code block ```json ... ```
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            return match.group(1).strip()

        # 2. Extract outermost JSON object from { to }
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            return text[first_brace:last_brace + 1].strip()

        return text

    def generate_quiz(self, video_title: str, transcript_text: str) -> Quiz:
        """
        Sends the transcript to OpenRouter and returns a validated Quiz model.
        """
        if not self.api_key:
            raise ValueError("OpenRouter API key is missing. Please set OPENROUTER_API_KEY in .env")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/youtube-community-quiz-automation",
            "X-Title": "YouTube Community Quiz Automation",
        }

        user_content = create_user_prompt(video_title, transcript_text)

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.4,
            "max_tokens": 1500,
        }

        logger.info(f"Sending quiz generation request to OpenRouter model: {self.model}")

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )

                if response.status_code != 200:
                    error_detail = response.text
                    logger.error(f"OpenRouter request failed ({response.status_code}): {error_detail}")
                    raise RuntimeError(f"OpenRouter API error (HTTP {response.status_code}): {error_detail}")

                data = response.json()

        except httpx.RequestError as e:
            logger.error(f"Network error while calling OpenRouter: {e}")
            raise RuntimeError(f"Network error communicating with OpenRouter: {e}")

        if isinstance(data, dict) and "error" in data:
            err_msg = data["error"].get("message", str(data["error"]))
            logger.error(f"OpenRouter returned error: {err_msg}")
            raise RuntimeError(f"OpenRouter error: {err_msg}. If this model is overloaded, consider using 'google/gemini-2.5-flash'.")

        try:
            raw_content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Unexpected response structure from OpenRouter: {data}")
            raise RuntimeError(f"OpenRouter returned unexpected response structure: {data}")

        cleaned_json_str = self._clean_json_response(raw_content)

        try:
            quiz = Quiz.model_validate_json(cleaned_json_str)
            logger.info("Successfully generated and validated quiz from OpenRouter.")
            return quiz
        except Exception as e:
            logger.error(f"Failed to validate generated JSON as Quiz: {e}\nRaw output: {raw_content}")
            raise ValueError(f"Generated quiz failed validation: {e}")
