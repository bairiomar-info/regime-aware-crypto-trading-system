from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from trading_system.data.models import Candle, Instrument, Timeframe

T = datetime(2026, 1, 1, tzinfo=timezone.utc)


def candle(**overrides: object) -> Candle:
    values: dict[str, object] = {
        "instrument": Instrument(symbol="BTCUSDT", base_asset="BTC", quote_asset="USDT", exchange="binance"),
        "timeframe": Timeframe.H1,
        "open_time": T,
        "close_time": T + timedelta(hours=1),
        "open": Decimal("100"),
        "high": Decimal("110"),
        "low": Decimal("90"),
        "close": Decimal("105"),
        "volume": Decimal("10"),
        "quote_volume": Decimal("1000"),
        "trade_count": 10,
        "taker_buy_base_volume": Decimal("5"),
        "taker_buy_quote_volume": Decimal("500"),
        "source": "test",
        "is_closed": True,
    }
    values.update(overrides)
    return Candle(**values)  # type: ignore[arg-type]


def test_candle_accepts_valid_ohlcv_structure() -> None:
    assert candle().close == Decimal("105")


def test_candle_rejects_close_time_not_after_open_time() -> None:
    with pytest.raises(ValueError, match="close_time"):
        candle(close_time=T)


def test_candle_rejects_naive_open_time() -> None:
    with pytest.raises(ValueError, match="open_time"):
        candle(open_time=datetime(2026, 1, 1))


def test_candle_rejects_naive_close_time() -> None:
    with pytest.raises(ValueError, match="close_time"):
        candle(close_time=datetime(2026, 1, 1, 1))


def test_candle_rejects_non_utc_open_time() -> None:
    with pytest.raises(ValueError, match="UTC"):
        candle(open_time=T.astimezone(timezone(timedelta(hours=1))))


def test_candle_rejects_high_below_close() -> None:
    with pytest.raises(ValueError, match="high"):
        candle(high=Decimal("104"))


def test_candle_rejects_high_below_open() -> None:
    with pytest.raises(ValueError, match="high"):
        candle(high=Decimal("99"))


def test_candle_rejects_low_above_close() -> None:
    with pytest.raises(ValueError, match="low"):
        candle(low=Decimal("106"))


def test_candle_rejects_low_above_open() -> None:
    with pytest.raises(ValueError, match="low"):
        candle(low=Decimal("101"))


def test_candle_accepts_zero_volume() -> None:
    result = candle(volume=Decimal("0"), quote_volume=Decimal("0"), trade_count=0, taker_buy_base_volume=Decimal("0"), taker_buy_quote_volume=Decimal("0"))
    assert result.volume == Decimal("0")


@pytest.mark.parametrize("field", ["volume", "quote_volume", "taker_buy_base_volume", "taker_buy_quote_volume"])
def test_candle_rejects_negative_volume(field: str) -> None:
    with pytest.raises(ValueError):
        candle(**{field: Decimal("-0.01")})


def test_candle_rejects_negative_trade_count() -> None:
    with pytest.raises(ValueError, match="trade_count"):
        candle(trade_count=-1)


def test_candle_rejects_empty_source() -> None:
    with pytest.raises(ValueError, match="source"):
        candle(source="")
