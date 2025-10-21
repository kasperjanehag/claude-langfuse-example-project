"""Wrapper for Langfuse integration with graceful error handling."""

import logging
import os
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# Global flag to track if Langfuse is available
_langfuse_available = None
_langfuse_checked = False


def is_langfuse_available() -> bool:
    """
    Check if Langfuse is available and working.

    Returns:
        True if Langfuse can be used, False otherwise
    """
    global _langfuse_available, _langfuse_checked

    if _langfuse_checked:
        return _langfuse_available

    try:
        from agent_sdk.utils.config import Config

        config = Config()

        # Only consider Langfuse available if all required config is present
        if not config.langfuse_public_key or not config.langfuse_secret_key:
            _langfuse_available = False
            _langfuse_checked = True
            logger.info("Langfuse credentials not configured - tracing disabled")
            return False

        # Try a simple HTTP check to see if Langfuse is running
        import urllib.request
        import socket

        try:
            # Quick check with 5 second timeout
            socket.setdefaulttimeout(5)
            response = urllib.request.urlopen(config.langfuse_host, timeout=5)
            response.close()
            _langfuse_available = True
            _langfuse_checked = True
            logger.info("Langfuse integration enabled")
            return True
        except Exception as e:
            _langfuse_available = False
            _langfuse_checked = True
            logger.debug(f"Langfuse service not reachable ({type(e).__name__}: {e}) - tracing disabled")
            return False

    except Exception as e:
        _langfuse_available = False
        _langfuse_checked = True
        logger.info(f"Langfuse check failed: {e} - tracing disabled")
        return False


def safe_observe(name: Optional[str] = None, as_type: Optional[str] = None):
    """
    Decorator that safely applies Langfuse @observe decorator.

    If Langfuse is not available, the decorator becomes a no-op.

    Args:
        name: Name for the observation
        as_type: Type of observation

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        # Try to apply Langfuse decorator if available
        if is_langfuse_available():
            try:
                from langfuse.decorators import observe
                return observe(name=name, as_type=as_type)(func)
            except Exception as e:
                logger.warning(f"Failed to apply Langfuse decorator: {e}")
                return func
        else:
            # Return function unchanged if Langfuse not available
            return func

    return decorator


def safe_langfuse_context(operation: str, *args, **kwargs) -> Any:
    """
    Safely call langfuse_context methods with error handling.

    Args:
        operation: Method name to call on langfuse_context
        *args: Positional arguments for the method
        **kwargs: Keyword arguments for the method

    Returns:
        Result of the operation, or None if it fails
    """
    if not is_langfuse_available():
        return None

    try:
        from langfuse.decorators import langfuse_context

        method = getattr(langfuse_context, operation, None)
        if method is None:
            logger.warning(f"langfuse_context.{operation} not found")
            return None

        return method(*args, **kwargs)
    except Exception as e:
        # Silently ignore Langfuse errors - don't pollute logs
        logger.debug(f"Langfuse context operation '{operation}' failed: {e}")
        return None


def update_current_trace(**kwargs):
    """Safely update current trace."""
    return safe_langfuse_context("update_current_trace", **kwargs)


def update_current_observation(**kwargs):
    """Safely update current observation."""
    return safe_langfuse_context("update_current_observation", **kwargs)


def flush():
    """Safely flush Langfuse."""
    return safe_langfuse_context("flush")
