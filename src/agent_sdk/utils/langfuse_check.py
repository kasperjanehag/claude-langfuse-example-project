"""Langfuse availability checker for example scripts."""

import sys
import urllib.request
from typing import Optional

from agent_sdk.utils.config import Config


class LangfuseNotAvailableError(Exception):
    """Raised when Langfuse is required but not available."""
    pass


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

    # Check 1: Credentials configured
    if not config.langfuse_public_key or not config.langfuse_secret_key:
        error_msg = (
            "\n❌ Langfuse credentials not configured!\n\n"
            "This example requires Langfuse for tracing and observability.\n\n"
            "Setup instructions:\n"
            "1. Copy .env.example to .env\n"
            "2. Start Langfuse: docker compose up -d\n"
            "3. Visit http://localhost:3000 and create account\n"
            "4. Go to Settings → API Keys\n"
            "5. Copy your keys to .env:\n"
            "   LANGFUSE_PUBLIC_KEY=pk-lf-...\n"
            "   LANGFUSE_SECRET_KEY=sk-lf-...\n"
        )
        if exit_on_failure:
            print(error_msg, file=sys.stderr)
            sys.exit(1)
        else:
            raise LangfuseNotAvailableError(error_msg)

    # Check 2: Service reachable
    try:
        response = urllib.request.urlopen(config.langfuse_host, timeout=5)
        response.close()
        return True
    except Exception as e:
        error_msg = (
            f"\n❌ Langfuse service not reachable at {config.langfuse_host}!\n\n"
            f"Error: {type(e).__name__}: {e}\n\n"
            "This example requires Langfuse to be running.\n\n"
            "To start Langfuse:\n"
            "1. Run: docker compose up -d\n"
            "2. Wait ~30 seconds for services to start\n"
            "3. Verify: curl http://localhost:3000\n"
            "4. Check logs: docker compose logs -f langfuse-web\n\n"
            "Then run this script again.\n"
        )
        if exit_on_failure:
            print(error_msg, file=sys.stderr)
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
