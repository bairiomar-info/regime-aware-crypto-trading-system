"""Deterministic aggregation and gate inputs for robustness experiments."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from .robustness import SensitivityResult


@dataclass(frozen=True)
class RobustnessSummary:
    case_count: int
    min_return: Decimal
    max_drawdown: Decimal
    median_return: Decimal
    positive_return_fraction: Decimal


def summarize_results(results: Iterable[SensitivityResult]) -> RobustnessSummary:
    """Aggregate sensitivity results without assigning a subjective pass/fail score."""
    values = tuple(results)
    if not values:
        raise ValueError("results must not be empty")
    returns = tuple(item.total_return for item in values)
    ordered = tuple(sorted(returns))
    middle = len(ordered) // 2
    if len(ordered) % 2:
        median = ordered[middle]
    else:
        median = (ordered[middle - 1] + ordered[middle]) / Decimal("2")
    positive = sum(value > 0 for value in returns)
    return RobustnessSummary(
        case_count=len(values),
        min_return=min(returns),
        max_drawdown=max(item.max_drawdown for item in values),
        median_return=median,
        positive_return_fraction=Decimal(positive) / Decimal(len(values)),
    )
