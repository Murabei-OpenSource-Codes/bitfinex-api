"""Smoke tests for package layout and public API."""
import unittest


class TestBitfinexPackage(unittest.TestCase):
    """Verify the client can be imported."""

    def test_import_bitfinex_api(self) -> None:
        """Import BitfinexAPI from the package root."""
        from bitfinex_api import BitfinexAPI

        client = BitfinexAPI()
        self.assertIsNotNone(client.session)


class TestBitfinexPublicEndpoint(unittest.TestCase):
    """Live call to a public Bitfinex endpoint."""

    def test_platform_status(self) -> None:
        """Fetch platform status from the public API."""
        from bitfinex_api import BitfinexAPI

        client = BitfinexAPI()
        status = client.get(endpoint="platform/status")
        self.assertIsInstance(status, list)