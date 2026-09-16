"""Deterministic parameter sensitivity helpers for research experiments."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Callable, Iterable

from .results import BacktestResult
from .robustness import SensitivityResult
from ..strategies.momentum import TimeSeriesMomentumConfig


@dataclass(frozen=True)
class MomentumParameterCase:
    name: str
    config: TimeSeriesMomentumConfig


def make_momentum_parameter_cases(
    *,
    lookbacks: Iterable[int],
    target_weights: Iterable[Decimal],
    min_returns: Iterable[Decimal],
) -> tuple[MomentumParameterCase, ...]:
    """Build a deterministic Cartesian grid of momentum configurations."""
    lbs, weights, thresholds = tuple(lookbacks), tuple(target_weights), tuple(min_returns)
    if not lbs or not weights or not thresholds:
        raise ValueError("parameter grids must not be empty")
    cases: list[MomentumParameterCase] = []
    for lookback in lbs:
        for weight in weights:
            for threshold in thresholds:
                config = TimeSeriesMomentumConfig(
                    lookback=lookback,
                    target_weight=weight,
                    min_return=threshold,
                )
                cases.append(
                    MomentumParameterCase(
                        f"lookback={lookback};target_weight={weight};min_return={threshold}",
                        config,
                    )
                )
    return tuple(cases)


def summarize_parameter_sensitivity(
    cases: Iterable[MomentumParameterCase],
    run: Callable[[TimeSeriesMomentumConfig], BacktestResult],
) -> tuple[SensitivityResult, ...]:
    """Evaluate parameter cases without mutating or reordering the grid."""
    case_list = tuple(cases)
    if not case_list:
        raise ValueError("cases must not be empty")
    return tuple(
        SensitivityResult(case.name, (result := run(case.config)).total_return, result.max_drawdown)
        for case in case_list
    )
