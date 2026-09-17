"""Bind chronological MarketBar data to the existing OOS experiment API."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Callable

from .engine import BacktestConfig, MarketBar
from .oos_experiments import Case, OOSExperimentResult, run_oos_experiments
from .oos_runner import run_oos_backtests
from .walk_forward import WalkForwardWindow


def run_market_bar_oos_experiments(
    bars: Sequence[MarketBar],
    windows: Sequence[WalkForwardWindow],
    cases: Sequence[Case],
    signal_factory_for_case: Callable,
    config: BacktestConfig,
) -> tuple[OOSExperimentResult, ...]:
    """Execute every case on every supplied OOS window using real MarketBars."""
    if not bars:
        raise ValueError("bars must not be empty")
    if not windows:
        raise ValueError("windows must not be empty")

    def window_runner(case: Case, index: int):
        if index >= len(windows):
            raise IndexError("OOS window index out of range")
        factory = signal_factory_for_case(case)
        return run_oos_backtests((windows[index],), factory, config)[0]

    return run_oos_experiments(cases, window_runner, len(windows))
