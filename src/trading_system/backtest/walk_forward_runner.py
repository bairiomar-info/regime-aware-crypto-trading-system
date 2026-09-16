"""Walk-forward out-of-sample execution with training history retained only as context."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from decimal import Decimal

from trading_system.strategies.models import StrategySignal

from .engine import BacktestConfig, MarketBar
from .evaluation import OOSSummary, OOSWindowResult, summarize_oos
from .runner import SignalFactory, run_backtest
from .walk_forward import WalkForwardWindow, make_walk_forward_windows


def run_walk_forward_oos(
    bars: Sequence[MarketBar],
    signal_factory: SignalFactory,
    config: BacktestConfig,
    *,
    train_size: int,
    test_size: int,
    step: int | None = None,
) -> OOSSummary:
    """Execute each test window OOS while exposing prior training bars as strategy history."""
    windows = make_walk_forward_windows(tuple(bars), train_size=train_size, test_size=test_size, step=step)
    if not windows:
        raise ValueError("dataset does not contain a complete train/test window")

    results: list[OOSWindowResult] = []
    for index, window in enumerate(windows):
        combined = window.train + window.test
        # Run on train+test so the signal factory receives warm-up history, then
        # measure only the test segment by executing from the test boundary.
        # A dedicated test runner keeps the train segment from affecting OOS cash.
        state_bars = combined
        start = len(window.train)
        result = _run_test_segment(state_bars, start, signal_factory, config)
        results.append(OOSWindowResult(index, result.total_return, result.max_drawdown))
    return summarize_oos(tuple(results))


def _run_test_segment(
    bars: Sequence[MarketBar],
    test_start: int,
    signal_factory: SignalFactory,
    config: BacktestConfig,
):
    if test_start >= len(bars) - 1:
        raise ValueError("test window must contain at least two bars")
    # Warm-up calls are deliberately read-only: they create no orders and do not
    # mutate backtest state. The first test decision is executed on the next bar.
    for index in range(test_start):
        signal_factory(bars[index], bars[: index + 1])
    return run_backtest(bars[test_start - 1 :], signal_factory, config)
