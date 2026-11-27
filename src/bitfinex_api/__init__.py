"""Python client for the Bitfinex HTTP API.

Import the client from ``bitfinex_api.data``::

    from bitfinex_api.data import BitfinexAPI

    client = BitfinexAPI()
    client.get(endpoint="tickers", query_params={"symbols": "ALL"})

Optional ``api_key`` and ``api_secret`` enable authenticated calls.
Request timeout and retries come from ``bitfinex_api.config``.
"""
from bitfinex_api.data import BitfinexAPI

__all__ = [
    "BitfinexAPI"]