"""Split Bitfinex pair codes into base and quote legs."""
import pandas as pd
from loguru import logger

from bitfinex_api.aux.config.contracts import PairSymbolsContract
from bitfinex_api.exceptions import BitfinexAPIInvalidParametersError


class TreatmentPairSymbols:
    """Treatment of pair symbols."""

    QUOTE_PAIR_COLUMNS: tuple[str, ...] = tuple(
        PairSymbolsContract.model_fields.keys())
    """DataFrame columns aligned with ``PairSymbolsContract``."""

    @staticmethod
    def split_trading_prefix(symbol: str) -> tuple[str | None, str]:
        """Split leading ``t`` or ``f`` from a REST pair symbol.

        Args:
            symbol (str):
                Value from ``pub:list:pair`` or candle ``par``.

        Returns:
            tuple[str | None, str]:
                Trading prefix (``t`` or ``f``) and legs without prefix.
        """
        text = (symbol or "").strip()
        if len(text) > 1 and text[0] in ("t", "f"):
            return text[0], text[1:]
        return None, text

    @classmethod
    def split_pair_list(
            cls,
            currency_pair_list: list[str],
            currency_codes: list[str]) -> pd.DataFrame:
        """Split pair codes into base and quote assets.

        Args:
            currency_pair_list (list[str]):
                Symbols from ``pub:list:pair``.
            currency_codes (list[str]):
                Platform currencies from ``pub:list:currency``.

        Returns:
            pd.DataFrame:
                One row per pair; columns match ``PairSymbolsContract``.
        """
        rows = [
            cls.split_pair(pair, currency_codes).model_dump()
            for pair in currency_pair_list
        ]
        return pd.DataFrame(rows, columns=list(cls.QUOTE_PAIR_COLUMNS))

    @classmethod
    def split_pair(
            cls,
            pair: str,
            currency_codes: list[str]) -> PairSymbolsContract:
        """Parse base and quote assets from one pair code.

        Colon notation (``DOGE:USD``) splits on the first colon. Concatenated
        notation (``BTCUSD``) matches the longest known quote suffix from
        ``currency_codes``.

        Args:
            pair (str):
                Bitfinex pair (with or without leading ``t``/``f``).
            currency_codes (list[str]):
                Platform currencies from ``pub:list:currency``.

        Returns:
            PairSymbolsContract:
                Validated instrument and leg fields.

        Raises:
            BitfinexAPIInvalidParametersError:
                When the pair cannot be split.
        """
        instrument = (pair or "").strip()
        if instrument == "":
            msg = "Empty Bitfinex pair symbol."
            raise BitfinexAPIInvalidParametersError(message=msg)

        trading_prefix, legs = cls.split_trading_prefix(symbol=instrument)
        if ":" in legs:
            base, quote = legs.split(":", 1)
            if base == "" or quote == "":
                msg = "Invalid colon pair symbol: {pair}"
                raise BitfinexAPIInvalidParametersError(
                    message=msg,
                    payload={"pair": instrument})
            return PairSymbolsContract(
                instrument=instrument,
                trading_prefix=trading_prefix,
                pair=legs,
                base=base,
                quote=quote)

        quotes = sorted({
            code.strip().upper()
            for code in currency_codes
            if code.strip()},
            key=len,
            reverse=True)

        legs_upper = legs.upper()
        for quote_upper in quotes:
            q_len = len(quote_upper)
            if q_len == 0 or len(legs_upper) <= q_len:
                continue

            if legs_upper.endswith(quote_upper):
                base = legs[:-q_len]
                quote = legs[-q_len:]
                if base == "":
                    continue
                return PairSymbolsContract(
                    instrument=instrument,
                    trading_prefix=trading_prefix,
                    pair=legs,
                    base=base,
                    quote=quote)

        msg = "Could not split pair into base and quote: {pair}"
        logger.warning(msg, pair=instrument)
        raise BitfinexAPIInvalidParametersError(
            message=msg,
            payload={"pair": instrument})
