"""Timeout and retry settings for the Bitfinex client."""
import os


def _positive_int(name: str, default: int) -> int:
    """Read a positive integer from the environment.

    A missing or blank value returns ``default``.

    Args:
        name (str):
            Environment variable name.
        default (int):
            Value used when the variable is missing or blank.

    Returns:
        int:
            Parsed positive integer.

    Raises:
        ValueError:
            If the value is not a positive integer.
    """
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(
            "{name} must be a positive integer. Got {raw}.".format(
                name=name, raw=raw)) from None
    if value < 1:
        raise ValueError(
            "{name} must be a positive integer. Got {raw}.".format(
                name=name, raw=raw))
    return value


def _positive_float(name: str, default: float) -> float:
    """Read a positive float from the environment.

    A missing or blank value returns ``default``.

    Args:
        name (str):
            Environment variable name.
        default (float):
            Value used when the variable is missing or blank.

    Returns:
        float:
            Parsed positive float.

    Raises:
        ValueError:
            If the value is not a positive float.
    """
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = float(raw)
    except ValueError:
        raise ValueError(
            "{name} must be a positive number. Got {raw}.".format(
                name=name, raw=raw)) from None
    if value <= 0:
        raise ValueError(
            "{name} must be a positive number. Got {raw}.".format(
                name=name, raw=raw))
    return value


BITFINEX__REQUEST_TIMEOUT: int = _positive_int(
    "BITFINEX__REQUEST_TIMEOUT", 60)
"""Seconds to wait for a single Bitfinex HTTP request."""

BITFINEX__PROXY_URL: str | None = os.environ.get(
    "BITFINEX__PROXY_URL", None)
"""URL of the proxy to use for requests to Bitfinex."""

BITFINEX__REQUEST_MAX_ATTEMPTS: int = _positive_int(
    "BITFINEX__REQUEST_MAX_ATTEMPTS", 5)
"""Maximum number of HTTP attempts before giving up on a network error."""

BITFINEX__REQUEST_RETRY_MIN_WAIT: float = _positive_float(
    "BITFINEX__REQUEST_RETRY_MIN_WAIT", 0.5)
"""Minimum wait time between HTTP attempts in seconds."""
