from datetime import UTC, datetime

import pytest

from trading_system.data.acquisition.binance import (
    BinanceAdapterError,
    BinanceHTTPError,
    BinanceKlineClient,
    BinanceRateLimitError,
)
from trading_system.data.models import Instrument, MarketType, Timeframe
from trading_system.data.acquisition.retry import RetryPolicy


START = datetime(2026, 1, 1, tzinfo=UTC)
END = datetime(2026, 1, 1, 1, tzinfo=UTC)
INSTRUMENT = Instrument(
    symbol="BTCUSDT",
    base_asset="BTC",
    quote_asset="USDT",
    market_type=MarketType.SPOT,
    exchange="BINANCE",
)


def row(open_ms: int, close_ms: int) -> list[object]:
    return [open_ms, "100.0", "110.0", "90.0", "105.0", "12.5", close_ms, "1300.0", 42, "6.0", "630.0", "0"]


def test_fetch_builds_correct_kline_request():
    calls: list[str] = []
    def transport(url: str):
        calls.append(url)
        return 200, {}, b"[]"
    client = BinanceKlineClient(transport=transport)
    assert client.fetch(instrument=INSTRUMENT, timeframe=Timeframe.H1, start=START, end=END) == []
    assert len(calls) == 1
    assert "symbol=BTCUSDT" in calls[0]
    assert "interval=1h" in calls[0]
    assert "limit=1000" in calls[0]
    assert "startTime=1767225600000" in calls[0]


def test_fetch_normalizes_binance_rows_to_canonical_candles():
    transport = lambda url: (200, {}, str([row(1767225600000, 1767229199999)]).replace("'", '"').encode())
    client = BinanceKlineClient(transport=transport, clock=lambda: datetime(2026, 1, 2, tzinfo=UTC))
    candles = client.fetch(instrument=INSTRUMENT, timeframe=Timeframe.H1, start=START, end=END)
    assert len(candles) == 1
    assert candles[0].instrument.symbol == "BTCUSDT"
    assert str(candles[0].close) == "105.0"
    assert candles[0].is_closed is True


def test_malformed_kline_row_is_rejected():
    client = BinanceKlineClient(transport=lambda url: (200, {}, b"[[1,2]]"))
    with pytest.raises(BinanceAdapterError, match="Malformed Binance kline row"):
        client.fetch(instrument=INSTRUMENT, timeframe=Timeframe.H1, start=START, end=END)


def test_non_retryable_http_error_is_exposed():
    body = b'{"code":-1121,"msg":"Invalid symbol."}'
    client = BinanceKlineClient(transport=lambda url: (400, {}, body))
    with pytest.raises(BinanceHTTPError) as exc:
        client.fetch(instrument=INSTRUMENT, timeframe=Timeframe.H1, start=START, end=END)
    assert exc.value.status == 400
    assert "Invalid symbol" in str(exc.value)


def test_rate_limit_uses_retry_after():
    calls = 0
    sleeps: list[float] = []
    def transport(url: str):
        nonlocal calls
        calls += 1
        if calls == 1:
            return 429, {"Retry-After": "3"}, b'{"msg":"too many requests"}'
        return 200, {}, b"[]"
    client = BinanceKlineClient(transport=transport, sleeper=sleeps.append, retry_policy=RetryPolicy(max_attempts=2))
    assert client.fetch(instrument=INSTRUMENT, timeframe=Timeframe.H1, start=START, end=END) == []
    assert sleeps == [3.0]
    assert calls == 2


def test_repeated_rate_limit_eventually_raises():
    client = BinanceKlineClient(transport=lambda url: (429, {"Retry-After": "1"}, b"{}"), sleeper=lambda _: None, retry_policy=RetryPolicy(max_attempts=2))
    with pytest.raises(BinanceRateLimitError):
        client.fetch(instrument=INSTRUMENT, timeframe=Timeframe.H1, start=START, end=END)


def test_pagination_advances_by_interval_without_duplicates():
    starts = [1767225600000, 1767229200000]
    pages = [[row(starts[0], starts[0] + 3599999)] * 1000, [row(starts[1], starts[1] + 3599999)]]
    calls: list[str] = []
    def transport(url: str):
        calls.append(url)
        return 200, {}, str(pages[len(calls) - 1]).replace("'", '"').encode()
    client = BinanceKlineClient(transport=transport)
    candles = client.fetch(instrument=INSTRUMENT, timeframe=Timeframe.H1, start=START, end=datetime(2026, 1, 1, 2, tzinfo=UTC))
    assert len(candles) == 1001
    assert len(calls) == 2
    assert "startTime=1767229200000" in calls[1]


def test_invalid_time_range_is_rejected_before_transport():
    called = False
    def transport(url: str):
        nonlocal called
        called = True
        return 200, {}, b"[]"
    client = BinanceKlineClient(transport=transport)
    with pytest.raises(ValueError):
        client.fetch(instrument=INSTRUMENT, timeframe=Timeframe.H1, start=END, end=START)
    assert called is False
