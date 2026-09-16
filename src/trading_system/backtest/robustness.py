"""Small deterministic helpers for controlled backtest sensitivity studies."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Callable, Iterable

from .engine import BacktestConfig
from .results import BacktestResult


@dataclass(frozen=True)
class SensitivityCase:
    name: str
    config: BacktestConfig


@dataclass(frozen=True)
class SensitivityResult:
    name: str
    total_return: Decimal
    max_drawdown: Decimal


def make_cost_sensitivity_cases(
    *, initial_cash: Decimal, fee_rates: Iterable[Decimal], slippage_rates: Iterable[Decimal]
) -> tuple[SensitivityCase, ...]:
    """Create deterministic fee/slippage cases without changing strategy inputs."""
    cases: list[SensitivityCase] = []
    for fee in fee_rates:
        for slippage in slippage_rates:
            config = BacktestConfig(initial_cash=initial_cash, fee_rate=fee, slippage_rate=slippage)
            cases.append(SensitivityCase(f"fee={fee};slippage={slippage}", config))
    return tuple(cases)


def summarize_sensitivity(
    cases: Iterable[SensitivityCase], run: Callable[[BacktestConfig], BacktestResult]
) -> tuple[SensitivityResult, ...]:
    """Run each controlled case and preserve input ordering for reproducibility."""
    results: list[SensitivityResult] = []
    for case in cases:
        result = run(case.config)
        results.append(SensitivityResult(case.name, result.total_return, result.max_drawdown))
    return tuple(results)
