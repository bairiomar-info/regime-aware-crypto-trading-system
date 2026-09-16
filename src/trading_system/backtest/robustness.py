"""Deterministic helpers for controlled backtest sensitivity studies."""

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
    if not initial_cash.is_finite() or initial_cash <= 0:
        raise ValueError("initial_cash must be positive and finite")
    fees, slippages = tuple(fee_rates), tuple(slippage_rates)
    if not fees or not slippages:
        raise ValueError("fee_rates and slippage_rates must not be empty")
    rates = (*fees, *slippages)
    if any(not isinstance(value, Decimal) or not value.is_finite() or value < 0 or value >= 1 for value in rates):
        raise ValueError("cost rates must be finite Decimals in [0, 1)")
    return tuple(
        SensitivityCase(
            f"fee={fee};slippage={slippage}",
            BacktestConfig(initial_cash=initial_cash, fee_rate=fee, slippage_rate=slippage),
        )
        for fee in fees
        for slippage in slippages
    )


def summarize_sensitivity(
    cases: Iterable[SensitivityCase], run: Callable[[BacktestConfig], BacktestResult]
) -> tuple[SensitivityResult, ...]:
    """Run each controlled case and preserve input ordering for reproducibility."""
    case_list = tuple(cases)
    if not case_list:
        raise ValueError("cases must not be empty")
    results: list[SensitivityResult] = []
    for case in case_list:
        result = run(case.config)
        results.append(SensitivityResult(case.name, result.total_return, result.max_drawdown))
    return tuple(results)
