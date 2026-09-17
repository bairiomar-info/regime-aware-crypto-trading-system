from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_system.backtest.candle_adapter import candles_to_market_bars
from trading_system.data.models import Candle, Instrument, MarketType, Timeframe


def _instrument() -> Instrument:
    return Instrument(symbol="BTCUSDT", base_asset="BTC", quote_asset="USDT", market_type=MarketType.SPOT, exchange="BINANCE")


def _candle(hour: int, open_price: str, close: str) -> Candle:
    return Candle(
        instrument=_instrument(),
        timeframe=Timeframe("1h"),
        open_time=datetime(2026, 9, 16, hour, tzinfo=timezone.utc),
        close_time=datetime(2026, 9, 16, hour, 59, 59, tzinfo=timezone.utc),
        open=Decimal(open_price),
        high=max(Decimal(open_price), Decimal(close)),
        low=min(Decimal(open_price), Decimal(close)),
        close=Decimal(close),
        volume=Decimal("1"),
        quote_volume=Decimal(close),
        trade_count=1,
    )


def test_candles_convert_to_market_bars_and_preserve_ohlc_inputs() -> None:
    bars = candles_to_market_bars((_candle(0, "99", "100"), _candle(1, "101", "102")))
    assert len(bars) == 2
    assert bars[0].open == Decimal("99")
    assert bars[0].close == Decimal("100")
    assert bars[1].open == Decimal("101")
    assert bars[1].close == Decimal("102")


def test_empty_candles_are_rejected() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        candles_to_market_bars(())
