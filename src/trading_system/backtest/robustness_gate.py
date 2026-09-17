"""Explicit, configurable acceptance gates for research robustness evidence."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .robustness_matrix import RobustnessMatrix


@dataclass(frozen=True)
class RobustnessGateConfig:
    min_positive_case_fraction: Decimal = Decimal("0.60")
    max_worst_drawdown: Decimal = Decimal("0.30")
    min_cases: int = 1


@dataclass(frozen=True)
class RobustnessGateResult:
    passed: bool
    positive_case_fraction: Decimal
    worst_drawdown: Decimal
    case_count: int
    failures: tuple[str, ...]


def evaluate_robustness_gate(
    matrix: RobustnessMatrix,
    config: RobustnessGateConfig = RobustnessGateConfig(),
) -> RobustnessGateResult:
    """Evaluate evidence against explicit thresholds; never rank or select a strategy."""
    case_count = len(matrix.cases)
    failures: list[str] = []
    if case_count < config.min_cases:
        failures.append("insufficient_cases")
    summary = matrix.summary
    positive_fraction = summary.positive_return_fraction
    worst_drawdown = summary.max_drawdown
    if positive_fraction < config.min_positive_case_fraction:
        failures.append("positive_case_fraction_below_threshold")
    if worst_drawdown > config.max_worst_drawdown:
        failures.append("worst_drawdown_above_threshold")
    return RobustnessGateResult(
        passed=not failures,
        positive_case_fraction=positive_fraction,
        worst_drawdown=worst_drawdown,
        case_count=case_count,
        failures=tuple(failures),
    )
