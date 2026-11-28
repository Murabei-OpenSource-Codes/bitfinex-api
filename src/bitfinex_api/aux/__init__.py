"""Auxiliary modules for Bitfinex API."""

from bitfinex_api.aux.base import BitfinexAPIBaseMixin
from bitfinex_api.aux.candles import BitfinexAPICandlesMixin
from bitfinex_api.aux.config import BitfinexAPIConfigMixin

__all__ = [
    "BitfinexAPIBaseMixin",
    "BitfinexAPICandlesMixin",
    "BitfinexAPIConfigMixin",
]