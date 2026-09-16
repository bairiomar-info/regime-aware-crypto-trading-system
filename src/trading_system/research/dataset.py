"""Validated research observations assembled from causal feature outputs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Iterable

from trading_system.features.models import FeatureSnapshot

from .time import require_utc


@dataclass(frozen=True)
class ResearchObservation:
    """One point-in-time research row with optional target return."""

    decision_time: datetime
    features: FeatureSnapshot
    forward_return: Decimal | None = None

    def __post_init__(self) -> None:
        if self.decision_time != self.features.decision_time:
            raise ValueError("decision_time must match feature decision_time")
        require_utc(self.decision_time, name="decision_time")
        if self.forward_return is not None:
            if not isinstance(self.forward_return, Decimal):
                raise TypeError("forward_return must be a Decimal")
            if not self.forward_return.is_finite():
                raise ValueError("forward_return must be finite")


@dataclass(frozen=True)
class ResearchDataset:
    """Immutable, chronologically ordered research observations."""

    observations: tuple[ResearchObservation, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.observations, tuple):
            raise TypeError("observations must be a tuple")
        previous: datetime | None = None
        for observation in self.observations:
            if not isinstance(observation, ResearchObservation):
                raise TypeError("observations must contain ResearchObservation values")
            if previous is not None and observation.decision_time <= previous:
                raise ValueError("observations must have strictly increasing decision_time")
            previous = observation.decision_time

    @classmethod
    def from_observations(cls, observations: Iterable[ResearchObservation]) -> "ResearchDataset":
        return cls(tuple(observations))

    @property
    def timestamps(self) -> tuple[datetime, ...]:
        return tuple(item.decision_time for item in self.observations)
