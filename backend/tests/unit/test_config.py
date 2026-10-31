import pytest

from questionary_extractor.config import Settings


def test_settings_use_defaults_without_dotenv_or_environment():
    settings = Settings(_env_file=None)

    assert settings.model_dump() == {
        "llm_provider": "ollama",
        "ollama_host": "http://localhost:11434",
        "ollama_model": "qwen3.5:9b",
        "gemini_api_key": "",
        "gemini_model": "gemini-flash-latest",
        "cors_origins": ["http://localhost:3000"],
    }


@pytest.mark.parametrize(
    ("environment_name", "field_name", "value", "expected"),
    [
        ("LLM_PROVIDER", "llm_provider", "gemini", "gemini"),
        (
            "OLLAMA_HOST",
            "ollama_host",
            "http://localhost:12345",
            "http://localhost:12345",
        ),
        ("OLLAMA_MODEL", "ollama_model", "configured-ollama", "configured-ollama"),
        ("GEMINI_API_KEY", "gemini_api_key", "test-api-key", "test-api-key"),
        ("GEMINI_MODEL", "gemini_model", "configured-gemini", "configured-gemini"),
        (
            "CORS_ORIGINS",
            "cors_origins",
            '["https://first.example", "https://second.example"]',
            ["https://first.example", "https://second.example"],
        ),
    ],
    ids=[
        "provider",
        "ollama-host",
        "ollama-model",
        "gemini-key",
        "gemini-model",
        "cors",
    ],
)
def test_environment_overrides_setting(
    monkeypatch, environment_name, field_name, value, expected
):
    monkeypatch.setenv(environment_name, value)

    settings = Settings(_env_file=None)

    assert getattr(settings, field_name) == expected
