"""Configuration management for claims-agentic-platform.

Loads environment variables from .env located at the project root.
Raises clear errors if required variables are missing.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Project root path (claims-agentic-platform/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

# Load .env file
load_dotenv(dotenv_path=ENV_PATH)


def _get_required_env(var_name: str, fallback_var: str | None = None) -> str:
    """Retrieve an environment variable or raise a clear error."""
    val = os.getenv(var_name)
    if (val is None or not val.strip()) and fallback_var:
        val = os.getenv(fallback_var)

    if val is None or not val.strip():
        var_display = f"'{var_name}'" if not fallback_var else f"'{var_name}' (or '{fallback_var}')"
        raise ValueError(
            f"Missing required environment variable: {var_display}.\n"
            f"Please ensure it is set in your .env file at:\n  {ENV_PATH}"
        )
    return val.strip()


class Settings:
    """Provides validated access to configuration settings."""

    @property
    def databricks_server_hostname(self) -> str:
        return _get_required_env("DATABRICKS_SERVER_HOSTNAME")

    @property
    def databricks_http_path(self) -> str:
        return _get_required_env("DATABRICKS_HTTP_PATH")

    @property
    def databricks_token(self) -> str:
        return _get_required_env("DATABRICKS_TOKEN")

    @property
    def groq_api_key(self) -> str:
        return _get_required_env("GROQ_API_KEY", fallback_var="GOOGLE_API_KEY")

    @property
    def google_api_key(self) -> str:
        return _get_required_env("GOOGLE_API_KEY", fallback_var="GROQ_API_KEY")

    @property
    def groq_model(self) -> str:
        return os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b").strip()


settings = Settings()


def __getattr__(name: str):
    """Enable module-level attribute access with validation upon access."""
    if name == "DATABRICKS_SERVER_HOSTNAME":
        return settings.databricks_server_hostname
    if name == "DATABRICKS_HTTP_PATH":
        return settings.databricks_http_path
    if name == "DATABRICKS_TOKEN":
        return settings.databricks_token
    if name == "GROQ_API_KEY":
        return settings.groq_api_key
    if name == "GOOGLE_API_KEY":
        return settings.google_api_key
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

