from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from trading_system.features.models import FeatureSnapshot
from trading_system.strategies.models import PortfolioContext, SignalDirection, StrategyContext, StrategySignal

T = datetime(2026, 1, 1, tzinfo=timezone.utc)


def features(time: datetime = T) -> FeatureSnapshot:
    return FeatureSnapshot(time, None, None, None, None, None, 1)


def valid_regime(time: datetime) -> object:
    from trading_system.regime.models import LevelState, MarketState, Transition, TrendState

    return MarketState(
        decision_time=time,
        trend=TrendState.UP,
        volatility=LevelState.NORMAL,
        breadth=LevelState.NORMAL,
        dispersion=LevelState.NORMAL,
        correlation=LevelState.NORMAL,
        transition=Transition.PERSISTING_UP,
        state_age=1,
        confidence=Decimal("0.8"),
    )


@pytest.mark.parametrize("symbol", ["", "btcusdt", "BTCUSDT "])
def test_strategy_signal_requires_uppercase_non_empty_symbol(symbol: str) -> None:
    with pytest.raises(ValueError, match="symbol"):
        StrategySignal(T, symbol, SignalDirection.NO_TRADE, "test")


def test_no_trade_cannot_have_target_weight() -> None:
    with pytest.raises(ValueError, match="NO_TRADE"):
        StrategySignal(T, "BTCUSDT", SignalDirection.NO_TRADE, "test", target_weight=Decimal("0.5"))


def test_long_requires_positive_target_weight() -> None:
    for weight in [Decimal("0"), Decimal("-0.1")]:
        with pytest.raises(ValueError, match="target_weight"):
            StrategySignal(T, "BTCUSDT", SignalDirection.LONG, "test", target_weight=weight)


def test_long_rejects_target_weight_above_one() -> None:
    with pytest.raises(ValueError, match="target_weight"):
        StrategySignal(T, "BTCUSDT", SignalDirection.LONG, "test", target_weight=Decimal("1.01"))


@pytest.mark.parametrize("confidence", [Decimal("-0.01"), Decimal("1.01")])
def test_signal_confidence_must_be_unit_interval(confidence: Decimal) -> None:
    with pytest.raises(ValueError, match="confidence"):
        StrategySignal(T, "BTCUSDT", SignalDirection.NO_TRADE, "test", confidence=confidence)


def test_signal_requires_reason() -> None:
    with pytest.raises(ValueError, match="reason"):
        StrategySignal(T, "BTCUSDT", SignalDirection.NO_TRADE, "")


def test_signal_metadata_keys_must_be_unique() -> None:
    with pytest.raises(ValueError, match="unique"):
        StrategySignal(T, "BTCUSDT", SignalDirection.NO_TRADE, "test", metadata=(("source", "a"), ("source", "b")))


def test_signal_metadata_must_be_tuple() -> None:
    with pytest.raises(TypeError, match="immutable tuple"):
        StrategySignal(T, "BTCUSDT", SignalDirection.NO_TRADE, "test", metadata=[])


def test_strategy_context_rejects_future_features() -> None:
    with pytest.raises(ValueError, match="features"):
        StrategyContext(T, "BTCUSDT", features(T + timedelta(hours=1)))


def test_strategy_context_rejects_future_regime() -> None:
    future = T + timedelta(hours=1)
    with pytest.raises(ValueError, match="regime"):
        StrategyContext(T, "BTCUSDT", features(T), regime=valid_regime(future))


def test_strategy_context_rejects_future_portfolio_snapshot() -> None:
    portfolio = PortfolioContext(T + timedelta(minutes=1), Decimal("1000"), Decimal("0"))
    with pytest.raises(ValueError, match="future"):
        StrategyContext(T, "BTCUSDT", features(T), portfolio=portfolio)


def test_strategy_context_requires_tuple_price_history() -> None:
    with pytest.raises(TypeError, match="immutable tuple"):
        StrategyContext(T, "BTCUSDT", features(T), price_history=[(T, Decimal("100"))])  # type: ignore[arg-type]


def test_strategy_context_rejects_duplicate_price_history_timestamps() -> None:
    with pytest.raises(ValueError, match="strictly chronological"):
        StrategyContext(T, "BTCUSDT", features(T), price_history=((T, Decimal("100")), (T, Decimal("101"))))


def test_strategy_context_rejects_future_price_history() -> None:
    with pytest.raises(ValueError, match="future"):
        StrategyContext(T, "BTCUSDT", features(T), price_history=((T + timedelta(minutes=1), Decimal("100")),))


@pytest.mark.parametrize("close", [Decimal("0"), Decimal("-1"), Decimal("NaN"), Decimal("Infinity")])
def test_strategy_context_rejects_invalid_price_history_close(close: Decimal) -> None:
    with pytest.raises((TypeError, ValueError)):
        StrategyContext(T, "BTCUSDT", features(T), price_history=((T, close),))


@pytest.mark.parametrize("weight", [Decimal("-0.01"), Decimal("1.01")])
def test_portfolio_context_rejects_weight_outside_unit_interval(weight: Decimal) -> None:
    with pytest.raises(ValueError, match="current_weight"):
        PortfolioContext(T, Decimal("1000"), weight)


def test_portfolio_context_rejects_negative_cash() -> None:
    with pytest.raises(ValueError, match="cash"):
        PortfolioContext(T, Decimal("-1"), Decimal("0"))


def test_portfolio_context_accepts_boundary_weight_zero() -> None:
    PortfolioContext(T, Decimal("1000"), Decimal("0"))


def test_portfolio_context_accepts_boundary_weight_one() -> None:
    PortfolioContext(T, Decimal("1000"), Decimal("1"))
