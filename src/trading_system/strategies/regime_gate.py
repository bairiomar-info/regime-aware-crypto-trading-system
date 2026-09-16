"""Explicit regime gating for research strategies."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from trading_system.regime.models import MarketState, TrendState
from .interface import ResearchStrategy
from .models import SignalDirection, StrategyContext, StrategySignal


@dataclass(frozen=True)
class RegimeGateConfig:
    allowed_trends: frozenset[TrendState]
    target_weight_multiplier: Decimal = Decimal("1")

    def __post_init__(self) -> None:
        if not self.allowed_trends:
            raise ValueError("allowed_trends must not be empty")
        if not self.target_weight_multiplier.is_finite() or not Decimal("0") < self.target_weight_multiplier <= Decimal("1"):
            raise ValueError("target_weight_multiplier must be within (0, 1]")


class RegimeGatedStrategy(ResearchStrategy):
    """Wrap a research strategy and suppress LONG signals in disallowed regimes."""

    def __init__(self, strategy: ResearchStrategy, config: RegimeGateConfig) -> None:
        self.strategy = strategy
        self.config = config
        self.name = f"regime_gate:{strategy.name}"

    def generate_signal(self, context: StrategyContext) -> StrategySignal:
        signal = self.strategy.generate_signal(context)
        if signal.direction is not SignalDirection.LONG:
            return signal
        regime: MarketState | None = context.regime
        if regime is None:
            return StrategySignal(signal.decision_time, signal.symbol, SignalDirection.NO_TRADE, "missing_regime")
        if regime.trend not in self.config.allowed_trends:
            return StrategySignal(signal.decision_time, signal.symbol, SignalDirection.NO_TRADE, "regime_gate_blocked", score=signal.score)
        weight = signal.target_weight * self.config.target_weight_multiplier
        return StrategySignal(signal.decision_time, signal.symbol, SignalDirection.LONG, signal.reason, signal.score, signal.confidence, weight, signal.metadata)
