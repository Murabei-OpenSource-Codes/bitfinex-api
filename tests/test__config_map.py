"""Live tests for config mixin."""
import math
import unittest
from bitfinex_api import BitfinexAPI


self = BitfinexAPI()


class TestConfigMixin(unittest.TestCase):
    """Live config calls."""

    def test_map_api_currency_symbol(self) -> None:
        """Sym map: platform code (e.g. DSH) maps to wallet symbol."""
        client = BitfinexAPI()
        sym_map = client.map_api_currency_symbol()
        self.assertIn("api_symbol", sym_map.columns)
        self.assertIn("currency_symbol", sym_map.columns)
        dsh = sym_map.loc[sym_map["api_symbol"] == "DSH", "currency_symbol"]
        self.assertFalse(dsh.empty)
        self.assertEqual(dsh.iloc[0], "DASH")

    def test_map_api_symbol_names(self) -> None:
        """Label map lists platform codes with human names."""
        client = BitfinexAPI()
        names = client.map_api_symbol_names()
        self.assertIn("api_symbol", names.columns)
        self.assertIn("name", names.columns)
        self.assertGreater(len(names), 0)
        btc = names.loc[names["api_symbol"] == "BTC", "name"]
        self.assertEqual(btc.iloc[0], "Bitcoin")

    def test_map_api_symbol_derivative_underlyings(self) -> None:
        """Derivative map links futures codes to underlying asset."""
        client = BitfinexAPI()
        undl = client.map_api_symbol_derivative_underlyings()
        self.assertIn("derivative_api_symbol", undl.columns)
        self.assertIn("underlying_api_symbol", undl.columns)
        btc_f0 = undl.loc[
            undl["derivative_api_symbol"] == "BTCF0",
            "underlying_api_symbol",
        ]
        self.assertFalse(btc_f0.empty)
        self.assertEqual(btc_f0.iloc[0], "BTC")

    def test_map_api_symbol_currency_pool(self) -> None:
        """Pool map ties ERC-20-style tokens to a parent network."""
        client = BitfinexAPI()
        pools = client.map_api_symbol_currency_pool()
        self.assertIn("api_symbol", pools.columns)
        self.assertIn("currency_pool", pools.columns)
        aave = pools.loc[pools["api_symbol"] == "AAVE", "currency_pool"]
        self.assertFalse(aave.empty)
        self.assertEqual(aave.iloc[0], "ETH")

    def test_map_api_symbol_currency_explorer(self) -> None:
        """Explorer map provides block explorer URL sets per asset."""
        client = BitfinexAPI()
        explorers = client.map_api_symbol_currency_explorer()
        self.assertIn("api_symbol", explorers.columns)
        self.assertIn("currency_explorer_url_list", explorers.columns)
        eth = explorers.loc[
            explorers["api_symbol"] == "ETH",
            "currency_explorer_url_list",
        ]
        self.assertFalse(eth.empty)
        urls = eth.iloc[0]
        self.assertTrue(
            isinstance(urls, list) and "etherscan.io" in urls[0],
            msg="ETH explorer should list etherscan",
        )

    def test_map_api_symbol_withdrawal_fee(self) -> None:
        """Tx fee map exposes withdrawal fee per platform code."""
        client = BitfinexAPI()
        fees = client.map_api_symbol_withdrawal_fee()
        self.assertIn("api_symbol", fees.columns)
        self.assertIn("withdrawal_fee", fees.columns)
        btc = fees.loc[fees["api_symbol"] == "BTC", "withdrawal_fee"]
        self.assertFalse(btc.empty)
        fee = btc.iloc[0]
        self.assertIsInstance(fee, (int, float))
        self.assertGreater(fee, 0)
        self.assertFalse(math.isnan(fee))

    def test_map_api_symbol_withdrawal_method(self) -> None:
        """Tx method map lists withdrawal rails per platform code."""
        client = BitfinexAPI()
        methods = client.map_api_symbol_withdrawal_method()
        self.assertIn("api_symbol", methods.columns)
        self.assertIn("currency_withdrawal_methods", methods.columns)
        btc = methods.loc[
            methods["api_symbol"] == "BTC", "currency_withdrawal_methods",
        ]
        self.assertFalse(btc.empty)
        rails = btc.iloc[0]
        self.assertIsInstance(rails, list)
        self.assertIn("BITCOIN", rails)

    def test_api_symbol_with_labels(self) -> None:
        """Merged sym + label map fills complement names where needed."""
        client = BitfinexAPI()
        merged = client.api_symbol_with_labels()
        self.assertIn("name", merged.columns)
        self.assertIn("currency_symbol", merged.columns)
        alg = merged.loc[merged["api_symbol"] == "ALG"].iloc[0]
        self.assertEqual(alg["name"], "Algorand")
        eth2p = merged.loc[merged["api_symbol"] == "ETH2P", "name"]
        self.assertEqual(eth2p.iloc[0], "Ethereum 2.0 Pending")

    def test_map_api_symbol_all(self) -> None:
        """Unified map: one row per sym code, derivatives keep original key."""
        client = BitfinexAPI()
        sym_map = client.map_api_currency_symbol()
        merged = client.map_api_symbol_all()
        expected_columns = {
            "api_symbol",
            "currency_symbol",
            "underlying_api_symbol",
            "is_derivative",
            "name",
            "currency_pool",
            "currency_explorer_url_list",
            "withdrawal_fee",
            "currency_withdrawal_methods",
        }
        self.assertTrue(expected_columns.issubset(set(merged.columns)))
        self.assertEqual(len(merged), len(sym_map))
        dsh = merged.loc[merged["api_symbol"] == "DSH"].iloc[0]
        self.assertFalse(dsh["is_derivative"])
        self.assertEqual(dsh["currency_symbol"], "DASH")
        self.assertEqual(dsh["name"], "Dash")
        btcf0 = merged.loc[merged["api_symbol"] == "BTCF0"].iloc[0]
        self.assertTrue(btcf0["is_derivative"])
        self.assertEqual(btcf0["underlying_api_symbol"], "BTC")
        self.assertEqual(btcf0["name"], "Bitcoin")
        self.assertIn("BITCOIN", btcf0["currency_withdrawal_methods"])