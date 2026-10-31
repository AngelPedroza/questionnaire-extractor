import httpx
import pytest
from fastapi.testclient import TestClient


def skip_unless_llm_ready(settings) -> None:
    if settings.llm_provider == "gemini":
        if not settings.gemini_api_key:
            pytest.skip("GEMINI_API_KEY is not set")
        return
    try:
        tags = httpx.get(f"{settings.ollama_host}/api/tags", timeout=2).json()
    except (httpx.HTTPError, ValueError):
        pytest.skip(f"Ollama is not reachable at {settings.ollama_host}")
    if settings.ollama_model not in {model["name"] for model in tags.get("models", [])}:
        pytest.skip(f"Ollama model {settings.ollama_model} is not pulled")


@pytest.fixture(scope="session")
def client():
    # Imported here so the readiness check runs before the app builds its LLM client.
    from questionary_extractor.config import settings

    skip_unless_llm_ready(settings)

    from questionary_extractor.main import app

    with TestClient(app) as test_client:
        yield test_client
