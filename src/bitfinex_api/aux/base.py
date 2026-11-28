"""Bitfinex REST API HTTP client base."""
import requests
from typing import Any
from urllib.parse import urljoin
from loguru import logger
from tenacity import (
    RetryCallState, retry, retry_if_exception_type,
    stop_after_attempt, wait_fixed,)

from bitfinex_api.config import (
    BITFINEX__PROXY_URL,
    BITFINEX__REQUEST_MAX_ATTEMPTS,
    BITFINEX__REQUEST_RETRY_MIN_WAIT,
    BITFINEX__REQUEST_TIMEOUT,)
from bitfinex_api.exceptions import (
    BitfinexAPIRequestTreatment, BitfinexAPIAuthenticationError)


RETRY_ERRORS = (requests.ConnectionError, requests.Timeout)
"""Tuple of errors to retry on."""


def _log_retry_before_sleep(retry_state: RetryCallState) -> None:
    """Log a network failure before sleeping for the next attempt."""
    outcome = retry_state.outcome
    if outcome is None or not outcome.failed:
        return
    exc = outcome.exception()
    fn_name = retry_state.fn.__name__
    msg = (
        "Bitfinex API {fn_name} failed ({error_type}): {error}. "
        "Attempt {attempt}/{max_attempts}, retrying").format(
            fn_name=fn_name,
            error_type=type(exc).__name__,
            error=exc,
            attempt=retry_state.attempt_number,
            max_attempts=BITFINEX__REQUEST_MAX_ATTEMPTS)
    logger.warning(msg)


_RETRY_ON_NETWORK = retry(
    retry=retry_if_exception_type(RETRY_ERRORS),
    stop=stop_after_attempt(BITFINEX__REQUEST_MAX_ATTEMPTS),
    wait=wait_fixed(BITFINEX__REQUEST_RETRY_MIN_WAIT),
    reraise=True,
    before_sleep=_log_retry_before_sleep)


class BitfinexAPIBaseMixin:
    """HTTP session and low-level methods for Bitfinex API v2."""

    PUBLIC_BASE_URL = "https://api-pub.bitfinex.com/v2/"
    """Base URL for public Bitfinex endpoints."""

    AUTH_BASE_URL = "https://api.bitfinex.com/v2/"
    """Base URL for authenticated Bitfinex endpoints."""

    _api_key = None
    """Bitfinex API key for authenticated endpoints."""

    _api_secret = None
    """Bitfinex API secret for authenticated endpoints."""

    def __init__(self, api_key: str | None = None,
                 api_secret: str | None = None) -> None:
        """Open a requests session for Bitfinex calls.

        Args:
            api_key (str | None):
                Bitfinex API key for authenticated endpoints.
            api_secret (str | None):
                Bitfinex API secret for authenticated endpoints.
        """
        self._api_key = api_key
        self._api_secret = api_secret

        proxies = None
        if BITFINEX__PROXY_URL is not None:
            proxies = {
                "http": BITFINEX__PROXY_URL,
                "https": BITFINEX__PROXY_URL}

        self.session = requests.Session()
        if proxies is not None:
            self.session.proxies.update(proxies)

    def build_headers(self) -> dict[str, str]:
        """Build default request headers."""
        return {"accept": "application/json"}

    def check_auth(self, authenticated: bool) -> None:
        """Check if authentication is required."""
        if authenticated:
            is_auth_not_set = (
                self._api_key is None or self._api_secret is None)
            if is_auth_not_set:
                msg = ("Authentication is required but API key and secret "
                       "are not set.")
                raise BitfinexAPIAuthenticationError(message=msg)
        return None

    @_RETRY_ON_NETWORK
    def get(self, endpoint: str | None = None,
            url: str | None = None, query_params: dict | None = None,
            authenticated: bool = False) -> Any:
        """Send a GET request and return the JSON body.

        Args:
            endpoint (str | None):
                Path joined onto the base URL.
            url (str | None):
                Full request URL when ``endpoint`` is omitted.
            query_params (dict | None):
                Query string parameters.
            authenticated (bool):
                When True, use the authenticated base URL and sign the
                request (not yet implemented).

        Returns:
            Any:
                Parsed JSON body (object or array).

        Raises:
            ValueError:
                When both ``endpoint`` and ``url`` are omitted.
            BitfinexAPIRequestError:
                When the response status is not successful.
        """
        # Validate if authentication is set before making the request
        self.check_auth(authenticated=authenticated)

        if endpoint is None:
            raise ValueError("Either endpoint or url must be provided.")

        # Redirect to the appropriate base URL based on authentication status
        # public and authenticated endpoints are handled on different
        # sub-domains
        base = self.AUTH_BASE_URL if authenticated else self.PUBLIC_BASE_URL
        url = urljoin(base, endpoint)
        headers = self.build_headers()

        response = self.session.get(
            url=url, params=query_params,
            headers=headers, timeout=BITFINEX__REQUEST_TIMEOUT)

        # Raise an exception if the response status, using the Bitfinex
        # return to raise the appropriate exception
        BitfinexAPIRequestTreatment.raise_by_code(response=response)
        return response.json()

    @_RETRY_ON_NETWORK
    def post(self, endpoint: str | None = None, url: str | None = None,
             query_params: dict | None = None, data: dict | None = None,
             authenticated: bool = False) -> Any:
        """Send a POST request and return the JSON body.

        Args:
            endpoint (str | None):
                Path joined onto the base URL.
            url (str | None):
                Full request URL when ``endpoint`` is omitted.
            query_params (dict | None):
                Query string parameters.
            data (dict | None):
                JSON request body.
            authenticated (bool):
                When True, use the authenticated base URL and sign the
                request (not yet implemented).

        Returns:
            Any:
                Parsed JSON body (object or array).

        Raises:
            ValueError:
                When both ``endpoint`` and ``url`` are omitted.
            BitfinexAPIRequestError:
                When the response status is not successful.
        """
        self.check_auth(authenticated=authenticated)

        if endpoint is None:
            raise ValueError("Either endpoint or url must be provided.")

        base = self.AUTH_BASE_URL if authenticated else self.PUBLIC_BASE_URL
        url = urljoin(base, endpoint)
        headers = self.build_headers()

        response = self.session.post(
            url=url,
            params=query_params,
            json=data,
            headers=headers,
            timeout=BITFINEX__REQUEST_TIMEOUT)

        # Raise an exception if the response status, using the Bitfinex
        # return to raise the appropriate exception
        BitfinexAPIRequestTreatment.raise_by_code(response=response)
        return response.json()
