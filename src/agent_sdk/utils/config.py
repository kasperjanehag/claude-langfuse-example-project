"""Configuration management for the agent SDK."""

import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv()


class Config(BaseSettings):
    """Application configuration."""

    # OpenAI Configuration (legacy)
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")

    # Anthropic Configuration
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")

    # Langfuse Configuration
    langfuse_public_key: str = Field(default="", alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str = Field(default="", alias="LANGFUSE_SECRET_KEY")
    langfuse_host: str = Field(default="http://localhost:3000", alias="LANGFUSE_HOST")

    # Application Settings
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    environment: str = Field(default="development", alias="ENVIRONMENT")

    # Model Configuration
    model: str = Field(default="gpt-5-nano-2025-08-07", alias="OPENAI_MODEL")
    max_tokens: int = Field(default=4096)
    temperature: float = Field(default=0.0)  # Deterministic for consistency

    # Data Paths
    obligations_data_dir: str = Field(default="data/obligations", alias="OBLIGATIONS_DATA_DIR")
    obligations_excel_file: str = Field(
        default="Obligations and Controls example.xlsx",
        alias="OBLIGATIONS_EXCEL_FILE"
    )
    generated_controls_dir: str = Field(
        default="data/obligations/generated_controls",
        alias="GENERATED_CONTROLS_DIR"
    )

    @property
    def obligations_excel_path(self) -> str:
        """Get full path to obligations Excel file."""
        return os.path.join(self.obligations_data_dir, self.obligations_excel_file)

    class Config:
        env_file = ".env"
        case_sensitive = False


def get_config() -> Config:
    """Get application configuration."""
    return Config()
