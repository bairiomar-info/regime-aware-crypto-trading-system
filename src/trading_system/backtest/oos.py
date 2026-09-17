"""Out-of-sample execution across precomputed walk-forward windows."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from .engine import BacktestConfig, MarketBar
from .results import BacktestResult
from .runner import SignalFactory, run_backtest
from .walk_forward import WalkForwardWindow


@dataclass(frozen=True)
class OOSWindowResult:
    window: WalkForwardWindow
    result: BacktestResult


@dataclass(frozen=True)
class OOSAggregate:
    windows: tuple[OOSWindowResult, ...]
    total_return: Decimal
    worst_drawdown: Decimal


def run_oos_windows(
    windows: Sequence[WalkForwardWindow],
    bars: Sequence[MarketBar],
    signal_factory: SignalFactory,
    config: BacktestConfig,
) -> OOSAggregate:
    """Execute only the test portions of supplied walk-forward windows.

    OOS test windows must form one chronological, non-overlapping evaluation
    stream. Training histories may overlap, but an observation cannot be
    counted twice in the aggregate performance result.
    """
    if not windows:
        raise ValueError("windows must not be empty")
    if not bars:
        raise ValueError("bars must not be empty")

    supplied = {bar.timestamp: bar for bar in bars}
    if len(supplied) != len(bars):
        raise ValueError("supplied bars must have unique timestamps")

    results: list[OOSWindowResult] = []
    previous_test_end = None
    for window in windows:
        test_bars = window.test
        if any(supplied.get(bar.timestamp) != bar for bar in test_bars):
            raise ValueError("window test bars must exactly match the supplied bar sequence")
        if len(test_bars) < 2:
            raise ValueError(f"window {test_bars[0].timestamp.isoformat()} has fewer than two test bars")
        if previous_test_end is not None and test_bars[0].timestamp <= previous_test_end:
            raise ValueError("OOS test windows must be strictly chronological and non-overlapping")
        result = run_backtest(test_bars, signal_factory, config)
        results.append(OOSWindowResult(window, result))
        previous_test_end = test_bars[-1].timestamp

    compounded = Decimal("1")
    for item in results:
        compounded *= Decimal("1") + item.result.total_return
    return OOSAggregate(
        windows=tuple(results),
        total_return=compounded - Decimal("1"),
        worst_drawdown=max(item.result.max_drawdown for item in results),
    )
