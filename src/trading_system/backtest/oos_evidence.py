"""Convert OOS experiment results into auditable Alpha evidence inputs."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from decimal import Decimal

from .alpha_evidence import AlphaEvidence, evaluate_alpha_evidence
from .alpha_gate import AlphaGateConfig
from .oos_experiments import OOSExperimentResult
from .regime_stability import RegimeOOSResult
from .robustness import SensitivityResult
from .robustness_report import RobustnessSummary, summarize_results


def _validate_experiments(experiments: Sequence[OOSExperimentResult]) -> int:
    if not experiments:
        raise ValueError("experiments must not be empty")
    window_count = len(experiments[0].windows)
    if window_count <= 0:
        raise ValueError("experiments must contain OOS windows")
    if any(len(item.windows) != window_count for item in experiments):
        raise ValueError("all experiments must contain the same OOS window count")
    if len({item.case_name for item in experiments}) != len(experiments):
        raise ValueError("experiment case_name values must be unique")
    return window_count


def summarize_oos_experiments(experiments: Sequence[OOSExperimentResult]) -> RobustnessSummary:
    """Derive the Alpha robustness summary directly from completed OOS experiments."""
    _validate_experiments(experiments)
    sensitivity = tuple(
        SensitivityResult(
            name=experiment.case_name,
            total_return=experiment.compounded_return,
            max_drawdown=experiment.worst_drawdown,
        )
        for experiment in experiments
    )
    return summarize_results(sensitivity)


def evaluate_oos_alpha_evidence(
    summary: RobustnessSummary,
    experiments: Sequence[OOSExperimentResult],
    regimes: Iterable[RegimeOOSResult],
    config: AlphaGateConfig = AlphaGateConfig(),
) -> AlphaEvidence:
    """Build Alpha evidence from completed OOS experiment results and a supplied summary."""
    window_count = _validate_experiments(experiments)
    worst_oos_return = min(window.total_return for experiment in experiments for window in experiment.windows)
    return evaluate_alpha_evidence(
        summary=summary,
        regimes=regimes,
        oos_window_count=window_count * len(experiments),
        worst_oos_return=worst_oos_return,
        config=config,
    )


def evaluate_completed_oos_alpha_evidence(
    experiments: Sequence[OOSExperimentResult],
    regimes: Iterable[RegimeOOSResult],
    config: AlphaGateConfig = AlphaGateConfig(),
) -> AlphaEvidence:
    """Evaluate Alpha evidence using only completed OOS experiment outputs."""
    summary = summarize_oos_experiments(experiments)
    return evaluate_oos_alpha_evidence(
        summary=summary,
        experiments=experiments,
        regimes=regimes,
        config=config,
    )
