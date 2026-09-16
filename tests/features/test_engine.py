from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from trading_system.data.models import Candle, Instrument, Timeframe
from trading_system.features import FeatureEngine, FeatureEngineConfig


def _series(symbol: str, closes: list[Decimal], *, offset: int = 0) -> list[Candle]:
    instrument = Instrument(
        symbol=symbol,
        base_asset=symbol.removesuffix("USDT"),
        quote_asset="USDT",
        exchange="BINANCE",
    )
    start = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(hours=offset)
    return [
        Candle(
            instrument=instrument,
            timeframe=Timeframe.H1,
            open_time=start + timedelta(hours=i),
            close_time=start + timedelta(hours=i + 1),
            open=price,
            high=price,
            low=price,
            close=price,
            volume=Decimal("1"),
            quote_volume=price,
            trade_count=1,
            taker_buy_base_volume=Decimal("1"),
            taker_buy_quote_volume=price,
            source="test",
            is_closed=True,
        )
        for i, price in enumerate(closes)
    ]


def _prices(start: Decimal, step: Decimal, count: int = 21) -> list[Decimal]:
    return [start + step * i for i in range(count)]


def test_compute_returns_all_five_market_features() -> None:
    engine = FeatureEngine(FeatureEngineConfig(trend_lookback=20, volatility_lookback=20, correlation_lookback=20))
    candles = {
        "BTCUSDT": _series("BTCUSDT", _prices(Decimal("100"), Decimal("1"))),
        "ETHUSDT": _series("ETHUSDT", _prices(Decimal("200"), Decimal("2"))),
        "SOLUSDT": _series("SOLUSDT", _prices(Decimal("50"), Decimal("0.5"))),
    }
    snapshot = engine.compute(candles)
    assert snapshot.asset_count == 3
    assert snapshot.trend_score is not None and snapshot.trend_score > 0
    assert snapshot.realized_volatility is not None and snapshot.realized_volatility >= 0
    assert snapshot.breadth == Decimal("1")
    assert snapshot.cross_sectional_dispersion is not None and snapshot.cross_sectional_dispersion >= 0
    assert snapshot.average_pairwise_correlation is not None


def test_insufficient_assets_returns_unavailable_features() -> None:
    engine = FeatureEngine(FeatureEngineConfig(min_assets=3))
    candles = {
        "BTCUSDT": _series("BTCUSDT", _prices(Decimal("100"), Decimal("1"))),
        "ETHUSDT": _series("ETHUSDT", _prices(Decimal("200"), Decimal("1"))),
    }
    snapshot = engine.compute(candles)
    assert snapshot.asset_count == 2
    assert snapshot.trend_score is None
    assert snapshot.realized_volatility is None


def test_short_asset_history_is_not_silently_dropped() -> None:
    engine = FeatureEngine()
    candles = {
        "BTCUSDT": _series("BTCUSDT", _prices(Decimal("100"), Decimal("1"))),
        "ETHUSDT": _series("ETHUSDT", _prices(Decimal("200"), Decimal("1"), count=10)),
        "SOLUSDT": _series("SOLUSDT", _prices(Decimal("50"), Decimal("0.5"))),
    }
    snapshot = engine.compute(candles)
    assert snapshot.asset_count == 3
    assert snapshot.trend_score is None
    assert snapshot.breadth is None


def test_misaligned_history_is_rejected() -> None:
    engine = FeatureEngine()
    candles = {
        "BTCUSDT": _series("BTCUSDT", _prices(Decimal("100"), Decimal("1"))),
        "ETHUSDT": _series("ETHUSDT", _prices(Decimal("200"), Decimal("1")), offset=1),
        "SOLUSDT": _series("SOLUSDT", _prices(Decimal("50"), Decimal("1"))),
    }
    with pytest.raises(ValueError, match="same candle"):
        engine.compute(candles)


def test_unfinalized_input_is_rejected() -> None:
    engine = FeatureEngine()
    values = _series("BTCUSDT", _prices(Decimal("100"), Decimal("1")))
    values[-1] = values[-1].model_copy(update={"is_closed": False})
    with pytest.raises(ValueError, match="finalized"):
        engine.compute({"BTCUSDT": values})


def test_configuration_rejects_too_short_lookbacks() -> None:
    with pytest.raises(ValueError):
        FeatureEngineConfig(trend_lookback=1)


def test_zero_variance_pair_makes_correlation_unavailable() -> None:
    engine = FeatureEngine()
    candles = {
        "BTCUSDT": _series("BTCUSDT", _prices(Decimal("100"), Decimal("1"))),
        "ETHUSDT": _series("ETHUSDT", [Decimal("200")] * 21),
        "SOLUSDT": _series("SOLUSDT", _prices(Decimal("50"), Decimal("0.5"))),
    }
    snapshot = engine.compute(candles)
    assert snapshot.average_pairwise_correlation is None
