"""Run deterministic robustness experiments across walk-forward OOS windows."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal

from .evaluation import OOSWindowResult, summarize_oos
from .parameter_sensitivity import MomentumParameterCase
from .results import BacktestResult
from .robustness import SensitivityCase


@dataclass(frozen=True)
class OOSExperimentResult:
    case_name: str
    windows: tuple[OOSWindowResult, ...]
    compounded_return: Decimal
    worst_drawdown: Decimal


def run_oos_experiments(
    cases: Sequence[SensitivityCase | MomentumParameterCase],
    window_runner: Callable[[object, int], BacktestResult],
    window_count: int,
) -> tuple[OOSExperimentResult, ...]:
    """Execute every case over every OOS window and retain window-level evidence."""
    if not cases:
        raise ValueError("cases must not be empty")
    if window_count <= 0:
        raise ValueError("window_count must be positive")
    results: list[OOSExperimentResult] = []
    for case in cases:
        windows = tuple(
            OOSWindowResult(index, run_result.total_return, run_result.max_drawdown)
            for index in range(window_count)
            for run_result in (window_runner(case.config, index),)
        )
        summary = summarize_oos(windows)
        results.append(OOSExperimentResult(case.name, windows, summary.compounded_return, summary.worst_drawdown))
    return tuple(results)
