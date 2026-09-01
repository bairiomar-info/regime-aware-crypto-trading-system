from decimal import Decimal

import pytest

from trading_system.data.models import Instrument, Timeframe
from trading_system.data.normalization import BinanceKlineNormalizer, BinanceRawKline


@pytest.fixture
def instrument() -> Instrument:
    return Instrument(
        symbol="BTCUSDT",
        base_asset="BTC",
        quote_asset="USDT",
        exchange="BINANCE",
    )


def raw_kline() -> BinanceRawKline:
    return BinanceRawKline(
        open_time_ms=1_756_722_000_000,
        open="100.10",
        high="110.20",
        low="99.90",
        close="105.50",
        volume="12.34560000",
        close_time_ms=1_756_722_059_999,
        quote_volume="1299.99900000",
        trade_count=42,
        taker_buy_base_volume="6.12340000",
        taker_buy_quote_volume="645.50000000",
    )


def test_binance_kline_is_normalized_without_float_prices(instrument):
    candle = BinanceKlineNormalizer().normalize(
        raw_kline(), instrument=instrument, timeframe=Timeframe.M1
    )

    assert candle.open == Decimal("100.10")
    assert candle.volume == Decimal("12.34560000")
    assert candle.source == "binance"
    assert candle.is_closed is True
    assert candle.open_time.tzinfo is not None


def test_binance_kline_timestamps_are_utc(instrument):
    candle = BinanceKlineNormalizer().normalize(
        raw_kline(), instrument=instrument, timeframe=Timeframe.M1
    )

    assert candle.open_time.utcoffset().total_seconds() == 0
    assert candle.close_time.utcoffset().total_seconds() == 0


def test_forming_candle_can_be_normalized_but_is_not_marked_closed(instrument):
    candle = BinanceKlineNormalizer().normalize(
        raw_kline(), instrument=instrument, timeframe=Timeframe.M1, is_closed=False
    )

    assert candle.is_closed is False


def test_negative_timestamp_is_rejected(instrument):
    raw = raw_kline()
    invalid = BinanceRawKline(
        open_time_ms=-1,
        open=raw.open,
        high=raw.high,
        low=raw.low,
        close=raw.close,
        volume=raw.volume,
        close_time_ms=raw.close_time_ms,
        quote_volume=raw.quote_volume,
        trade_count=raw.trade_count,
        taker_buy_base_volume=raw.taker_buy_base_volume,
        taker_buy_quote_volume=raw.taker_buy_quote_volume,
    )

    with pytest.raises(ValueError):
        BinanceKlineNormalizer().normalize(
            invalid, instrument=instrument, timeframe=Timeframe.M1
        )
