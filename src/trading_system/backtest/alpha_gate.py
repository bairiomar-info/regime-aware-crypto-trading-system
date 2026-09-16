"""Explicit, configurable evidence gate for research-stage Alpha readiness."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .robustness_report import RobustnessSummary


@dataclass(frozen=True)
class AlphaGateConfig:
    min_cases: int = 5
    min_positive_fraction: Decimal = Decimal("0.60")
    max_drawdown: Decimal = Decimal("0.30")


@dataclass(frozen=True)
class AlphaGateResult:
    passed: bool
    sufficient_cases: bool
    sufficient_positive_fraction: bool
    acceptable_drawdown: bool


def evaluate_alpha_gate(summary: RobustnessSummary, config: AlphaGateConfig = AlphaGateConfig()) -> AlphaGateResult:
    """Evaluate evidence against explicit configurable research thresholds."""
    sufficient_cases = summary.case_count >= config.min_cases
    sufficient_positive_fraction = summary.positive_return_fraction >= config.min_positive_fraction
    acceptable_drawdown = summary.max_drawdown <= config.max_drawdown
    return AlphaGateResult(
        passed=sufficient_cases and sufficient_positive_fraction and acceptable_drawdown,
        sufficient_cases=sufficient_cases,
        sufficient_positive_fraction=sufficient_positive_fraction,
        acceptable_drawdown=acceptable_drawdown,
    )
