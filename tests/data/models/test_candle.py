from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from trading_system.data.models import Candle, Instrument, Timeframe


@pytest.fixture
def instrument() -> Instrument:
    return Instrument(
        symbol="BTCUSDT",
        base_asset="BTC",
        quote_asset="USDT",
        exchange="BINANCE",
    )


def make_candle(instrument: Instrument, **overrides) -> Candle:
    values = {
        "instrument": instrument,
        "timeframe": Timeframe.M1,
        "open_time": datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
        "close_time": datetime(2026, 9, 1, 10, 1, tzinfo=timezone.utc),
        "open": Decimal("100"),
        "high": Decimal("110"),
        "low": Decimal("90"),
        "close": Decimal("105"),
        "volume": Decimal("2.5"),
        "quote_volume": Decimal("250"),
        "trade_count": 42,
        "taker_buy_base_volume": Decimal("1.2"),
        "taker_buy_quote_volume": Decimal("120"),
        "source": "binance",
        "is_closed": True,
    }
    values.update(overrides)
    return Candle(**values)


def test_valid_closed_candle_is_accepted(instrument):
    candle = make_candle(instrument)

    assert candle.close == Decimal("105")
    assert candle.open_time.tzinfo == timezone.utc
    assert candle.is_closed is True


def test_candle_rejects_naive_timestamps(instrument):
    with pytest.raises(ValidationError):
        make_candle(instrument, open_time=datetime(2026, 9, 1, 10, 0))


def test_candle_rejects_non_utc_timestamps(instrument):
    from datetime import timedelta

    non_utc = timezone(timedelta(hours=1))
    with pytest.raises(ValidationError):
        make_candle(instrument, open_time=datetime(2026, 9, 1, 10, 0, tzinfo=non_utc))


def test_candle_rejects_invalid_price_relationships(instrument):
    with pytest.raises(ValidationError):
        make_candle(instrument, high=Decimal("95"))

    with pytest.raises(ValidationError):
        make_candle(instrument, low=Decimal("106"))


def test_candle_rejects_non_positive_prices(instrument):
    with pytest.raises(ValidationError):
        make_candle(instrument, close=Decimal("0"))


def test_candle_rejects_non_positive_time_interval(instrument):
    with pytest.raises(ValidationError):
        make_candle(
            instrument,
            close_time=datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
        )
