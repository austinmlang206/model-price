"""Application configuration using pydantic-settings.

All hardcoded values are centralized here and can be overridden via environment variables.
"""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

# Read version from pyproject.toml
def _get_version() -> str:
    """Read version from pyproject.toml."""
    pyproject_path = Path(__file__).parent / "pyproject.toml"
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        for line in content.split("\n"):
            if line.startswith("version"):
                # Parse: version = "0.2.0"
                return line.split("=")[1].strip().strip('"').strip("'")
    return "0.0.0"


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    api_version: str = _get_version()
    reload: bool = True

    # CORS configuration (comma-separated list in env var)
    cors_origins: List[str] = ["http://localhost:5173"]

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # External API URLs
    litellm_url: str = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"
    openai_pricing_url: str = "https://platform.openai.com/docs/pricing"
    gemini_pricing_url: str = "https://ai.google.dev/pricing"
    bedrock_url: str = "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrock/current/us-east-1/index.json"
    bedrock_fm_url: str = "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrockFoundationModels/current/us-east-1/index.json"
    openrouter_url: str = "https://openrouter.ai/api/v1/models"
    azure_prices_url: str = "https://prices.azure.com/api/retail/prices"

    # HTTP timeouts (seconds)
    http_timeout: float = 60.0
    metadata_timeout: float = 30.0
    scraper_subprocess_timeout: int = 300
    scraper_page_load_timeout: int = 60000  # milliseconds
    scraper_wait_timeout: int = 2000  # milliseconds
    gemini_scraper_wait_timeout: int = 3000  # milliseconds


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience alias
settings = get_settings()
