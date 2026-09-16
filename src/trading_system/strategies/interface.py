"""Research strategy protocol isolated from portfolio, risk, and execution."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import StrategyContext, StrategySignal


@runtime_checkable
class ResearchStrategy(Protocol):
    """A deterministic function from point-in-time context to a research signal."""

    name: str

    def generate_signal(self, context: StrategyContext) -> StrategySignal:
        """Return a signal; implementations must not place or plan orders."""


def evaluate_strategy(strategy: ResearchStrategy, context: StrategyContext) -> StrategySignal:
    """Evaluate one strategy and enforce identity with its input context."""
    signal = strategy.generate_signal(context)
    if not isinstance(signal, StrategySignal):
        raise TypeError("strategy must return a StrategySignal")
    if signal.decision_time != context.decision_time:
        raise ValueError("strategy signal must match context decision_time")
    if signal.symbol != context.symbol:
        raise ValueError("strategy signal must match context symbol")
    return signal
