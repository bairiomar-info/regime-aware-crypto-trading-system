from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_system.backtest.candle_conversion import rows_to_candles
from trading_system.data.models import Instrument, Timeframe


def _row(hour: int) -> dict:
    timestamp = datetime(2026, 9, 16, hour, tzinfo=timezone.utc)
    return {
        "open_time": timestamp,
        "close_time": timestamp,
        "open": Decimal("100"),
        "high": Decimal("101"),
        "low": Decimal("99"),
        "close": Decimal("100"),
        "volume": Decimal("1"),
        "quote_volume": Decimal("100"),
        "trade_count": 1,
    }


def test_rows_convert_to_validated_candles() -> None:
    candles = rows_to_candles(
        (_row(0), _row(1)),
        instrument=Instrument(symbol="BTCUSDT", venue="binance"),
        timeframe=Timeframe("1h"),
        source="test.parquet",
    )
    assert len(candles) == 2
    assert candles[0].open == Decimal("100")
    assert candles[1].close == Decimal("100")
    assert candles[0].source == "test.parquet"


def test_empty_rows_are_rejected() -> None:
    with pytest.raises(ValueError, match="at least one candle"):
        rows_to_candles(
            (),
            instrument=Instrument(symbol="BTCUSDT", venue="binance"),
            timeframe=Timeframe("1h"),
            source="test.parquet",
        )
