import httpx
import ollama
from pydantic import ValidationError

from questionary_extractor.adapters.llm import QuestionnaireLLM
from questionary_extractor.adapters.prompt import SYSTEM_PROMPT
from questionary_extractor.domain.errors import ExtractionError, LLMUnavailableError
from questionary_extractor.domain.questionnaire import Questionnaire


class OllamaQuestionnaireLLM(QuestionnaireLLM):
    def __init__(self, host: str, model: str):
        self.client = ollama.Client(host=host, timeout=180)
        self.model = model

    def extract(self, text: str) -> Questionnaire:
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                format=Questionnaire.model_json_schema(),
                think=False,
                options={"temperature": 0, "num_ctx": 8192},
            )
            return Questionnaire.model_validate_json(response.message.content)
        except (ConnectionError, httpx.TimeoutException) as exc:
            raise LLMUnavailableError("The language model is not reachable.") from exc
        except (ollama.ResponseError, ValidationError) as exc:
            raise ExtractionError(
                "The language model returned an invalid response."
            ) from exc
