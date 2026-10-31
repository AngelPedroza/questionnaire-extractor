import json

import httpx
import pytest

from questionary_extractor.adapters import gemini_llm
from questionary_extractor.adapters.prompt import SYSTEM_PROMPT
from questionary_extractor.domain.errors import (
    ExtractionError,
    LLMTimeoutError,
    LLMUnavailableError,
)
from questionary_extractor.domain.questionnaire import Questionnaire


@pytest.fixture
def make_adapter(monkeypatch):
    monkeypatch.setattr(
        gemini_llm,
        "RETRY_OPTIONS",
        gemini_llm.RETRY_OPTIONS.model_copy(
            update={"initial_delay": 0.001, "jitter": 0.0}
        ),
    )
    adapters = []

    def make(handler):
        client = httpx.Client(transport=httpx.MockTransport(handler), trust_env=False)
        adapter = gemini_llm.GeminiQuestionnaireLLM(
            "test-api-key", "test-model", http_client=client
        )
        adapters.append((adapter, client))
        return adapter

    yield make
    for adapter, client in adapters:
        adapter.client.close()
        client.close()


def test_success_sends_gemini_rest_contract(
    make_adapter, recording_handler, gemini_response, questionnaire
):
    handler = recording_handler([gemini_response()])
    adapter = make_adapter(handler)

    assert adapter.extract("Document text") == questionnaire

    assert len(handler.requests) == 1
    request = handler.requests[0]
    assert request.method == "POST"
    assert request.url.path == "/v1beta/models/test-model:generateContent"
    payload = json.loads(request.content)
    assert payload["contents"] == [
        {"role": "user", "parts": [{"text": "Document text"}]}
    ]
    assert payload["systemInstruction"] == {
        "role": "user",
        "parts": [{"text": SYSTEM_PROMPT}],
    }
    config = payload["generationConfig"]
    assert config["temperature"] == 0
    assert config["responseMimeType"] == "application/json"
    assert config["responseJsonSchema"] == Questionnaire.model_json_schema()
    assert request.extensions["timeout"]["read"] == 90


def test_transient_503_then_success_retries_once(
    make_adapter, recording_handler, gemini_response, questionnaire
):
    handler = recording_handler(
        [
            httpx.Response(503, json={"error": {"code": 503, "message": "busy"}}),
            gemini_response(),
        ]
    )
    adapter = make_adapter(handler)

    assert adapter.extract("Document text") == questionnaire
    assert len(handler.requests) == 2


def test_rate_limit_exhaustion_is_unavailable(make_adapter, recording_handler):
    handler = recording_handler(
        [
            httpx.Response(
                429, json={"error": {"code": 429, "message": "rate limited"}}
            )
            for _ in range(2)
        ]
    )
    adapter = make_adapter(handler)

    with pytest.raises(LLMUnavailableError) as error:
        adapter.extract("Document text")

    assert str(error.value) == "The language model is not reachable."
    assert len(handler.requests) == 2


def test_400_is_extraction_error_without_retry(make_adapter, recording_handler):
    handler = recording_handler(
        [httpx.Response(400, json={"error": {"code": 400, "message": "bad request"}})]
    )
    adapter = make_adapter(handler)

    with pytest.raises(ExtractionError):
        adapter.extract("Document text")

    assert len(handler.requests) == 1


@pytest.mark.parametrize("timeout_type", [httpx.ReadTimeout, httpx.ConnectTimeout])
def test_timeout_exhaustion_is_timeout_after_two_attempts(
    make_adapter, recording_handler, timeout_type
):
    handler = recording_handler([timeout_type("timed out") for _ in range(2)])
    adapter = make_adapter(handler)

    with pytest.raises(LLMTimeoutError) as error:
        adapter.extract("Document text")

    assert (
        str(error.value) == "The document took too long to process. Try a smaller file."
    )
    assert isinstance(error.value.__cause__, timeout_type)
    assert len(handler.requests) == 2


def test_connect_error_exhaustion_is_unavailable(make_adapter, recording_handler):
    handler = recording_handler([httpx.ConnectError("offline") for _ in range(2)])
    adapter = make_adapter(handler)

    with pytest.raises(LLMUnavailableError):
        adapter.extract("Document text")

    assert len(handler.requests) == 2


def test_unlisted_500_is_not_retried(make_adapter, recording_handler):
    handler = recording_handler(
        [httpx.Response(500, json={"error": {"code": 500, "message": "server error"}})]
    )
    adapter = make_adapter(handler)

    with pytest.raises(LLMUnavailableError):
        adapter.extract("Document text")

    assert len(handler.requests) == 1


@pytest.mark.parametrize(
    "malformation",
    [
        "invalid-http-json",
        "missing-candidates",
        "invalid-model-json",
        "invalid-model-schema",
    ],
)
def test_malformed_response_is_extraction_error(
    make_adapter, recording_handler, gemini_response, malformation
):
    responses = {
        "invalid-http-json": httpx.Response(200, content="not-json"),
        "missing-candidates": httpx.Response(200, json={}),
        "invalid-model-json": gemini_response("not-json"),
        "invalid-model-schema": gemini_response("{}"),
    }
    handler = recording_handler([responses[malformation]])
    adapter = make_adapter(handler)

    with pytest.raises(ExtractionError):
        adapter.extract("Document text")

    assert len(handler.requests) == 1
