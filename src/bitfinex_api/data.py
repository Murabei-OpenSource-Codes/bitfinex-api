"""Bitfinex REST API client."""
from bitfinex_api.aux import (
    BitfinexAPIBaseMixin,
    BitfinexAPICandlesMixin,
    BitfinexAPIConfigMixin,
)


class BitfinexAPI(
        BitfinexAPIBaseMixin,
        BitfinexAPICandlesMixin,
        BitfinexAPIConfigMixin):
    """Client for Bitfinex HTTP endpoints."""
