"""Exceptions for Bitfinex HTTP client errors."""
import requests


class BitfinexAPIError(Exception):
    """Base exception for Bitfinex API client errors.

    Attributes:
        message (str):
            Human-readable error description.
        payload (dict):
            Optional context returned by the API or client.
    """

    def __repr__(self) -> str:
        """Return the exception representation."""
        template = "{class_name}: {message}"
        message = self.format_message()
        return template.format(
            class_name=self.__class__.__name__,
            message=message)

    def __str__(self) -> str:
        """Return the string representation of the exception."""
        return self.__repr__()

    def __init__(self, message: str, payload: dict | None = None) -> None:
        """Initialize the exception."""
        self.message = message
        if payload is None:
            payload = {}
        self.payload = payload

    def format_message(self) -> str:
        """Fill message placeholders from the payload."""
        try:
            return self.message.format(**self.payload)
        except (KeyError, IndexError, ValueError):
            return self.message

    def to_dict(self) -> dict[str, object]:
        """Serialize the exception to a dictionary."""
        message = self.format_message()
        return {
            "payload": self.payload,
            "type": self.__class__.__name__,
            "message": message}


class BitfinexAPIInvalidParametersError(BitfinexAPIError):
    """Exception for invalid parameters errors."""


class BitfinexAPIDataValidationError(BitfinexAPIError):
    """Exception for data validation errors."""


# Request-related errors
class BitfinexAPIRequestError(BitfinexAPIError):
    """Exception for a failed Bitfinex HTTP response."""


class BitfinexAPIAuthenticationError(BitfinexAPIRequestError):
    """Exception for missing or invalid Bitfinex API credentials."""


class BitfinexAPINoneResponseError(BitfinexAPIRequestError):
    """Exception for response body containing no data."""


class BitfinexAPIRequestTreatment:
    """Map a Bitfinex HTTP response onto a domain exception."""

    @classmethod
    def raise_by_code(cls, response: requests.Response) -> None:
        """Raise when the response status is not successful."""
        if response.ok:
            return

        if response.status_code in (401, 403):
            payload = {"url": response.url, "error": response.text}
            raise BitfinexAPIAuthenticationError(
                message="Authentication failed for {url}: {error}",
                payload=payload)

        try:
            response_payload = response.json()
        except requests.JSONDecodeError:
            response_payload = {
                "json_decode_error": True,
                "error": response.text,
                "url": response.url}

        payload = {
            "url": response.url,
            "error": response_payload}
        raise BitfinexAPIRequestError(
            message="Error fetching data from {url}: {error}",
            payload=payload)
