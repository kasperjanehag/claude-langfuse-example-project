"""Langfuse availability checker for example scripts."""

import sys
import urllib.request
from typing import Optional

from agent_sdk.utils.config import Config

# Configure logger for this module


class LangfuseNotAvailableError(Exception):
    """Raised when Langfuse is required but not available."""
    pass


def _mask_key(key: Optional[str]) -> str:
    """Mask a key for safe display, showing only first and last few chars."""
    if not key:
        return "❌ NOT SET"
    if len(key) < 10:
        return "***"
    return f"{key[:8]}...{key[-4:]}"


def _print_config_status(config: Config) -> None:
    """Print current Langfuse configuration for debugging."""


def check_langfuse_available(exit_on_failure: bool = True) -> bool:
    """
    Check if Langfuse is available and properly configured.

    This function verifies:
    1. Langfuse credentials are configured in environment
    2. Langfuse service is reachable via HTTP

    Args:
        exit_on_failure: If True, exits the program with error message.
                        If False, raises LangfuseNotAvailableError.

    Returns:
        True if Langfuse is available

    Raises:
        LangfuseNotAvailableError: If Langfuse is not available and exit_on_failure=False
    """
    config = Config()

    # Always print config for transparency
    _print_config_status(config)

    # Check 1: Credentials configured
    has_public_key = bool(config.langfuse_public_key and config.langfuse_public_key.strip())
    has_secret_key = bool(config.langfuse_secret_key and config.langfuse_secret_key.strip())

    if not has_public_key or not has_secret_key:
        missing_keys = []
        if not has_public_key:
            missing_keys.append("LANGFUSE_PUBLIC_KEY")
        if not has_secret_key:
            missing_keys.append("LANGFUSE_SECRET_KEY")

        error_msg = (
            f"\n❌ Langfuse credentials not configured!\n\n"
            f"Missing environment variables: {', '.join(missing_keys)}\n\n"
            "This example requires Langfuse for tracing and observability.\n\n"
            "📋 Setup Instructions:\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "1. Start Langfuse services:\n"
            "   $ docker compose up -d\n\n"
            "2. Wait for services to be ready (~30 seconds):\n"
            "   $ docker compose logs -f langfuse-web\n"
            "   (Look for 'Ready' or 'Listening on' message)\n\n"
            "3. Visit http://localhost:3000 and:\n"
            "   - Create an account (or sign in)\n"
            "   - Create a project\n"
            "   - Go to Settings → API Keys\n\n"
            "4. Copy your keys to .env file:\n"
            "   LANGFUSE_PUBLIC_KEY=pk-lf-...\n"
            "   LANGFUSE_SECRET_KEY=sk-lf-...\n"
            "   LANGFUSE_HOST=http://localhost:3000\n\n"
            "5. Verify .env file is in project root (not in subdirectory)\n\n"
            "Need help? Check docs/LANGFUSE_INTEGRATION.md\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        if exit_on_failure:
            sys.exit(1)
        else:
            raise LangfuseNotAvailableError(error_msg)

    # Check 2: Service reachable
    try:
        response = urllib.request.urlopen(config.langfuse_host, timeout=5)
        status_code = response.getcode()
        response.close()

        return True

    except urllib.error.HTTPError as e:
        # HTTP error but server is reachable
        if e.code in [200, 301, 302, 404]:
            return True

        error_msg = (
            f"\n❌ Langfuse service returned HTTP error!\n\n"
            f"URL:    {config.langfuse_host}\n"
            f"Status: HTTP {e.code} {e.reason}\n\n"
            "📋 Troubleshooting:\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "1. Verify Langfuse is running:\n"
            "   $ docker compose ps\n"
            "   (Look for langfuse-web container in 'Up' state)\n\n"
            "2. Check if correct port is configured:\n"
            "   - Default: http://localhost:3000\n"
            "   - Your LANGFUSE_HOST: {config.langfuse_host}\n\n"
            "3. Check web logs for errors:\n"
            "   $ docker compose logs langfuse-web --tail 50\n\n"
            "4. Try accessing in browser:\n"
            "   $ open {config.langfuse_host}\n\n"
            "5. Restart Langfuse:\n"
            "   $ docker compose restart\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        if exit_on_failure:
            sys.exit(1)
        else:
            raise LangfuseNotAvailableError(error_msg)

    except urllib.error.URLError as e:
        # Connection refused or timeout
        error_msg = (
            f"\n❌ Cannot connect to Langfuse service!\n\n"
            f"URL:   {config.langfuse_host}\n"
            f"Error: {e.reason}\n\n"
            "📋 Troubleshooting:\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "1. Check if Langfuse Docker containers are running:\n"
            "   $ docker compose ps\n\n"
            "2. Start Langfuse if not running:\n"
            "   $ docker compose up -d\n"
            "   $ docker compose logs -f langfuse-web\n"
            "   (Wait for 'Ready' message, usually ~30 seconds)\n\n"
            "3. Verify port is not blocked:\n"
            "   $ curl -v {config.langfuse_host}\n\n"
            "4. Check if another service is using port 3000:\n"
            "   $ lsof -i :3000\n\n"
            "5. Verify LANGFUSE_HOST setting:\n"
            "   - Should be: http://localhost:3000\n"
            "   - Your value: {config.langfuse_host}\n\n"
            "6. Try restarting Docker:\n"
            "   $ docker compose down\n"
            "   $ docker compose up -d\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        if exit_on_failure:
            sys.exit(1)
        else:
            raise LangfuseNotAvailableError(error_msg)

    except Exception as e:
        # Unexpected error
        error_msg = (
            f"\n❌ Unexpected error connecting to Langfuse!\n\n"
            f"URL:       {config.langfuse_host}\n"
            f"Error:     {type(e).__name__}\n"
            f"Message:   {e}\n\n"
            "📋 Troubleshooting:\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "1. Verify Langfuse is running:\n"
            "   $ docker compose ps\n"
            "   $ docker compose logs langfuse-web --tail 50\n\n"
            "2. Check network connectivity:\n"
            "   $ curl {config.langfuse_host}\n\n"
            "3. Verify .env configuration:\n"
            "   - LANGFUSE_HOST should be http://localhost:3000\n"
            "   - No trailing slashes in URL\n\n"
            "If the issue persists, check docs/LANGFUSE_INTEGRATION.md\n"
            "or create an issue with the error details above.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        if exit_on_failure:
            sys.exit(1)
        else:
            raise LangfuseNotAvailableError(error_msg)


def require_langfuse() -> None:
    """
    Require Langfuse to be available or exit.

    This is a convenience wrapper for check_langfuse_available(exit_on_failure=True).
    Call this at the start of example scripts that require Langfuse.

    Example:
        ```python
        from agent_sdk.utils.langfuse_check import require_langfuse

        def main():
            require_langfuse()  # Will exit if Langfuse not available
            # ... rest of your code
        ```
    """
    check_langfuse_available(exit_on_failure=True)


def get_langfuse_status() -> dict:
    """
    Get the current status of Langfuse availability.

    Returns:
        Dict with status information:
        {
            "available": bool,
            "credentials_configured": bool,
            "service_reachable": bool,
            "error": Optional[str]
        }
    """
    config = Config()
    status = {
        "available": False,
        "credentials_configured": False,
        "service_reachable": False,
        "error": None,
    }

    # Check credentials
    if config.langfuse_public_key and config.langfuse_secret_key:
        status["credentials_configured"] = True
    else:
        status["error"] = "Credentials not configured"
        return status

    # Check service
    try:
        response = urllib.request.urlopen(config.langfuse_host, timeout=5)
        response.close()
        status["service_reachable"] = True
        status["available"] = True
    except Exception as e:
        status["error"] = f"{type(e).__name__}: {e}"

    return status
