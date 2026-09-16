from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from trading_system.features.models import FeatureSnapshot
from trading_system.strategies import (
    PortfolioContext,
    SignalDirection,
    StrategyContext,
    StrategySignal,
    evaluate_strategy,
)


TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)


def context(*, portfolio: PortfolioContext | None = None) -> StrategyContext:
    return StrategyContext(
        decision_time=TIME,
        symbol="BTCUSDT",
        features=FeatureSnapshot(TIME, Decimal("0"), Decimal("1"), Decimal("0.5"), Decimal("0.1"), Decimal("0"), 2),
        portfolio=portfolio,
    )


def test_long_signal_is_bounded_to_fully_funded_spot_exposure() -> None:
    signal = StrategySignal(
        decision_time=TIME,
        symbol="BTCUSDT",
        direction=SignalDirection.LONG,
        target_weight=Decimal("0.25"),
        confidence=Decimal("0.8"),
        score=Decimal("1.2"),
        reason="causal research condition",
        metadata=(("lookback", "20"),),
    )
    assert signal.target_weight == Decimal("0.25")


def test_no_trade_is_explicit_and_cannot_smuggle_an_allocation() -> None:
    signal = StrategySignal(TIME, "BTCUSDT", SignalDirection.NO_TRADE, "insufficient history")
    assert signal.target_weight is None
    with pytest.raises(ValueError, match="NO_TRADE"):
        StrategySignal(TIME, "BTCUSDT", SignalDirection.NO_TRADE, "invalid", target_weight=Decimal("0.1"))


@pytest.mark.parametrize("weight", [Decimal("0"), Decimal("-0.1"), Decimal("1.01")])
def test_long_signal_cannot_request_short_or_leveraged_exposure(weight: Decimal) -> None:
    with pytest.raises(ValueError, match="target_weight"):
        StrategySignal(TIME, "BTCUSDT", SignalDirection.LONG, "invalid", target_weight=weight)


def test_context_requires_point_in_time_inputs_and_nonfuture_portfolio() -> None:
    with pytest.raises(ValueError, match="features"):
        StrategyContext(
            decision_time=TIME,
            symbol="BTCUSDT",
            features=FeatureSnapshot(TIME + timedelta(hours=1), Decimal("0"), Decimal("1"), Decimal("0.5"), Decimal("0.1"), Decimal("0"), 2),
        )
    future_portfolio = PortfolioContext(TIME + timedelta(microseconds=1), Decimal("100"), Decimal("0"))
    with pytest.raises(ValueError, match="future"):
        context(portfolio=future_portfolio)


def test_strategy_protocol_result_must_match_input_identity() -> None:
    class Valid:
        name = "valid"

        def generate_signal(self, received: StrategyContext) -> StrategySignal:
            return StrategySignal(received.decision_time, received.symbol, SignalDirection.NO_TRADE, "no setup")

    class WrongSymbol:
        name = "wrong"

        def generate_signal(self, received: StrategyContext) -> StrategySignal:
            return StrategySignal(received.decision_time, "ETHUSDT", SignalDirection.NO_TRADE, "bad identity")

    assert evaluate_strategy(Valid(), context()).direction is SignalDirection.NO_TRADE
    with pytest.raises(ValueError, match="symbol"):
        evaluate_strategy(WrongSymbol(), context())


def test_metadata_is_immutable_and_auditable() -> None:
    with pytest.raises(TypeError, match="immutable"):
        StrategySignal(TIME, "BTCUSDT", SignalDirection.NO_TRADE, "bad metadata", metadata=[("source", "x")])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unique"):
        StrategySignal(
            TIME,
            "BTCUSDT",
            SignalDirection.NO_TRADE,
            "duplicate metadata",
            metadata=(("rule", "a"), ("rule", "b")),
        )
