"""Merge multiple ``conf`` map DataFrames on ``api_symbol``."""
import pandas as pd
from loguru import logger

from bitfinex_api.aux.config.config_map import BitfinexAPIConfigMapMixin
from bitfinex_api.exceptions import BitfinexAPIDataValidationError


API_SYMBOL_NAME_COMPLEMENT_MAP: dict[str, str] = {
    "ETH2P": "Ethereum 2.0 Pending",
    "ETH2R": "Ethereum 2.0 Rewards",
    "ETH2U": "Ethereum 2.0 Unstaking",
    "ETH2X": "Ethereum 2.0",
    "EUTF0": "Tether EURt (derivative)",
    "HBARF0": "Hedera (derivative)",
    "ONDOF0": "Ondo (derivative)",
    "TAOF0": "Bittensor (derivative)",
    "TESTALGO": "Algorand (test)",
    "TESTALGOF0": "Algorand (test derivative)",
    "TESTEOS": "EOS (test)",
    "TESTXTZF0": "Tezos (test derivative)",
    "TONF0": "Toncoin (derivative)",
}
"""Labels for platform codes absent from ``pub:map:currency:label``."""


class BitfinexAPIConfigComposeMixin(BitfinexAPIConfigMapMixin):
    """Client-side joins across map endpoints."""

    CURRENCY_INFO_COLUMNS: tuple[str, ...] = (
        "currency", "name", "sym", "pool", "explorer", "tx_fee",
        "tx_method", )
    """Target schema for full currency metadata (future list helpers)."""

    def map_api_symbol_all_info(self) -> pd.DataFrame:
        """``map_api_symbol_all`` plus label backfill for sym-only codes."""
        symbol_name_map = self.map_api_symbol_names()
        merged = self.map_api_symbol_all()

        is_na_name = merged.loc[:, "name"].isna()
        missing_names = merged.loc[is_na_name, :].drop(columns=["name"])
        to_merge_missing = symbol_name_map.rename(
            columns={"api_symbol": "currency_symbol"})
        missing_with_names = missing_names.merge(
            to_merge_missing, on="currency_symbol", how="left")

        is_na_name_last_resort = missing_with_names.loc[:, "name"].isna()
        missing_with_names.loc[is_na_name_last_resort, "name"] = (
            missing_with_names.loc[is_na_name_last_resort, "api_symbol"]
            .map(API_SYMBOL_NAME_COMPLEMENT_MAP))

        all_data = pd.concat([
            merged.loc[~is_na_name, :], missing_with_names])

        value_count_api_symbol = all_data["api_symbol"].value_counts()
        if not (value_count_api_symbol == 1).all():
            duplicates = value_count_api_symbol[
                value_count_api_symbol != 1].index.tolist()
            msg = "Duplicate API symbols: {duplicates}"
            raise BitfinexAPIDataValidationError(
                message=msg, payload={"duplicates": duplicates})

        missing_name_codes = all_data.loc[
            all_data["name"].isna(), "api_symbol"].tolist()
        if missing_name_codes:
            msg = "Missing names for API symbols: {missing_names}"
            logger.warning(msg, missing_names=missing_name_codes)
        return all_data

    def api_symbol_with_labels(self) -> pd.DataFrame:
        """Backward-compatible alias for ``map_api_symbol_all_info``."""
        return self.map_api_symbol_all_info()
