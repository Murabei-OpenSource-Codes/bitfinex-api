"""Shared helpers for Bitfinex ``conf`` endpoints."""
import datetime
from typing import Any

from bitfinex_api.exceptions import BitfinexAPIInvalidParametersError


class BitfinexAPIConfigBaseMixin:
    """``unwrap_response``, market validation, platform status."""

    VALID_MARKETS: tuple[str, ...] = (
        "exchange", "margin", "futures", "securities")
    """Valid markets for ``pub:list:pair`` segments."""

    def validate_market(self, market: str) -> None:
        """Validate the market."""
        if market not in self.VALID_MARKETS:
            raise BitfinexAPIInvalidParametersError(
                message="Invalid market: {market}. Expected one of {choices}.",
                payload={"market": market, "choices": self.VALID_MARKETS})

    def unwrap_response(self, body: Any) -> Any:
        """Unwrap the response body from a Bitfinex API call."""
        if not isinstance(body, list) or len(body) == 0:
            return None
        return body[0]

    def platform_status(self) -> dict[str, Any]:
        """Fetch ``GET /v2/platform/status``."""
        path = "platform/status"
        collected_at = datetime.datetime.now(datetime.timezone.utc)
        body = self.unwrap_response(self.get(endpoint=path))
        return {
            "collected_at": collected_at,
            "body": body,
        }
