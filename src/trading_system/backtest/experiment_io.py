"""Persistence helpers for reproducible experiment artifacts."""

from __future__ import annotations

from pathlib import Path

from .experiment_result import ExperimentResult, serialize_experiment_result


def write_experiment_result(result: ExperimentResult, path: str | Path) -> Path:
    """Write a deterministic JSON artifact, creating parent directories as needed."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(serialize_experiment_result(result) + "\n", encoding="utf-8")
    return target
