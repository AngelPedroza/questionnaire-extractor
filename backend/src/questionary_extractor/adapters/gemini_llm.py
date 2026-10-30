from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from questionary_extractor.adapters.llm import QuestionnaireLLM
from questionary_extractor.adapters.prompt import SYSTEM_PROMPT
from questionary_extractor.domain.errors import ExtractionError, LLMUnavailableError
from questionary_extractor.domain.questionnaire import Questionnaire


class GeminiQuestionnaireLLM(QuestionnaireLLM):
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY must be set when LLM_PROVIDER is gemini."
            )
        self.client = genai.Client(api_key=api_key)
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
                ),
            )
            return Questionnaire.model_validate_json(response.text)
        except errors.ServerError as exc:
            raise LLMUnavailableError("The language model is not reachable.") from exc
        except (errors.APIError, ValidationError) as exc:
            raise ExtractionError(
                "The language model returned an invalid response."
            ) from exc
