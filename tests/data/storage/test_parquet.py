from datetime import UTC, datetime, timedelta
from decimal import Decimal

from trading_system.data.models import Candle, Instrument, MarketType, Timeframe
from trading_system.data.storage.parquet import read_candles, write_candles


def make_candle(index: int = 0) -> Candle:
    start = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(hours=index)
    return Candle(
        instrument=Instrument(symbol="BTCUSDT", exchange="BINANCE", base_asset="BTC", quote_asset="USDT", market_type=MarketType.SPOT),
        timeframe=Timeframe("1h"), open_time=start, close_time=start + timedelta(hours=1),
        open=Decimal("60000.12345678"), high=Decimal("60100.12345678"), low=Decimal("59900.12345678"), close=Decimal("60050.12345678"),
        volume=Decimal("12.34567890"), quote_volume=Decimal("740000.12345678"), trade_count=1234,
        taker_buy_base_volume=Decimal("6.12345678"), taker_buy_quote_volume=Decimal("367000.12345678"),
        source="binance", is_closed=True,
    )


def test_parquet_round_trip_preserves_financial_values(tmp_path):
    path = tmp_path / "btc.parquet"
    write_candles(path, [make_candle(), make_candle(1)])
    rows = read_candles(path)
    assert len(rows) == 2
    assert rows[0]["open"] == "60000.12345678"
    assert rows[0]["volume"] == "12.34567890"
    assert rows[0]["trade_count"] == 1234
    assert rows[0]["is_closed"] is True


def test_parquet_round_trip_preserves_utc_timestamps(tmp_path):
    path = tmp_path / "btc.parquet"
    candle = make_candle()
    write_candles(path, [candle])
    row = read_candles(path)[0]
    assert row["open_time"].tzinfo is not None
    assert row["open_time"].utcoffset().total_seconds() == 0


def test_write_replaces_destination_atomically(tmp_path):
    path = tmp_path / "btc.parquet"
    write_candles(path, [make_candle()])
    write_candles(path, [make_candle(1), make_candle(2)])
    assert len(read_candles(path)) == 2
    assert not path.with_name(path.name + ".tmp").exists()
