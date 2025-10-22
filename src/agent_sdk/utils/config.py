"""Configuration management - Example Template.

CUSTOMIZE THIS:
- Add your own configuration fields
- Update defaults for your use case
- Add validation as needed
"""

import os

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class Config(BaseSettings):
    """
    Application configuration using Pydantic Settings.

    Automatically loads from environment variables and .env file.
    """

    # OpenAI Configuration
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        alias="OPENAI_BASE_URL"
    )

    # Langfuse Configuration (for observability)
    langfuse_public_key: str = Field(default="", alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str = Field(default="", alias="LANGFUSE_SECRET_KEY")
    langfuse_host: str = Field(
        default="http://localhost:3000",
        alias="LANGFUSE_HOST"
    )

    # Model Configuration
    model: str = Field(
        default="gpt-4o",
        alias="OPENAI_MODEL"
    )
    max_tokens: int = Field(default=4096)
    temperature: float = Field(default=0.0)

    # Data Paths - customize for your use case
    data_dir: str = Field(default="data", alias="DATA_DIR")
    output_dir: str = Field(default="data/outputs", alias="OUTPUT_DIR")

    class Config:
        env_file = ".env"
        case_sensitive = False


def get_config() -> Config:
    """Get application configuration."""
    return Config()
