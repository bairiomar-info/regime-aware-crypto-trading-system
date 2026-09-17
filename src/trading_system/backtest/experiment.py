"""Deterministic orchestration for multi-case robustness experiments."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from decimal import Decimal

from trading_system.compliance.classification import AssetCompliance
from trading_system.execution.gate import PreTradeConfig
from trading_system.strategies.interface import ResearchStrategy
from trading_system.strategies.models import StrategyContext

from .engine import BacktestConfig, MarketBar
from .integrated import IntegratedBacktestInput, run_strategy_backtest
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


def run_strategy_experiment_matrix(
    bars: Sequence[MarketBar],
    contexts: Sequence[StrategyContext],
    cases: Iterable[ExperimentCase],
    strategy_factory: Callable[[object | None], ResearchStrategy],
    *,
    asset_compliance: AssetCompliance | None = None,
    pre_trade_config: PreTradeConfig = PreTradeConfig(),
) -> tuple[ExperimentResult, ...]:
    """Run experiment cases through the canonical strategy/backtest path.

    Unlike the generic matrix runner, this entry point does not accept an
    arbitrary backtest callback. Every case is evaluated by
    ``run_strategy_backtest``, preserving the project's causal execution,
    portfolio, risk, and compliance boundary.
    """
    if not bars:
        raise ValueError("bars must not be empty")
    if not contexts:
        raise ValueError("contexts must not be empty")
    case_list = tuple(cases)
    if not case_list:
        raise ValueError("cases must not be empty")

    context_tuple = tuple(contexts)
    results: list[ExperimentResult] = []
    for case in case_list:
        strategy = strategy_factory(case.strategy_config)
        result = run_strategy_backtest(
            strategy,
            IntegratedBacktestInput(
                tuple(bars),
                context_tuple,
                asset_compliance=asset_compliance,
            ),
            case.backtest_config,
            pre_trade_config=pre_trade_config,
        )
        results.append(ExperimentResult(case.name, result.total_return, result.max_drawdown))
    return tuple(results)
