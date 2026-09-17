from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_system.backtest.dataset_loader import load_candle_dataset
from trading_system.data.models import Instrument, MarketType, Timeframe


def _instrument() -> Instrument:
    return Instrument(symbol="BTCUSDT", base_asset="BTC", quote_asset="USDT", market_type=MarketType.SPOT, exchange="BINANCE")


def test_dataset_loader_composes_with_canonical_candle_conversion(tmp_path) -> None:
    pyarrow = pytest.importorskip("pyarrow")
    table = pyarrow.table(
        {
            "open_time": [datetime(2026, 9, 16, 0, tzinfo=timezone.utc)],
            "close_time": [datetime(2026, 9, 16, 0, 59, tzinfo=timezone.utc)],
            "open": [Decimal("100")],
            "high": [Decimal("101")],
            "low": [Decimal("99")],
            "close": [Decimal("100.5")],
            "volume": [Decimal("2")],
            "quote_volume": [Decimal("201")],
            "trade_count": [10],
            "taker_buy_base_volume": [Decimal("1")],
            "taker_buy_quote_volume": [Decimal("100")],
            "is_closed": [True],
        }
    )
    target = tmp_path / "btc.parquet"
    pyarrow.parquet.write_table(table, target)

    dataset = load_candle_dataset(target)
    candles = dataset.to_candles(instrument=_instrument(), timeframe=Timeframe("1h"))

    assert len(candles) == 1
    assert candles[0].open == Decimal("100")
    assert candles[0].close == Decimal("100.5")
    assert candles[0].source == str(target)
