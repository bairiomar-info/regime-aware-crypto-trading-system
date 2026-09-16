"""Small orchestration entry point for reproducible research experiments."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

from .alpha_evidence import AlphaEvidence
from .experiment_io import write_experiment_result
from .experiment_manifest import ExperimentManifest
from .experiment_result import ExperimentResult, bind_result_to_manifest, fingerprint_experiment_result


def run_reproducible_experiment(
    manifest: ExperimentManifest,
    evidence_factory: Callable[[], AlphaEvidence],
    output_path: str | Path,
) -> tuple[ExperimentResult, str]:
    """Build, bind, fingerprint, and persist one reproducible research result."""
    evidence = evidence_factory()
    result = bind_result_to_manifest(manifest, evidence)
    result_fingerprint = fingerprint_experiment_result(result)
    write_experiment_result(result, output_path)
    return result, result_fingerprint
