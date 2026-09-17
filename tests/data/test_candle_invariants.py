from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from trading_system.data.models.candle import Candle
from trading_system.data.models.instrument import Instrument
from trading_system.data.models.timeframe import Timeframe


def make_candle(**overrides):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    values = dict(
        instrument=Instrument(symbol="BTCUSDT", exchange="binance"),
        timeframe=Timeframe("1h"),
        open_time=start,
        close_time=start + timedelta(hours=1),
        open=Decimal("100"), high=Decimal("110"), low=Decimal("90"), close=Decimal("105"),
        volume=Decimal("10"), quote_volume=Decimal("1000"), trade_count=10,
        taker_buy_base_volume=Decimal("5"), taker_buy_quote_volume=Decimal("500"),
        source="test", is_closed=True,
    )
    values.update(overrides)
    return Candle(**values)


def test_valid_candle() -> None:
    assert make_candle().close == Decimal("105")


def test_ohlc_relationships_are_enforced() -> None:
    with pytest.raises(ValidationError):
        make_candle(high=Decimal("99"))
    with pytest.raises(ValidationError):
        make_candle(low=Decimal("106"))


def test_close_must_follow_open() -> None:
    with pytest.raises(ValidationError):
        make_candle(close_time=datetime(2026, 1, 1, tzinfo=timezone.utc))


def test_negative_market_values_are_rejected() -> None:
    for field in ("open", "high", "low", "close"):
        with pytest.raises(ValidationError):
            make_candle(**{field: Decimal("-1")})


def test_negative_volume_and_trade_count_are_rejected() -> None:
    for field in ("volume", "quote_volume", "taker_buy_base_volume", "taker_buy_quote_volume", "trade_count"):
        with pytest.raises(ValidationError):
            make_candle(**{field: Decimal("-1") if field != "trade_count" else -1})


def test_candle_times_must_be_utc() -> None:
    naive = datetime(2026, 1, 1)
    with pytest.raises(ValidationError):
        make_candle(open_time=naive)
