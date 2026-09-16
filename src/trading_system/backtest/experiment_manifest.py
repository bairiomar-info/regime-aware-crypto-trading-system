"""Immutable metadata for reproducible research experiments."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ExperimentManifest:
    experiment_id: str
    dataset_id: str
    strategy_id: str
    started_at: datetime
    parameters: tuple[tuple[str, str], ...]
    cost_model_id: str
    walk_forward_id: str

    def __post_init__(self) -> None:
        if not self.experiment_id.strip():
            raise ValueError("experiment_id must not be empty")
        if not self.dataset_id.strip():
            raise ValueError("dataset_id must not be empty")
        if not self.strategy_id.strip():
            raise ValueError("strategy_id must not be empty")
        if not self.cost_model_id.strip():
            raise ValueError("cost_model_id must not be empty")
        if not self.walk_forward_id.strip():
            raise ValueError("walk_forward_id must not be empty")
        if self.started_at.tzinfo is None:
            raise ValueError("started_at must be timezone-aware")
