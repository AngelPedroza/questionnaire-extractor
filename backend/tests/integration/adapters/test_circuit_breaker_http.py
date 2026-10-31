import httpx
import pytest

from questionary_extractor.adapters.circuit_breaker import CircuitBreakerLLM
from questionary_extractor.adapters.ollama_llm import OllamaQuestionnaireLLM
from questionary_extractor.domain.errors import LLMTimeoutError, LLMUnavailableError


def test_breaker_blocks_transport_until_half_open_trial(recording_handler):
    handler = recording_handler([httpx.ReadTimeout("timed out") for _ in range(4)])
    adapter = OllamaQuestionnaireLLM(
        "http://localhost:11434", "test-model", transport=httpx.MockTransport(handler)
    )
    now = 0.0
    breaker = CircuitBreakerLLM(adapter, clock=lambda: now)
    try:
        for _ in range(3):
            with pytest.raises(LLMTimeoutError):
                breaker.extract("Document text")
        assert len(handler.requests) == 3

        with pytest.raises(LLMUnavailableError, match="temporarily unavailable"):
            breaker.extract("Blocked")
        assert len(handler.requests) == 3

        now = 30.0
        with pytest.raises(LLMTimeoutError):
            breaker.extract("Trial")
        assert len(handler.requests) == 4

        with pytest.raises(LLMUnavailableError, match="temporarily unavailable"):
            breaker.extract("Blocked again")
        assert len(handler.requests) == 4
    finally:
        adapter.client.close()
