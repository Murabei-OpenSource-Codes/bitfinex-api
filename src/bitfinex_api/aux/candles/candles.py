"""Bitfinex public candle history endpoints."""
import datetime
import re
from typing import Any

from loguru import logger

from bitfinex_api.exceptions import BitfinexAPIError, BitfinexAPIRequestError

ENDPOINT_CANDLES = "candles"
CANDLE_HIST_MAX_LIMIT = 10000

_BITFINEX_PERIOD_RE = re.compile(r"^(\d+)([mDhWM])$")


def build_hist_query_params(
        start_ms: int | None = None,
        end_ms: int | None = None,
        limit: int | None = None,
        sort: int | None = None) -> dict | None:
    """Build query string for Bitfinex ``/hist`` endpoints."""
    params: dict[str, int] = {}
    if start_ms is not None:
        params["start"] = start_ms
    if end_ms is not None:
        params["end"] = end_ms
    if limit is not None:
        params["limit"] = limit
    if sort is not None:
        params["sort"] = sort
    return params or None


def bitfinex_candle_period_to_ms(period: str) -> int:
    """Map a Bitfinex candle period string to bar length in milliseconds."""
    text = (period or "").strip()
    match = _BITFINEX_PERIOD_RE.match(text)
    if not match:
        msg = "Unsupported Bitfinex candle period: {period}"
        raise BitfinexAPIError(
            message=msg,
            payload={"period": text})
    count = int(match.group(1))
    unit = match.group(2)
    if unit == "m":
        return count * 60_000
    if unit == "h":
        return count * 3_600_000
    if unit == "D":
        return count * 86_400_000
    if unit == "W":
        return count * 7 * 86_400_000
    return count * 30 * 86_400_000


class BitfinexAPICandlesMixin:
    """Fetch trade candles from Bitfinex REST API v2."""

    def _raise_api_body_error(
            self,
            body: Any,
            *,
            path: str,
            symbol: str | None) -> None:
        """Raise when the JSON body carries a Bitfinex error field."""
        if not isinstance(body, dict) or not body.get("error"):
            return
        raise BitfinexAPIRequestError(
            message="Bitfinex API error for path={path}: {error}",
            payload={
                "path": path,
                "par": symbol,
                "error": body.get("error"),
            })

    def _fetch_candles_paginated(
            self,
            path: str,
            symbol: str,
            period: str,
            start_ms: int,
            end_ms: int) -> dict:
        """Fetch all candle bars between ``start_ms`` and ``end_ms``.

        Args:
            path (str):
                REST path under ``v2/`` (no leading slash).
            symbol (str):
                Full Bitfinex symbol, e.g. ``tBTCUSD``.
            period (str):
                Candle timeframe, e.g. ``1h``.
            start_ms (int):
                Inclusive lower bound (ms).
            end_ms (int):
                Inclusive upper bound (ms).

        Returns:
            dict:
                Envelope with ``par``, ``endpoint``, ``collected_at``,
                and ``body`` (list of candle rows).

        Raises:
            BitfinexAPIError:
                When pagination exceeds a safe page count.
            BitfinexAPIRequestError:
                On HTTP or API-level errors.
        """
        step_ms = bitfinex_candle_period_to_ms(period)
        cursor = start_ms
        merged: list = []
        collected_at: str | None = None
        span_ms = max(end_ms - start_ms, step_ms)
        max_pages = span_ms // (step_ms * CANDLE_HIST_MAX_LIMIT) + 3
        pages = 0
        while cursor <= end_ms:
            pages += 1
            if pages > max_pages:
                msg = (
                    "Candle pagination exceeded safe page count "
                    "for par={par}")
                raise BitfinexAPIError(
                    message=msg,
                    payload={
                        "endpoint": ENDPOINT_CANDLES,
                        "par": symbol,
                        "pages": pages,
                    })
            params = build_hist_query_params(
                start_ms=cursor,
                end_ms=end_ms,
                limit=CANDLE_HIST_MAX_LIMIT,
                sort=1)
            stamp = datetime.datetime.now(
                datetime.timezone.utc).isoformat()
            body = self.get(endpoint=path, query_params=params)
            self._raise_api_body_error(
                body, path=path, symbol=symbol)
            if collected_at is None:
                collected_at = stamp
            batch = body or []
            if not batch:
                break
            merged.extend(batch)
            if len(batch) < CANDLE_HIST_MAX_LIMIT:
                break
            last_mts = batch[-1][0]
            cursor = last_mts + step_ms
        logger.info(
            "Candles fetched par={par} bars={n} pages={pages}",
            par=symbol,
            n=len(merged),
            pages=pages,
        )
        if collected_at is None:
            collected_at = datetime.datetime.now(
                datetime.timezone.utc).isoformat()
        return {
            "par": symbol,
            "endpoint": ENDPOINT_CANDLES,
            "collected_at": collected_at,
            "body": merged,
        }

    def get_candles(
            self,
            symbol: str,
            period: str,
            *,
            limit: int | None = None,
            start_ms: int | None = None,
            end_ms: int | None = None,
            section: str = "hist") -> dict:
        """Fetch candle history for one trading pair.

        Uses ``GET /v2/candles/trade:{period}:{symbol}/{section}``.

        Args:
            symbol (str):
                Full Bitfinex symbol, e.g. ``tBTCUSD``.
            period (str):
                Timeframe, e.g. ``1m``, ``1h``, ``1D``.
            limit (int | None):
                Cap on bars (API max 10000). When ``start_ms`` and
                ``end_ms`` are set and ``limit`` is omitted, all bars
                in the window are paginated.
            start_ms (int | None):
                Bars with ``MTS >= start``.
            end_ms (int | None):
                Bars with ``MTS <= end``.
            section (str):
                ``hist`` or ``last``.

        Returns:
            dict:
                Envelope with ``par``, ``endpoint``, ``collected_at``,
                and ``body`` (list of candle rows).

        Raises:
            BitfinexAPIError:
                On invalid period or pagination guard.
            BitfinexAPIRequestError:
                On HTTP or API-level errors.
        """
        path = "candles/trade:{period}:{symbol}/{section}".format(
            period=period, symbol=symbol, section=section)
        if (section == "hist" and start_ms is not None
                and end_ms is not None and limit is None):
            return self._fetch_candles_paginated(
                path=path,
                symbol=symbol,
                period=period,
                start_ms=start_ms,
                end_ms=end_ms)
        params = build_hist_query_params(
            start_ms=start_ms, end_ms=end_ms, limit=limit)
        collected_at = datetime.datetime.now(
            datetime.timezone.utc).isoformat()
        logger.info(
            "Bitfinex GET endpoint={endpoint} par={par}",
            endpoint=ENDPOINT_CANDLES,
            par=symbol,
        )
        body = self.get(endpoint=path, query_params=params)
        self._raise_api_body_error(body, path=path, symbol=symbol)
        return {
            "par": symbol,
            "endpoint": ENDPOINT_CANDLES,
            "collected_at": collected_at,
            "body": body,
        }
