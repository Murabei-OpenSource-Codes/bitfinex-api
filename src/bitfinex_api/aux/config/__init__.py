"""Bitfinex ``conf`` pair and currency metadata."""
from bitfinex_api.aux.config.config import (
    BitfinexAPIConfigMixin,
    BitfinexAPIConfigMapMixin,
    BitfinexAPIConfigComposeMixin,
    BitfinexAPIConfigListMixin,
    BitfinexAPIConfigBaseMixin,
)
from bitfinex_api.aux.config.treatment import TreatmentPairSymbols


__all__ = [
    "BitfinexAPIConfigBaseMixin",
    "BitfinexAPIConfigComposeMixin",
    "BitfinexAPIConfigListMixin",
    "BitfinexAPIConfigMapMixin",
    "BitfinexAPIConfigMixin",
    "TreatmentPairSymbols",
]