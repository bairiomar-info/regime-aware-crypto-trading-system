"""Run the existing causal backtest independently on each OOS window."""

from __future__ import annotations

from collections.abc import Sequence

from .engine import BacktestConfig
from .results import BacktestResult
from .runner import SignalFactory, run_backtest
from .walk_forward import WalkForwardWindow


def run_oos_backtests(
    windows: Sequence[WalkForwardWindow],
    signal_factory: SignalFactory,
    config: BacktestConfig,
) -> tuple[BacktestResult, ...]:
    """Execute every OOS test segment with no training/test concatenation."""
    if not windows:
        raise ValueError("at least one OOS window is required")
    return tuple(run_backtest(window.test, signal_factory, config) for window in windows)
