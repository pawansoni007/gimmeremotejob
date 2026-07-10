"""Runtime configuration, loaded from environment / .env."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM — local Ollama (OpenAI-compatible)
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "minimax-m3:cloud"
    ollama_api_key: str = "ollama"
    # minimax-m3 is a thinking model — reasoning eats into the output budget,
    # so leave generous headroom for the visible answers.
    ollama_max_tokens: int = 8192
    ollama_timeout_seconds: float = 300.0

    # Optional markdown file describing the applicant (background, stack,
    # wins). Grounds the drafted answers; without it the model must use
    # [FILL: ...] placeholders for personal facts.
    applicant_profile_path: str = "profile.md"

    # Database
    database_url: str = "postgresql+psycopg://apply:apply@localhost:5432/apply"

    # Service
    service_port: int = 8756


settings = Settings()
