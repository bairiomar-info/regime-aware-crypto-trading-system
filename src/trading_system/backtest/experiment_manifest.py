"""Immutable metadata for reproducible research experiments."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json


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
        for field_name in ("experiment_id", "dataset_id", "strategy_id", "cost_model_id", "walk_forward_id"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be empty")
        if self.started_at.tzinfo is None:
            raise ValueError("started_at must be timezone-aware")

    def canonical_payload(self) -> dict[str, object]:
        return {
            "experiment_id": self.experiment_id,
            "dataset_id": self.dataset_id,
            "strategy_id": self.strategy_id,
            "started_at": self.started_at.isoformat(),
            "parameters": list(self.parameters),
            "cost_model_id": self.cost_model_id,
            "walk_forward_id": self.walk_forward_id,
        }

    def fingerprint(self) -> str:
        payload = json.dumps(self.canonical_payload(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
