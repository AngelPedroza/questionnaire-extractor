from json import JSONDecodeError

import httpx
from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from questionary_extractor.adapters.llm import QuestionnaireLLM
from questionary_extractor.adapters.prompt import SYSTEM_PROMPT
from questionary_extractor.domain.errors import (
    ExtractionError,
    LLMTimeoutError,
    LLMUnavailableError,
)
from questionary_extractor.domain.questionnaire import Questionnaire

# Two 90 s attempts plus backoff target about 185 s of Vercel's 300 s budget.
TIMEOUT_MS = 90_000
RETRY_OPTIONS = types.HttpRetryOptions(attempts=2, http_status_codes=[429, 503])


class GeminiQuestionnaireLLM(QuestionnaireLLM):
    def __init__(
        self, api_key: str, model: str, http_client: httpx.Client | None = None
    ):
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY must be set when LLM_PROVIDER is gemini."
            )
        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=TIMEOUT_MS,
                retry_options=RETRY_OPTIONS,
                httpx_client=http_client,
            ),
        )
        self.model = model

    def extract(self, text: str) -> Questionnaire:
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=text,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_json_schema=Questionnaire.model_json_schema(),
                    temperature=0,
                    # Copying fields needs little reasoning; LOW mirrors think=False on Ollama.
                    thinking_config=types.ThinkingConfig(thinking_level="LOW"),
                ),
            )
            return Questionnaire.model_validate_json(response.text)
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError() from exc
        except (httpx.ConnectError, errors.ServerError) as exc:
            raise LLMUnavailableError("The language model is not reachable.") from exc
        except (errors.APIError, ValidationError, JSONDecodeError) as exc:
            if isinstance(exc, errors.ClientError) and exc.code == 429:
                raise LLMUnavailableError(
                    "The language model is not reachable."
                ) from exc
            raise ExtractionError(
                "The language model returned an invalid response."
            ) from exc
