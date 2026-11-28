# """Unit and live tests for candle mixin."""
# import unittest

# from bitfinex_api.aux.candles.candles import (
#     bitfinex_candle_period_to_ms,
#     build_hist_query_params,
# )


# class TestCandleContracts(unittest.TestCase):
#     """Candle period and query helpers."""

#     def test_candle_period_to_ms(self) -> None:
#         """Map common Bitfinex periods to milliseconds."""
#         self.assertEqual(bitfinex_candle_period_to_ms("1h"), 3_600_000)
#         self.assertEqual(bitfinex_candle_period_to_ms("1D"), 86_400_000)

#     def test_build_hist_query_params_empty(self) -> None:
#         """Omitted bounds yield None."""
#         self.assertIsNone(build_hist_query_params())

#     def test_build_hist_query_params_full(self) -> None:
#         """All query keys are included when set."""
#         params = build_hist_query_params(
#             start_ms=1, end_ms=2, limit=10, sort=1)
#         self.assertEqual(params, {
#             "start": 1,
#             "end": 2,
#             "limit": 10,
#             "sort": 1,
#         })


# class TestCandlesLive(unittest.TestCase):
#     """Live candle call against the public API."""

#     def test_get_candles_limit(self) -> None:
#         """Fetch one candle bar for tBTCUSD."""
#         from bitfinex_api import BitfinexAPI

#         client = BitfinexAPI()
#         envelope = client.get_candles(
#             symbol="tBTCUSD",
#             period="1h",
#             limit=1,
#         )
#         self.assertEqual(envelope["endpoint"], "candles")
#         self.assertEqual(envelope["par"], "tBTCUSD")
#         body = envelope["body"]
#         self.assertIsInstance(body, list)
#         self.assertGreaterEqual(len(body), 1)
#         row = body[0]
#         self.assertEqual(len(row), 6)
