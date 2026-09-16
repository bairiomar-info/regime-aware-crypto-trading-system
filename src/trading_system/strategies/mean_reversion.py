"""Point-in-time long-only mean-reversion research strategy."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .interface import ResearchStrategy
from .models import SignalDirection, StrategyContext, StrategySignal


@dataclass(frozen=True)
class MeanReversionConfig:
    """Configuration for a close-vs-reference mean-reversion signal."""

    lookback: int
    entry_threshold: Decimal
    target_weight: Decimal

    def __post_init__(self) -> None:
        if self.lookback <= 0:
            raise ValueError("lookback must be positive")
        if not self.entry_threshold.is_finite() or not Decimal("0") < self.entry_threshold < Decimal("1"):
            raise ValueError("entry_threshold must be within (0, 1)")
        if not self.target_weight.is_finite() or not Decimal("0") < self.target_weight <= Decimal("1"):
            raise ValueError("target_weight must be within (0, 1]")


class MeanReversion(ResearchStrategy):
    """Go long when price is sufficiently below its trailing mean.

    The mean uses only observations at or before the decision time. This is a
    research signal only; portfolio, risk, compliance, and execution remain
    separate layers.
    """

    name = "mean_reversion"

    def __init__(self, config: MeanReversionConfig) -> None:
        self.config = config

    def generate_signal(self, context: StrategyContext) -> StrategySignal:
        history = context.price_history
        if len(history) < self.config.lookback:
            return StrategySignal(
                context.decision_time,
                context.symbol,
                SignalDirection.NO_TRADE,
                "insufficient_price_history",
            )

        window = history[-self.config.lookback :]
        if window[-1][0] != context.decision_time:
            raise ValueError("latest price observation must match decision_time")

        total = Decimal("0")
        previous_time = None
        for timestamp, close in window:
            if previous_time is not None and timestamp <= previous_time:
                raise ValueError("price history must be strictly chronological")
            if not close.is_finite() or close <= 0:
                raise ValueError("price history closes must be positive and finite")
            if timestamp > context.decision_time:
                raise ValueError("price history cannot contain future observations")
            total += close
            previous_time = timestamp

        mean = total / Decimal(self.config.lookback)
        deviation = (window[-1][1] / mean) - Decimal("1")
        if deviation <= -self.config.entry_threshold:
            return StrategySignal(
                context.decision_time,
                context.symbol,
                SignalDirection.LONG,
                "price_below_trailing_mean",
                score=-deviation,
                target_weight=self.config.target_weight,
            )

        return StrategySignal(
            context.decision_time,
            context.symbol,
            SignalDirection.NO_TRADE,
            "mean_reversion_threshold_not_met",
            score=-deviation,
        )
