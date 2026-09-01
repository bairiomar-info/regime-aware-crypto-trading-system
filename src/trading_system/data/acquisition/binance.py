"""Binance Spot REST historical kline adapter.

This module owns transport concerns only. It converts Binance kline pages into
canonical candles through the existing pure normalizer and never writes data.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..models import Candle, Instrument, Timeframe
from ..normalization.binance import BinanceKlineNormalizer, BinanceRawKline
from .retry import RetryPolicy


class BinanceAdapterError(RuntimeError):
    """Base error for Binance historical-data acquisition."""


class BinanceHTTPError(BinanceAdapterError):
    """Non-retryable Binance HTTP/API error."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"Binance HTTP {status}: {message}")
        self.status = status
        self.message = message


class BinanceRateLimitError(BinanceAdapterError):
    """Raised when Binance asks the client to back off after a rate limit."""

    def __init__(self, status: int, retry_after: float | None) -> None:
        super().__init__(f"Binance rate limit response: HTTP {status}")
        self.status = status
        self.retry_after = retry_after


class BinanceTransportError(BinanceAdapterError):
    """Raised when the HTTP transport cannot reach Binance."""


Transport = Callable[[str], tuple[int, Mapping[str, str], bytes]]
Sleeper = Callable[[float], None]
Clock = Callable[[], datetime]


_INTERVAL_MS: dict[Timeframe, int] = {
    Timeframe.M1: 60_000,
    Timeframe.M5: 300_000,
    Timeframe.M15: 900_000,
    Timeframe.H1: 3_600_000,
    Timeframe.H4: 14_400_000,
    Timeframe.D1: 86_400_000,
}


class BinanceKlineClient:
    """Fetch Binance Spot klines and return canonical candles."""

    endpoint = "/api/v3/klines"
    max_limit = 1000

    def __init__(
        self,
        *,
        base_url: str = "https://api.binance.com",
        retry_policy: RetryPolicy | None = None,
        transport: Transport | None = None,
        sleeper: Sleeper = time.sleep,
        clock: Clock = lambda: datetime.now(timezone.utc),
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.retry_policy = retry_policy or RetryPolicy()
        self.transport = transport or self._default_transport
        self.sleeper = sleeper
        self.clock = clock
        self.normalizer = BinanceKlineNormalizer()

    def fetch(
        self,
        *,
        instrument: Instrument,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
    ) -> list[Candle]:
        """Fetch the complete requested range using deterministic pagination."""
        self._validate_range(start, end)
        cursor_ms = self._to_ms(start)
        end_ms = self._to_ms(end)
        interval_ms = _INTERVAL_MS[timeframe]
        candles: list[Candle] = []

        while cursor_ms <= end_ms:
            rows = self._request_page(
                symbol=instrument.symbol,
                interval=timeframe.value,
                start_ms=cursor_ms,
                end_ms=end_ms,
            )
            if not rows:
                break

            for row in rows:
                raw = self._parse_row(row)
                if raw.open_time_ms < self._to_ms(start) or raw.open_time_ms > end_ms:
                    continue
                candles.append(
                    self.normalizer.normalize(
                        raw,
                        instrument=instrument,
                        timeframe=timeframe,
                        is_closed=self._to_ms(self.clock()) > raw.close_time_ms,
                    )
                )

            last_open_ms = int(rows[-1][0])
            next_cursor = last_open_ms + interval_ms
            if next_cursor <= cursor_ms:
                raise BinanceAdapterError("Binance pagination did not advance")
            cursor_ms = next_cursor

            if len(rows) < self.max_limit:
                break

        return candles

    def _request_page(self, *, symbol: str, interval: str, start_ms: int, end_ms: int) -> list[list[Any]]:
        query = urlencode(
            {
                "symbol": symbol,
                "interval": interval,
                "startTime": start_ms,
                "endTime": end_ms,
                "limit": self.max_limit,
            }
        )
        url = f"{self.base_url}{self.endpoint}?{query}"

        for attempt in range(1, self.retry_policy.max_attempts + 1):
            try:
                status, headers, body = self.transport(url)
            except (URLError, TimeoutError, OSError) as exc:
                if attempt == self.retry_policy.max_attempts:
                    raise BinanceTransportError(str(exc)) from exc
                self.sleeper(self.retry_policy.delay_seconds(attempt))
                continue

            if status in (418, 429):
                retry_after = self._retry_after(headers)
                if attempt == self.retry_policy.max_attempts:
                    raise BinanceRateLimitError(status, retry_after)
                self.sleeper(retry_after if retry_after is not None else self.retry_policy.delay_seconds(attempt))
                continue

            if 500 <= status < 600:
                if attempt == self.retry_policy.max_attempts:
                    raise BinanceHTTPError(status, body.decode("utf-8", errors="replace"))
                self.sleeper(self.retry_policy.delay_seconds(attempt))
                continue

            if status < 200 or status >= 300:
                raise BinanceHTTPError(status, self._error_message(body))

            try:
                payload = json.loads(body)
            except json.JSONDecodeError as exc:
                raise BinanceAdapterError("Binance returned invalid JSON") from exc
            if not isinstance(payload, list):
                raise BinanceAdapterError("Binance kline response must be a JSON array")
            return payload

        raise BinanceAdapterError("Binance request exhausted retries")

    @staticmethod
    def _default_transport(url: str) -> tuple[int, Mapping[str, str], bytes]:
        request = Request(url, headers={"Accept": "application/json"}, method="GET")
        try:
            with urlopen(request, timeout=15) as response:
                return response.status, dict(response.headers.items()), response.read()
        except HTTPError as exc:
            return exc.code, dict(exc.headers.items()), exc.read()

    @staticmethod
    def _parse_row(row: Any) -> BinanceRawKline:
        if not isinstance(row, list) or len(row) < 11:
            raise BinanceAdapterError("Malformed Binance kline row")
        try:
            values = [row[i] for i in range(11)]
            return BinanceRawKline(
                open_time_ms=int(values[0]),
                open=str(values[1]),
                high=str(values[2]),
                low=str(values[3]),
                close=str(values[4]),
                volume=str(values[5]),
                close_time_ms=int(values[6]),
                quote_volume=str(values[7]),
                trade_count=int(values[8]),
                taker_buy_base_volume=str(values[9]),
                taker_buy_quote_volume=str(values[10]),
            )
        except (TypeError, ValueError, IndexError) as exc:
            raise BinanceAdapterError("Malformed Binance kline row values") from exc

    @staticmethod
    def _retry_after(headers: Mapping[str, str]) -> float | None:
        value = next((v for k, v in headers.items() if k.lower() == "retry-after"), None)
        if value is None:
            return None
        try:
            return max(0.0, float(value))
        except ValueError:
            return None

    @staticmethod
    def _error_message(body: bytes) -> str:
        try:
            payload = json.loads(body)
            if isinstance(payload, dict) and "msg" in payload:
                return str(payload["msg"])
        except json.JSONDecodeError:
            pass
        return body.decode("utf-8", errors="replace")

    @staticmethod
    def _validate_range(start: datetime, end: datetime) -> None:
        if start.tzinfo is None or start.utcoffset() is None or end.tzinfo is None or end.utcoffset() is None:
            raise ValueError("historical-data bounds must be timezone-aware")
        if end <= start:
            raise ValueError("historical-data end must be after start")

    @staticmethod
    def _to_ms(value: datetime) -> int:
        return int(value.timestamp() * 1000)
