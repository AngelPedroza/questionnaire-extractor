from types import SimpleNamespace

import httpx
import ollama
import pytest

from questionary_extractor.adapters.ollama_llm import (
    MAX_INPUT_CHARS,
    OllamaQuestionnaireLLM,
)
from questionary_extractor.adapters.prompt import SYSTEM_PROMPT
from questionary_extractor.domain.errors import (
    DocumentTooLongError,
    ExtractionError,
    LLMTimeoutError,
    LLMUnavailableError,
)
from questionary_extractor.domain.questionnaire import Questionnaire


class OllamaClientStub:
    def __init__(self, content="", error=None):
        self.content = content
        self.error = error
        self.calls = []

    def chat(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return SimpleNamespace(message=SimpleNamespace(content=self.content))


@pytest.fixture
def adapter():
    return OllamaQuestionnaireLLM("http://localhost:11434", "test-model")


@pytest.mark.parametrize(
    "provider_error",
    [ConnectionError("offline"), httpx.ConnectTimeout("timed out")],
    ids=["connection-error", "connect-timeout"],
)
def test_unreachable_model_raises_unavailable_with_exact_message(
    adapter, provider_error
):
    adapter.client = OllamaClientStub(error=provider_error)

    with pytest.raises(LLMUnavailableError) as error:
        adapter.extract("Document text")

    assert str(error.value) == "The language model is not reachable."
    assert error.value.__cause__ is provider_error


def test_provider_error_raises_extraction_error_with_exact_message(adapter):
    provider_error = ollama.ResponseError("x", 404)
    adapter.client = OllamaClientStub(error=provider_error)

    with pytest.raises(ExtractionError) as error:
        adapter.extract("Document text")

    assert str(error.value) == "The language model returned an invalid response."
    assert error.value.__cause__ is provider_error


@pytest.mark.parametrize(
    "content", ["{invalid", "{}"], ids=["invalid-json", "invalid-schema"]
)
def test_invalid_response_raises_extraction_error_with_exact_message(adapter, content):
    adapter.client = OllamaClientStub(content=content)

    with pytest.raises(ExtractionError) as error:
        adapter.extract("Document text")

    assert str(error.value) == "The language model returned an invalid response."


def test_extract_returns_validated_questionnaire(adapter, make_questionnaire):
    expected = make_questionnaire()
    adapter.client = OllamaClientStub(content=expected.model_dump_json())

    result = adapter.extract("Document text")

    assert isinstance(result, Questionnaire)
    assert result == expected


def test_request_sends_schema_prompt_and_deterministic_options(
    adapter, make_questionnaire
):
    client = OllamaClientStub(content=make_questionnaire().model_dump_json())
    adapter.client = client

    adapter.extract("Document text")

    assert client.calls == [
        {
            "model": "test-model",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "Document text"},
            ],
            "format": Questionnaire.model_json_schema(),
            "think": False,
            "options": {"temperature": 0, "num_ctx": 8192},
        }
    ]


def test_read_timeout_is_not_unavailable_or_retried(adapter):
    provider_error = httpx.ReadTimeout("timed out")
    client = OllamaClientStub(error=provider_error)
    adapter.client = client

    with pytest.raises(LLMTimeoutError) as error:
        adapter.extract("Document text")

    assert (
        str(error.value) == "The document took too long to process. Try a smaller file."
    )
    assert error.value.__cause__ is provider_error
    assert len(client.calls) == 1


def test_text_over_budget_is_rejected_before_calling_client(
    adapter, make_questionnaire
):
    client = OllamaClientStub(content=make_questionnaire().model_dump_json())
    adapter.client = client

    with pytest.raises(DocumentTooLongError) as error:
        adapter.extract("x" * (MAX_INPUT_CHARS + 1))

    assert (
        str(error.value) == "The document is too long to process. Try a shorter file."
    )
    assert client.calls == []


def test_text_at_budget_is_accepted(adapter, make_questionnaire):
    expected = make_questionnaire()
    adapter.client = OllamaClientStub(content=expected.model_dump_json())

    assert adapter.extract("x" * MAX_INPUT_CHARS) == expected
    assert len(adapter.client.calls) == 1


def test_default_client_uses_bounded_timeout_and_connection_retries(monkeypatch):
    from questionary_extractor.adapters import ollama_llm

    transports = []
    clients = []
    transport = object()

    def make_transport(**kwargs):
        transports.append(kwargs)
        return transport

    def make_client(**kwargs):
        clients.append(kwargs)
        return OllamaClientStub()

    monkeypatch.setattr(ollama_llm.httpx, "HTTPTransport", make_transport)
    monkeypatch.setattr(ollama_llm.ollama, "Client", make_client)

    OllamaQuestionnaireLLM("http://localhost:11434", "test-model")

    assert transports == [{"retries": 2}]
    assert clients == [
        {"host": "http://localhost:11434", "timeout": 180, "transport": transport}
    ]


def test_client_accepts_injected_transport(monkeypatch):
    from questionary_extractor.adapters import ollama_llm

    clients = []
    transport = httpx.MockTransport(lambda request: httpx.Response(200))
    monkeypatch.setattr(
        ollama_llm.ollama, "Client", lambda **kwargs: clients.append(kwargs)
    )

    OllamaQuestionnaireLLM("http://localhost:11434", "test-model", transport=transport)

    assert clients[0]["transport"] is transport


def test_invalid_http_json_raises_extraction_error(adapter):
    from json import JSONDecodeError

    provider_error = JSONDecodeError("invalid JSON", "not-json", 0)
    adapter.client = OllamaClientStub(error=provider_error)

    with pytest.raises(ExtractionError) as error:
        adapter.extract("Document text")

    assert error.value.__cause__ is provider_error
