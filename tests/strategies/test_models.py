from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_system.features.models import FeatureSnapshot
from trading_system.regime.models import MarketState
from trading_system.strategies.models import PortfolioContext, SignalDirection, StrategyContext, StrategySignal


def test_long_signal_requires_bounded_target_weight() -> None:
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for weight in (Decimal("0"), Decimal("1.01"), Decimal("NaN")):
        with pytest.raises((ValueError, TypeError)):
            StrategySignal(t, "BTCUSDT", SignalDirection.LONG, "test", target_weight=weight)


def test_no_trade_cannot_carry_target_weight() -> None:
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(ValueError):
        StrategySignal(t, "BTCUSDT", SignalDirection.NO_TRADE, "test", target_weight=Decimal("0.2"))


def test_confidence_is_bounded() -> None:
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for confidence in (Decimal("-0.1"), Decimal("1.1")):
        with pytest.raises(ValueError):
            StrategySignal(t, "BTCUSDT", SignalDirection.NO_TRADE, "test", confidence=confidence)


def test_strategy_context_rejects_future_price_history() -> None:
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    # FeatureSnapshot construction is intentionally delegated to the existing model contract.
    feature = FeatureSnapshot(decision_time=t, values=())
    with pytest.raises(ValueError, match="future"):
        StrategyContext(t, "BTCUSDT", feature, price_history=((t, Decimal("100")), (t.replace(hour=1), Decimal("101"))))


def test_strategy_context_rejects_non_chronological_history() -> None:
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    feature = FeatureSnapshot(decision_time=t, values=())
    with pytest.raises(ValueError, match="chronological"):
        StrategyContext(t, "BTCUSDT", feature, price_history=((t, Decimal("100")), (t, Decimal("101"))))


def test_portfolio_context_rejects_future_state() -> None:
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    feature = FeatureSnapshot(decision_time=t, values=())
    portfolio = PortfolioContext(t.replace(hour=1), Decimal("100"), Decimal("0"))
    with pytest.raises(ValueError, match="future"):
        StrategyContext(t, "BTCUSDT", feature, portfolio=portfolio)
