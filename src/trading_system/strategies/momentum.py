"""Causal time-series momentum research strategy."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .interface import ResearchStrategy
from .models import SignalDirection, StrategyContext, StrategySignal


@dataclass(frozen=True)
class TimeSeriesMomentumConfig:
    """Configuration for a simple close-to-close momentum signal."""

    lookback: int
    target_weight: Decimal
    min_return: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        if self.lookback <= 0:
            raise ValueError("lookback must be positive")
        if not self.target_weight.is_finite() or not Decimal("0") < self.target_weight <= Decimal("1"):
            raise ValueError("target_weight must be within (0, 1]")
        if not self.min_return.is_finite():
            raise ValueError("min_return must be finite")


class TimeSeriesMomentum(ResearchStrategy):
    """Go long when the trailing return exceeds the configured threshold.

    The strategy consumes only prices at or before ``decision_time`` supplied
    by its immutable context. It produces a research signal and never orders.
    """

    name = "time_series_momentum"

    def __init__(self, config: TimeSeriesMomentumConfig) -> None:
        self.config = config

    def generate_signal(self, context: StrategyContext) -> StrategySignal:
        history = context.price_history
        required = self.config.lookback + 1
        if len(history) < required:
            return StrategySignal(
                context.decision_time,
                context.symbol,
                SignalDirection.NO_TRADE,
                "insufficient_price_history",
            )

        window = history[-required:]
        if window[-1][0] != context.decision_time:
            raise ValueError("latest price observation must match decision_time")
        previous_time = None
        for timestamp, close in window:
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                raise ValueError("price history timestamps must be timezone-aware")
            if previous_time is not None and timestamp <= previous_time:
                raise ValueError("price history must be strictly chronological")
            if not close.is_finite() or close <= 0:
                raise ValueError("price history closes must be positive and finite")
            previous_time = timestamp

        start = window[0][1]
        end = window[-1][1]
        trailing_return = (end / start) - Decimal("1")
        if trailing_return > self.config.min_return:
            return StrategySignal(
                context.decision_time,
                context.symbol,
                SignalDirection.LONG,
                "positive_trailing_return",
                score=trailing_return,
                target_weight=self.config.target_weight,
            )
        return StrategySignal(
            context.decision_time,
            context.symbol,
            SignalDirection.NO_TRADE,
            "momentum_threshold_not_met",
            score=trailing_return,
        )
