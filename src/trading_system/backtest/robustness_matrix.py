"""Execution and aggregation of controlled cost/parameter robustness grids."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from .engine import BacktestConfig, MarketBar
from .parameter_sensitivity import MomentumParameterCase
from .results import BacktestResult
from .robustness import SensitivityResult
from .robustness_report import RobustnessSummary, summarize_results


@dataclass(frozen=True)
class RobustnessCaseResult:
    name: str
    parameter_name: str
    cost_name: str
    result: SensitivityResult


@dataclass(frozen=True)
class RobustnessMatrix:
    cases: tuple[RobustnessCaseResult, ...]
    summary: RobustnessSummary


def run_momentum_cost_matrix(
    bars: Sequence[MarketBar],
    parameter_cases: Sequence[MomentumParameterCase],
    cost_cases: Sequence[tuple[str, BacktestConfig]],
    run: Callable[[Sequence[MarketBar], MomentumParameterCase, BacktestConfig], BacktestResult],
) -> RobustnessMatrix:
    """Run every parameter × cost combination and aggregate only observed results."""
    if not bars:
        raise ValueError("bars must not be empty")
    if not parameter_cases or not cost_cases:
        raise ValueError("parameter_cases and cost_cases must not be empty")
    cases: list[RobustnessCaseResult] = []
    for parameter_case in parameter_cases:
        for cost_name, config in cost_cases:
            result = run(bars, parameter_case, config)
            sensitivity = SensitivityResult(
                name=f"{parameter_case.name}|{cost_name}",
                total_return=result.total_return,
                max_drawdown=result.max_drawdown,
            )
            cases.append(RobustnessCaseResult(sensitivity.name, parameter_case.name, cost_name, sensitivity))
    return RobustnessMatrix(tuple(cases), summarize_results(case.result for case in cases))
