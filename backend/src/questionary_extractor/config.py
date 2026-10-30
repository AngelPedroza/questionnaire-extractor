from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: Literal["ollama", "gemini"] = "ollama"
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen3.5:9b"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-latest"
    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
