"""Tests for configuration."""

import os

from agent_sdk.utils.config import Config


def test_config_defaults():
    """Test configuration defaults."""
    config = Config()

    assert config.log_level == "INFO"
    assert config.environment == "development"
    assert config.model == "claude-3-5-sonnet-20241022"
    assert config.max_tokens == 4096
    assert config.temperature == 0.7
    assert config.langfuse_host == "http://localhost:3000"


def test_config_from_env(monkeypatch):
    """Test configuration from environment variables."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key_123")
    monkeypatch.setenv("MODEL", "claude-3-opus-20240229")
    monkeypatch.setenv("MAX_TOKENS", "2000")

    config = Config()

    assert config.anthropic_api_key == "test_key_123"
    assert config.model == "claude-3-opus-20240229"
    assert config.max_tokens == 2000
