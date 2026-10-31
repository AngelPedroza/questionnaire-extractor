import json
import socket

import httpx
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


@pytest.fixture
def make_adapter():
    adapters = []

    def make(handler):
        adapter = OllamaQuestionnaireLLM(
            "http://localhost:11434",
            "test-model",
            transport=httpx.MockTransport(handler),
        )
        adapters.append(adapter)
        return adapter

    yield make
    for adapter in adapters:
        adapter.client.close()


def test_success_sends_ollama_chat_contract(
    make_adapter, recording_handler, ollama_response, questionnaire
):
    handler = recording_handler([ollama_response()])
    adapter = make_adapter(handler)

    assert adapter.extract("Document text") == questionnaire

    assert len(handler.requests) == 1
    request = handler.requests[0]
    assert request.method == "POST"
    assert request.url.path == "/api/chat"
    payload = json.loads(request.content)
    assert payload["model"] == "test-model"
    assert payload["messages"] == [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Document text"},
    ]
    assert payload["format"] == Questionnaire.model_json_schema()
    assert payload["think"] is False
    assert payload["stream"] is False
    assert payload["options"] == {"temperature": 0, "num_ctx": 8192}
    # Ollama's default keep-alive applies, so the model is unloaded when idle.
    assert "keep_alive" not in payload
    assert request.extensions["timeout"]["read"] == 180


def test_read_timeout_is_not_retried(make_adapter, recording_handler):
    handler = recording_handler([httpx.ReadTimeout("timed out")])
    adapter = make_adapter(handler)

    with pytest.raises(LLMTimeoutError) as error:
        adapter.extract("Document text")

    assert (
        str(error.value) == "The document took too long to process. Try a smaller file."
    )
    assert isinstance(error.value.__cause__, httpx.ReadTimeout)
    assert len(handler.requests) == 1


@pytest.mark.parametrize("status", [404, 500])
def test_http_errors_are_not_retried(make_adapter, recording_handler, status):
    handler = recording_handler(
        [httpx.Response(status, json={"error": "provider failure"})]
    )
    adapter = make_adapter(handler)

    with pytest.raises(ExtractionError) as error:
        adapter.extract("Document text")

    assert str(error.value) == "The language model returned an invalid response."
    assert len(handler.requests) == 1


@pytest.mark.parametrize(
    "malformation",
    [
        "invalid-http-json",
        "missing-message",
        "invalid-model-json",
        "invalid-model-schema",
    ],
)
def test_malformed_response_is_extraction_error(
    make_adapter, recording_handler, ollama_response, malformation
):
    responses = {
        "invalid-http-json": httpx.Response(200, content="not-json"),
        "missing-message": httpx.Response(200, json={}),
        "invalid-model-json": ollama_response("not-json"),
        "invalid-model-schema": ollama_response("{}"),
    }
    handler = recording_handler([responses[malformation]])
    adapter = make_adapter(handler)

    with pytest.raises(ExtractionError):
        adapter.extract("Document text")

    assert len(handler.requests) == 1


def test_over_budget_document_does_not_reach_transport(make_adapter, recording_handler):
    handler = recording_handler([])
    adapter = make_adapter(handler)

    with pytest.raises(DocumentTooLongError):
        adapter.extract("x" * (MAX_INPUT_CHARS + 1))

    assert handler.requests == []


def test_unreachable_loopback_host_is_unavailable(monkeypatch):
    monkeypatch.setenv("NO_PROXY", "127.0.0.1")
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    adapter = OllamaQuestionnaireLLM(f"http://127.0.0.1:{port}", "test-model")
    try:
        with pytest.raises(LLMUnavailableError) as error:
            adapter.extract("Document text")

        assert str(error.value) == "The language model is not reachable."
        assert isinstance(error.value.__cause__, ConnectionError)
    finally:
        adapter.client.close()
