"""Deterministic orchestration for multi-case robustness experiments."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from decimal import Decimal

from .engine import BacktestConfig, MarketBar
from .parameter_sensitivity import MomentumParameterCase
from .results import BacktestResult
from .robustness import SensitivityCase


@dataclass(frozen=True)
class ExperimentCase:
    """A named, immutable experiment configuration."""
    name: str
    backtest_config: BacktestConfig
    strategy_config: object | None = None


@dataclass(frozen=True)
class ExperimentResult:
    """Objective outputs associated with one experiment case."""
    name: str
    total_return: Decimal
    max_drawdown: Decimal


def combine_cost_and_parameter_cases(
    cost_cases: Iterable[SensitivityCase],
    parameter_cases: Iterable[MomentumParameterCase],
) -> tuple[ExperimentCase, ...]:
    """Create a deterministic Cartesian product without mutating inputs."""
    costs = tuple(cost_cases)
    parameters = tuple(parameter_cases)
    if not costs or not parameters:
        raise ValueError("cost_cases and parameter_cases must not be empty")
    return tuple(
        ExperimentCase(f"{parameter.name}|{cost.name}", cost.config, parameter.config)
        for parameter in parameters
        for cost in costs
    )


def run_experiment_matrix(
    bars: Sequence[MarketBar],
    cases: Iterable[ExperimentCase],
    run: Callable[[Sequence[MarketBar], ExperimentCase], BacktestResult],
) -> tuple[ExperimentResult, ...]:
    """Run every experiment case in stable order."""
    if not bars:
        raise ValueError("bars must not be empty")
    case_list = tuple(cases)
    if not case_list:
        raise ValueError("cases must not be empty")
    return tuple(
        ExperimentResult(case.name, (result := run(bars, case)).total_return, result.max_drawdown)
        for case in case_list
    )
