"""Combine OOS and regime evidence for an auditable Alpha research decision."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from .alpha_gate import AlphaGateConfig, AlphaGateResult, evaluate_alpha_gate
from .regime_stability import RegimeOOSResult
from .robustness_report import RobustnessSummary


@dataclass(frozen=True)
class AlphaEvidence:
    gate: AlphaGateResult
    regimes: tuple[RegimeOOSResult, ...]
    oos_window_count: int
    worst_oos_return: Decimal
    worst_regime_return: Decimal
    all_oos_windows_positive: bool
    all_regimes_positive: bool


def evaluate_alpha_evidence(
    summary: RobustnessSummary,
    regimes: Iterable[RegimeOOSResult],
    oos_window_count: int,
    worst_oos_return: Decimal,
    config: AlphaGateConfig = AlphaGateConfig(),
) -> AlphaEvidence:
    """Produce auditable Alpha evidence without selecting or ranking strategies."""
    if oos_window_count <= 0:
        raise ValueError("oos_window_count must be positive")
    if worst_oos_return is None:
        raise ValueError("worst_oos_return is required")
    regime_values = tuple(regimes)
    if not regime_values:
        raise ValueError("regimes must not be empty")
    gate = evaluate_alpha_gate(summary, config)
    worst_regime_return = min(item.worst_return for item in regime_values)
    return AlphaEvidence(
        gate=gate,
        regimes=regime_values,
        oos_window_count=oos_window_count,
        worst_oos_return=worst_oos_return,
        worst_regime_return=worst_regime_return,
        all_oos_windows_positive=worst_oos_return > 0,
        all_regimes_positive=worst_regime_return > 0,
    )
