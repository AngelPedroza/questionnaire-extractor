import pytest

from questionary_extractor.adapters.circuit_breaker import CircuitBreakerLLM
from questionary_extractor.adapters.gemini_llm import GeminiQuestionnaireLLM
from questionary_extractor.adapters.llm import QuestionnaireLLM
from questionary_extractor.adapters.ollama_llm import OllamaQuestionnaireLLM
from questionary_extractor.config import Settings


def test_abstract_llm_cannot_be_instantiated():
    with pytest.raises(TypeError, match="abstract"):
        QuestionnaireLLM()


def test_default_settings_create_ollama_adapter():
    settings = Settings(_env_file=None)

    adapter = QuestionnaireLLM.from_settings(settings)

    assert isinstance(adapter, CircuitBreakerLLM)
    assert isinstance(adapter.inner, OllamaQuestionnaireLLM)
    assert adapter.inner.model == settings.ollama_model


def test_gemini_settings_with_key_create_gemini_adapter():
    settings = Settings(
        _env_file=None,
        llm_provider="gemini",
        gemini_api_key="test-api-key",
        gemini_model="configured-model",
    )

    adapter = QuestionnaireLLM.from_settings(settings)

    assert isinstance(adapter, CircuitBreakerLLM)
    assert isinstance(adapter.inner, GeminiQuestionnaireLLM)
    assert adapter.inner.model == "configured-model"


def test_gemini_settings_without_key_raise_configuration_error():
    settings = Settings(_env_file=None, llm_provider="gemini")

    with pytest.raises(RuntimeError) as error:
        QuestionnaireLLM.from_settings(settings)

    assert str(error.value) == "GEMINI_API_KEY must be set when LLM_PROVIDER is gemini."
