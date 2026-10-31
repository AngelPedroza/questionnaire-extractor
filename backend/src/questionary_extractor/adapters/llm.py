from abc import ABC, abstractmethod

from questionary_extractor.config import Settings
from questionary_extractor.domain.questionnaire import Questionnaire


class QuestionnaireLLM(ABC):
    @abstractmethod
    def extract(self, text: str) -> Questionnaire: ...

    @staticmethod
    def from_settings(settings: Settings) -> "QuestionnaireLLM":
        # Imported here to avoid a circular import and to load only the selected SDK.
        from questionary_extractor.adapters.circuit_breaker import CircuitBreakerLLM

        if settings.llm_provider == "gemini":
            from questionary_extractor.adapters.gemini_llm import GeminiQuestionnaireLLM

            return CircuitBreakerLLM(
                GeminiQuestionnaireLLM(settings.gemini_api_key, settings.gemini_model)
            )

        from questionary_extractor.adapters.ollama_llm import OllamaQuestionnaireLLM

        return CircuitBreakerLLM(
            OllamaQuestionnaireLLM(settings.ollama_host, settings.ollama_model)
        )
