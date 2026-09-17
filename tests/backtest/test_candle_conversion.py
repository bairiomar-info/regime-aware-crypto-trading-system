from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_system.backtest.candle_conversion import rows_to_candles
from trading_system.data.models import Instrument, MarketType, Timeframe


def _instrument() -> Instrument:
    return Instrument(symbol="BTCUSDT", base_asset="BTC", quote_asset="USDT", market_type=MarketType.SPOT, exchange="BINANCE")


def _row(hour: int) -> dict:
    timestamp = datetime(2026, 9, 16, hour, tzinfo=timezone.utc)
    return {
        "open_time": timestamp,
        "close_time": timestamp.replace(minute=59),
        "open": Decimal("100"),
        "high": Decimal("101"),
        "low": Decimal("99"),
        "close": Decimal("100"),
        "volume": Decimal("1"),
        "quote_volume": Decimal("100"),
        "trade_count": 1,
        "taker_buy_base_volume": Decimal("0.5"),
        "taker_buy_quote_volume": Decimal("50"),
        "is_closed": True,
    }


def test_rows_convert_to_validated_candles() -> None:
    candles = rows_to_candles(
        (_row(0), _row(1)),
        instrument=_instrument(),
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
            instrument=_instrument(),
            timeframe=Timeframe("1h"),
            source="test.parquet",
        )
