"""Bitfinex ``conf/pub:map:*`` currency map endpoints."""
import pandas as pd
from loguru import logger
from bitfinex_api.aux.config.config_base import BitfinexAPIConfigBaseMixin
from bitfinex_api.exceptions import (
    BitfinexAPINoneResponseError,
    BitfinexAPIDataValidationError)


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


class BitfinexAPIConfigMapMixin(BitfinexAPIConfigBaseMixin):
    """One HTTP call per ``pub:map`` config key."""

    API_CURRENCY_SYMBOLS_COLUMNS: tuple[str, ...] = (
        "api_symbol", "currency_symbol")
    """DataFrame columns for ``conf/pub:map:currency:sym``.

    ``api_symbol`` is the platform wallet code (e.g. ``DSH``).
    ``currency_symbol`` is the symbol Bitfinex uses in APIs (e.g. ``DASH``).
    """

    API_SYMBOL_NAMES_COLUMNS: tuple[str, ...] = (
        "api_symbol", "name")
    """DataFrame columns for ``conf/pub:map:currency:label``.

    ``api_symbol`` is the wallet code; ``name`` is the display label
    (e.g. ``BTC`` → ``Bitcoin``).
    """

    API_SYMBOL_UNDERLYING_COLUMNS: tuple[str, ...] = (
        "derivative_api_symbol", "underlying_api_symbol")
    """DataFrame columns for ``conf/pub:map:currency:undl``.

    Maps a derivative code (e.g. ``BTCF0``) to its underlying (e.g. ``BTC``).
    """

    API_SYMBOL_CURRENCY_POOL_COLUMNS: tuple[str, ...] = (
        "api_symbol", "currency_pool")
    """DataFrame columns for ``conf/pub:map:currency:pool``.

    ``currency_pool`` is the parent network for the asset (e.g. ``BAT``
    → ``ETH``).
    """

    API_SYMBOL_CURRENCY_EXPLORER_COLUMNS: tuple[str, ...] = (
        "api_symbol", "currency_explorer_url_list")
    """DataFrame columns for ``conf/pub:map:currency:explorer``.

    ``currency_explorer_url_list`` is a list of block explorer URLs.
    """

    API_SYMBOL_CURRENCY_TX_FEE_COLUMNS: tuple[str, ...] = (
        "api_symbol", "withdrawal_fee")
    """DataFrame columns for ``conf/pub:map:currency:tx:fee``.

    ``withdrawal_fee`` is taken from the second value in each fee pair
    (amount charged in units of ``api_symbol``).
    """

    API_SYMBOL_CURRENCY_WITHDRAWAL_METHOD_COLUMNS: tuple[str, ...] = (
        "api_symbol", "currency_withdrawal_methods")
    """DataFrame columns built from ``conf/pub:map:tx:method``.

    Bitfinex returns method → codes; we invert to one row per
    ``api_symbol`` with a list of withdrawal ``method`` ids (rails).
    """

    API_SYMBOL_ALL_COLUMNS: tuple[str, ...] = (
        'api_symbol', 'is_derivative', 'underlying_api_symbol',
        'currency_symbol', 'name', 'currency_pool',
        'currency_explorer_url_list', 'withdrawal_fee',
        'currency_withdrawal_methods')
    """DataFrame columns for all the maps."""

    def map_api_currency_symbol(self) -> pd.DataFrame:
        """``pub:map:currency:sym`` — platform code → wallet symbol."""
        endpoint = "conf/pub:map:currency:sym"
        body = self.unwrap_response(self.get(endpoint=endpoint))
        if body is None:
            raise BitfinexAPINoneResponseError(
                message="No response body from {endpoint}.",
                payload={"endpoint": endpoint})
        frame = pd.DataFrame(
            body, columns=self.API_CURRENCY_SYMBOLS_COLUMNS)
        return frame.sort_values("api_symbol").reset_index(drop=True)

    def map_api_symbol_names(self) -> pd.DataFrame:
        """``pub:map:currency:label`` — platform code → display name."""
        endpoint = "conf/pub:map:currency:label"
        body = self.unwrap_response(self.get(endpoint=endpoint))
        if body is None:
            raise BitfinexAPINoneResponseError(
                message="No response body from {endpoint}.",
                payload={"endpoint": endpoint})
        frame = pd.DataFrame(
            body, columns=self.API_SYMBOL_NAMES_COLUMNS)
        return frame.sort_values("api_symbol").reset_index(drop=True)

    def map_api_currency_symbol_with_names(self) -> pd.DataFrame:
        """``map_api_currency_symbol`` plus label backfill for sym-only codes."""
        symbol_name_map = self.map_api_symbol_names()
        currency_symbol_map = self.map_api_currency_symbol()

        # Use the currency symbol to join the symbol name map
        # some api are not normalized or are derivatives.
        merged = currency_symbol_map.merge(
            symbol_name_map, on="api_symbol", how="left")
        is_na_name = merged.loc[:, "name"].isna()
        missing_names = merged.loc[is_na_name, :].drop(columns=["name"])
        to_merge_missing = symbol_name_map.rename(
            columns={"api_symbol": "currency_symbol"})
        missing_with_names = missing_names.merge(
            to_merge_missing, on="currency_symbol", how="left")

        # Still some missing, they will be filled directly from the map
        # dictionary.
        is_na_name_last_resort = missing_with_names.loc[:, "name"].isna()
        missing_with_names.loc[is_na_name_last_resort, "name"] = (
            missing_with_names.loc[is_na_name_last_resort, "api_symbol"]
            .map(API_SYMBOL_NAME_COMPLEMENT_MAP))

        # Join both results and validate if eventually there are duplicates
        # or missing names. The missing name will be logged to futter
        # adjust of the package.
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

    def map_api_symbol_derivative_underlyings(self) -> pd.DataFrame:
        """``pub:map:currency:undl`` — derivative → underlying."""
        endpoint = "conf/pub:map:currency:undl"
        body = self.unwrap_response(self.get(endpoint=endpoint))
        if body is None:
            raise BitfinexAPINoneResponseError(
                message="No response body from {endpoint}.",
                payload={"endpoint": endpoint})
        return pd.DataFrame(
            body, columns=self.API_SYMBOL_UNDERLYING_COLUMNS)

    def map_api_symbol_currency_pool(self) -> pd.DataFrame:
        """``pub:map:currency:pool`` — token → parent network code."""
        endpoint = "conf/pub:map:currency:pool"
        body = self.unwrap_response(self.get(endpoint=endpoint))
        if body is None:
            raise BitfinexAPINoneResponseError(
                message="No response body from {endpoint}.",
                payload={"endpoint": endpoint})
        return pd.DataFrame(
            body, columns=self.API_SYMBOL_CURRENCY_POOL_COLUMNS)

    def map_api_symbol_currency_explorer(self) -> pd.DataFrame:
        """``pub:map:currency:explorer`` — code → explorer URL list."""
        endpoint = "conf/pub:map:currency:explorer"
        body = self.unwrap_response(self.get(endpoint=endpoint))
        if body is None:
            raise BitfinexAPINoneResponseError(
                message="No response body from {endpoint}.",
                payload={"endpoint": endpoint})
        return pd.DataFrame(
            body, columns=self.API_SYMBOL_CURRENCY_EXPLORER_COLUMNS)

    def map_api_symbol_withdrawal_fee(self) -> pd.DataFrame:
        """``pub:map:currency:tx:fee`` — code → withdrawal fee."""
        endpoint = "conf/pub:map:currency:tx:fee"
        body = self.unwrap_response(self.get(endpoint=endpoint))
        if body is None:
            raise BitfinexAPINoneResponseError(
                message="No response body from {endpoint}.",
                payload={"endpoint": endpoint})
        rows = [
            {"api_symbol": row[0], "withdrawal_fee": row[1][1]}
            for row in body
            if isinstance(row, list) and len(row) >= 2
        ]
        return pd.DataFrame(
            rows, columns=self.API_SYMBOL_CURRENCY_TX_FEE_COLUMNS)

    def map_api_symbol_withdrawal_method(self) -> pd.DataFrame:
        """``pub:map:tx:method`` inverted to code → method ids."""
        endpoint = "conf/pub:map:tx:method"
        body = self.unwrap_response(self.get(endpoint=endpoint))
        if body is None:
            raise BitfinexAPINoneResponseError(
                message="No response body from {endpoint}.",
                payload={"endpoint": endpoint})
        symbol_to_methods: dict[str, list[str]] = {}
        for method, api_symbols in body:
            for api_symbol in api_symbols:
                bucket = symbol_to_methods.setdefault(api_symbol, [])
                bucket.append(method)
        rows = [
            {
                "api_symbol": api_symbol,
                "currency_withdrawal_methods": methods,
            }
            for api_symbol, methods in symbol_to_methods.items()
        ]
        return pd.DataFrame(
            rows, columns=self.API_SYMBOL_CURRENCY_WITHDRAWAL_METHOD_COLUMNS)

    def map_api_symbol_all(self) -> pd.DataFrame:
        """Left-join every map table on ``api_symbol`` (one row per code)."""
        # Get the currency symbol with names due to the treatment of the
        # missing names for some api symbols.
        currency_symbol = self.map_api_currency_symbol_with_names()
        symbol_underlying = self.map_api_symbol_derivative_underlyings()

        # Use the underlying symbol to join all the other maps
        # the currency symbol and the underlying symbol
        # 'api_symbol_original' is created to preserve the original symbol
        # for derivatives to aling if exchange information.
        merged = currency_symbol\
            .merge(
                symbol_underlying,
                left_on="api_symbol", right_on="derivative_api_symbol",
                how="left", indicator=True)\
                .rename(columns={"api_symbol": "api_symbol_original"})
        merged['is_derivative'] = merged['_merge'] == "both"
        merged['api_symbol'] = merged["api_symbol_original"]\
            .mask(merged["is_derivative"], merged["underlying_api_symbol"])
        merged = merged.drop(
            columns=["derivative_api_symbol", "_merge"])

        # Add other information
        # Many to one merges are necessary since the defivative will have same
        # api_symbol for now as the underlying symbol.
        symbol_pool = self.map_api_symbol_currency_pool()
        merged = merged.merge(
            symbol_pool, on="api_symbol", how="left",
            validate="many_to_one")

        symbol_explorer = self.map_api_symbol_currency_explorer()
        merged = merged.merge(
            symbol_explorer, on="api_symbol", how="left",
            validate="many_to_one")

        symbol_withdrawal_fee = self.map_api_symbol_withdrawal_fee()
        merged = merged.merge(
            symbol_withdrawal_fee, on="api_symbol", how="left",
            validate="many_to_one")

        symbol_withdrawal_method = self.map_api_symbol_withdrawal_method()
        merged = merged.merge(
            symbol_withdrawal_method, on="api_symbol", how="left",
            validate="many_to_one")

        return_df = merged\
            .drop(columns=["api_symbol"])\
            .rename(columns={"api_symbol_original": "api_symbol"})

        # Validate all symbols are present in the return dataframe.
        if len(return_df) != len(currency_symbol):
            message = (
                "Information merge from the map tables is not correct. "
                "Currency symbol count [{n_currency_symbol}], "
                "return df count [{n_return_df}].")
            raise BitfinexAPIDataValidationError(
                message=message,
                payload={
                    "n_currency_symbol": len(currency_symbol),
                    "n_return_df": len(return_df)})

        # Validate if eventually there are duplicates or missing names.
        value_count_api_symbol = return_df["api_symbol"]\
            .value_counts()
        if not (value_count_api_symbol == 1).all():
            duplicates = value_count_api_symbol[
                value_count_api_symbol != 1].index.tolist()
            msg = "Duplicate api_symbols: {duplicates}"
            raise BitfinexAPIDataValidationError(
                message=msg, payload={"duplicates": duplicates})
        return return_df.sort_values("currency_symbol").reset_index(drop=True)
