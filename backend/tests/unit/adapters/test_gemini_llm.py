from types import SimpleNamespace

import httpx
import pytest
from google.genai import errors

from questionary_extractor.adapters.gemini_llm import GeminiQuestionnaireLLM
from questionary_extractor.adapters.prompt import SYSTEM_PROMPT
from questionary_extractor.domain.errors import (
    ExtractionError,
    LLMTimeoutError,
    LLMUnavailableError,
)
from questionary_extractor.domain.questionnaire import Questionnaire


class GeminiModelsStub:
    def __init__(self, text="", error=None):
        self.text = text
        self.error = error
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return SimpleNamespace(text=self.text)


@pytest.fixture
def adapter():
    return GeminiQuestionnaireLLM("test-api-key", "test-model")


def test_server_error_raises_unavailable_with_exact_message(adapter):
    provider_error = errors.ServerError(503, {})
    adapter.client = SimpleNamespace(models=GeminiModelsStub(error=provider_error))

    with pytest.raises(LLMUnavailableError) as error:
        adapter.extract("Document text")

    assert str(error.value) == "The language model is not reachable."
    assert error.value.__cause__ is provider_error


def test_client_error_raises_extraction_error_with_exact_message(adapter):
    provider_error = errors.ClientError(400, {})
    adapter.client = SimpleNamespace(models=GeminiModelsStub(error=provider_error))

    with pytest.raises(ExtractionError) as error:
        adapter.extract("Document text")

    assert str(error.value) == "The language model returned an invalid response."
    assert error.value.__cause__ is provider_error


@pytest.mark.parametrize(
    "text", ["{invalid", "{}"], ids=["invalid-json", "invalid-schema"]
)
def test_invalid_response_raises_extraction_error_with_exact_message(adapter, text):
    adapter.client = SimpleNamespace(models=GeminiModelsStub(text=text))

    with pytest.raises(ExtractionError) as error:
        adapter.extract("Document text")

    assert str(error.value) == "The language model returned an invalid response."


def test_extract_returns_validated_questionnaire(adapter, make_questionnaire):
    expected = make_questionnaire()
    adapter.client = SimpleNamespace(
        models=GeminiModelsStub(text=expected.model_dump_json())
    )

    result = adapter.extract("Document text")

    assert isinstance(result, Questionnaire)
    assert result == expected


def test_request_sends_prompt_schema_and_deterministic_config(
    adapter, make_questionnaire
):
    models = GeminiModelsStub(text=make_questionnaire().model_dump_json())
    adapter.client = SimpleNamespace(models=models)

    adapter.extract("Document text")

    assert len(models.calls) == 1
    request = models.calls[0]
    assert request["model"] == "test-model"
    assert request["contents"] == "Document text"
    config = request["config"]
    assert config.system_instruction == SYSTEM_PROMPT
    assert config.response_json_schema == Questionnaire.model_json_schema()
    assert config.response_mime_type == "application/json"
    assert config.temperature == 0
    assert config.thinking_config.thinking_level == "LOW"


@pytest.mark.parametrize("timeout_type", ["ReadTimeout", "ConnectTimeout"])
def test_timeout_raises_timeout_domain_error(adapter, timeout_type):
    provider_error = getattr(httpx, timeout_type)("timed out")
    adapter.client = SimpleNamespace(models=GeminiModelsStub(error=provider_error))

    with pytest.raises(LLMTimeoutError) as error:
        adapter.extract("Document text")

    assert (
        str(error.value) == "The document took too long to process. Try a smaller file."
    )
    assert error.value.__cause__ is provider_error


def test_rate_limit_raises_unavailable_error(adapter):
    provider_error = errors.ClientError(429, {})
    adapter.client = SimpleNamespace(models=GeminiModelsStub(error=provider_error))

    with pytest.raises(LLMUnavailableError) as error:
        adapter.extract("Document text")

    assert str(error.value) == "The language model is not reachable."
    assert error.value.__cause__ is provider_error


def test_connection_error_raises_unavailable_error(adapter):
    import httpx

    provider_error = httpx.ConnectError("offline")
    adapter.client = SimpleNamespace(models=GeminiModelsStub(error=provider_error))

    with pytest.raises(LLMUnavailableError) as error:
        adapter.extract("Document text")

    assert str(error.value) == "The language model is not reachable."
    assert error.value.__cause__ is provider_error


def test_client_uses_bounded_timeout_and_transient_status_retries(monkeypatch):
    from questionary_extractor.adapters import gemini_llm

    clients = []
    monkeypatch.setattr(
        gemini_llm.genai, "Client", lambda **kwargs: clients.append(kwargs)
    )

    GeminiQuestionnaireLLM("test-api-key", "test-model")

    assert clients[0]["api_key"] == "test-api-key"
    options = clients[0]["http_options"]
    assert options.timeout == 90_000
    assert options.retry_options.attempts == 2
    assert options.retry_options.http_status_codes == [429, 503]


def test_client_accepts_injected_http_client(monkeypatch):
    import httpx

    from questionary_extractor.adapters import gemini_llm

    clients = []
    monkeypatch.setattr(
        gemini_llm.genai, "Client", lambda **kwargs: clients.append(kwargs)
    )
    with httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(200))
    ) as client:
        GeminiQuestionnaireLLM("test-api-key", "test-model", http_client=client)

        assert clients[0]["http_options"].httpx_client is client


def test_invalid_http_json_raises_extraction_error(adapter):
    from json import JSONDecodeError

    provider_error = JSONDecodeError("invalid JSON", "not-json", 0)
    adapter.client = SimpleNamespace(models=GeminiModelsStub(error=provider_error))

    with pytest.raises(ExtractionError) as error:
        adapter.extract("Document text")

    assert error.value.__cause__ is provider_error
