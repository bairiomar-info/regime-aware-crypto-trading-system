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

    def __post_init__(self) -> None:
        if self.min_cases < 1:
            raise ValueError("min_cases must be at least 1")
        if not self.min_positive_fraction.is_finite() or not Decimal("0") <= self.min_positive_fraction <= Decimal("1"):
            raise ValueError("min_positive_fraction must be finite and between 0 and 1")
        if not self.max_drawdown.is_finite() or not Decimal("0") <= self.max_drawdown <= Decimal("1"):
            raise ValueError("max_drawdown must be finite and between 0 and 1")


@dataclass(frozen=True)
class AlphaGateResult:
    passed: bool
    sufficient_cases: bool
    sufficient_positive_fraction: bool
    acceptable_drawdown: bool


def evaluate_alpha_gate(summary: RobustnessSummary, config: AlphaGateConfig = AlphaGateConfig()) -> AlphaGateResult:
    """Evaluate evidence against explicit configurable research thresholds."""
    if summary.case_count < 1:
        raise ValueError("summary must contain at least one case")
    for name, value in (
        ("min_return", summary.min_return),
        ("max_drawdown", summary.max_drawdown),
        ("median_return", summary.median_return),
        ("positive_return_fraction", summary.positive_return_fraction),
    ):
        if not value.is_finite():
            raise ValueError(f"summary.{name} must be finite")
    if not Decimal("0") <= summary.positive_return_fraction <= Decimal("1"):
        raise ValueError("summary.positive_return_fraction must be between 0 and 1")
    if summary.max_drawdown < 0:
        raise ValueError("summary.max_drawdown must not be negative")

    sufficient_cases = summary.case_count >= config.min_cases
    sufficient_positive_fraction = summary.positive_return_fraction >= config.min_positive_fraction
    acceptable_drawdown = summary.max_drawdown <= config.max_drawdown
    return AlphaGateResult(
        passed=sufficient_cases and sufficient_positive_fraction and acceptable_drawdown,
        sufficient_cases=sufficient_cases,
        sufficient_positive_fraction=sufficient_positive_fraction,
        acceptable_drawdown=acceptable_drawdown,
    )
