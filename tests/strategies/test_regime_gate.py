from datetime import datetime, timezone
from decimal import Decimal

from trading_system.features.models import FeatureSnapshot
from trading_system.regime.models import LevelState, MarketState, Transition, TrendState
from trading_system.strategies.models import SignalDirection, StrategyContext, StrategySignal
from trading_system.strategies.regime_gate import RegimeGateConfig, RegimeGatedStrategy


class StubStrategy:
    name = "stub"

    def generate_signal(self, context: StrategyContext) -> StrategySignal:
        return StrategySignal(context.decision_time, context.symbol, SignalDirection.LONG, "stub", target_weight=Decimal("1"))


def features(time: datetime) -> FeatureSnapshot:
    return FeatureSnapshot(
        decision_time=time,
        trend_score=None,
        realized_volatility=None,
        breadth=None,
        cross_sectional_dispersion=None,
        average_pairwise_correlation=None,
        asset_count=1,
    )


def regime(time: datetime, trend: TrendState) -> MarketState:
    return MarketState(
        decision_time=time,
        trend=trend,
        volatility=LevelState.NORMAL,
        breadth=LevelState.NORMAL,
        dispersion=LevelState.NORMAL,
        correlation=LevelState.NORMAL,
        transition=Transition.PERSISTING_NEUTRAL,
        state_age=1,
        confidence=Decimal("1"),
    )


def test_gate_blocks_disallowed_trend_without_changing_strategy_signal_contract() -> None:
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    context = StrategyContext(t, "BTCUSDT", features=features(t), regime=regime(t, TrendState.DOWN))
    result = RegimeGatedStrategy(StubStrategy(), RegimeGateConfig(frozenset({TrendState.UP}))).generate_signal(context)
    assert result.direction is SignalDirection.NO_TRADE
    assert result.reason == "regime_gate_blocked"


def test_gate_scales_allowed_target_weight() -> None:
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    context = StrategyContext(t, "BTCUSDT", features=features(t), regime=regime(t, TrendState.UP))
    result = RegimeGatedStrategy(StubStrategy(), RegimeGateConfig(frozenset({TrendState.UP}), Decimal("0.5"))).generate_signal(context)
    assert result.direction is SignalDirection.LONG
    assert result.target_weight == Decimal("0.5")
