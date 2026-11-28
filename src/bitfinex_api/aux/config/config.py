"""Aggregate Bitfinex ``conf`` mixins for the HTTP client."""
from bitfinex_api.aux.config.config_base import BitfinexAPIConfigBaseMixin
from bitfinex_api.aux.config.config_compose import (
    API_SYMBOL_NAME_COMPLEMENT_MAP,
    BitfinexAPIConfigComposeMixin,
)
from bitfinex_api.aux.config.config_list import BitfinexAPIConfigListMixin
from bitfinex_api.aux.config.config_map import BitfinexAPIConfigMapMixin


class BitfinexAPIConfigMixin(
        BitfinexAPIConfigComposeMixin,
        BitfinexAPIConfigListMixin):
    """All config endpoint mixins composed for ``BitfinexAPI``."""


__all__ = [
    "API_SYMBOL_NAME_COMPLEMENT_MAP",
    "BitfinexAPIConfigBaseMixin",
    "BitfinexAPIConfigComposeMixin",
    "BitfinexAPIConfigListMixin",
    "BitfinexAPIConfigMapMixin",
    "BitfinexAPIConfigMixin",
]
