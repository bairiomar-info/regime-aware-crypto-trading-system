from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_system.backtest.candle_adapter import candles_to_market_bars
from trading_system.data.models import Candle, Instrument, Timeframe


def _candle(hour: int, close: str) -> Candle:
    return Candle(
        instrument=Instrument(symbol="BTCUSDT", venue="binance"),
        timeframe=Timeframe("1h"),
        open_time=datetime(2026, 9, 16, hour, tzinfo=timezone.utc),
        close_time=datetime(2026, 9, 16, hour, 59, 59, tzinfo=timezone.utc),
        open=Decimal(close),
        high=Decimal(close),
        low=Decimal(close),
        close=Decimal(close),
        volume=Decimal("1"),
        quote_volume=Decimal(close),
        trade_count=1,
    )


def test_candles_convert_to_market_bars() -> None:
    bars = candles_to_market_bars((_candle(0, "100"), _candle(1, "101")))
    assert len(bars) == 2
    assert bars[0].close == Decimal("100")
    assert bars[1].close == Decimal("101")


def test_empty_candles_are_rejected() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        candles_to_market_bars(())
