"""Parse Bitfinex ``conf`` map payloads into dictionaries."""
from typing import Any

import pandas as pd


def conf_slot_pairs_to_dict(entries: Any) -> dict[str, Any]:
    """Turn ``[[code, value], ...]`` into a lookup dict.

    Args:
        entries (Any):
            One slot from a multi-key ``GET /v2/conf/...`` body.

    Returns:
        dict[str, Any]:
            Keys are currency codes; values are map payloads.
    """
    if not isinstance(entries, list):
        return {}
    result: dict[str, Any] = {}
    for row in entries:
        if not isinstance(row, list) or len(row) < 2:
            continue
        code = str(row[0]).strip()
        if code == "":
            continue
        result[code] = row[1]
    return result


def derivative_currency_codes(undl_map: dict[str, Any]) -> set[str]:
    """Return derivative instrument codes (``undl`` map keys)."""
    return set(undl_map.keys())


CURRENCY_NAME_OVERRIDES: dict[str, str] = {
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


def apply_currency_name_overrides(
        frame: pd.DataFrame,
        *,
        code_column: str = "api_symbol",
        name_column: str = "name",
        overrides: dict[str, str] | None = None) -> pd.DataFrame:
    """Fill blank ``name`` values from ``CURRENCY_NAME_OVERRIDES``."""
    if not isinstance(frame, pd.DataFrame):
        msg = "frame must be a pandas DataFrame."
        raise TypeError(msg)
    lookup = overrides if overrides is not None else CURRENCY_NAME_OVERRIDES
    if name_column not in frame.columns:
        return frame
    out = frame.copy()
    codes = out[code_column].astype(str).str.upper()
    missing = out[name_column].isna()
    out.loc[missing, name_column] = codes.map(lookup)
    return out
