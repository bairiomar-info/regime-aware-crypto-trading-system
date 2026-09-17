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
    """Execute only the test portions of supplied walk-forward windows."""
    if not windows:
        raise ValueError("windows must not be empty")
    if not bars:
        raise ValueError("bars must not be empty")

    available = {bar.timestamp for bar in bars}
    results: list[OOSWindowResult] = []
    for window in windows:
        test_bars = window.test
        if any(bar.timestamp not in available for bar in test_bars):
            raise ValueError("window test bars must come from the supplied bar sequence")
        if len(test_bars) < 2:
            raise ValueError(f"window {test_bars[0].timestamp.isoformat()} has fewer than two test bars")
        result = run_backtest(test_bars, signal_factory, config)
        results.append(OOSWindowResult(window, result))

    compounded = Decimal("1")
    for item in results:
        compounded *= Decimal("1") + item.result.total_return
    return OOSAggregate(
        windows=tuple(results),
        total_return=compounded - Decimal("1"),
        worst_drawdown=max(item.result.max_drawdown for item in results),
    )
