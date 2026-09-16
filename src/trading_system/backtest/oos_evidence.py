"""Convert OOS experiment results into auditable Alpha evidence inputs."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from decimal import Decimal

from .alpha_evidence import AlphaEvidence, evaluate_alpha_evidence
from .alpha_gate import AlphaGateConfig
from .oos_experiments import OOSExperimentResult
from .regime_stability import RegimeOOSResult
from .robustness_report import RobustnessSummary


def evaluate_oos_alpha_evidence(
    summary: RobustnessSummary,
    experiments: Sequence[OOSExperimentResult],
    regimes: Iterable[RegimeOOSResult],
    config: AlphaGateConfig = AlphaGateConfig(),
) -> AlphaEvidence:
    """Build Alpha evidence from completed OOS experiment results."""
    if not experiments:
        raise ValueError("experiments must not be empty")
    window_count = len(experiments[0].windows)
    if window_count <= 0:
        raise ValueError("experiments must contain OOS windows")
    if any(len(item.windows) != window_count for item in experiments):
        raise ValueError("all experiments must contain the same OOS window count")
    worst_oos_return = min(
        (window.total_return for experiment in experiments for window in experiment.windows),
        default=Decimal("0"),
    )
    return evaluate_alpha_evidence(
        summary=summary,
        regimes=regimes,
        oos_window_count=window_count,
        worst_oos_return=worst_oos_return,
        config=config,
    )
