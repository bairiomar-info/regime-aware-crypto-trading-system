"""Research-only fit/freeze lifecycle for walk-forward experiments."""

from __future__ import annotations

from typing import Protocol, TypeVar

from .interface import ResearchStrategy

T = TypeVar("T", bound=ResearchStrategy)


class FittableResearchStrategy(ResearchStrategy, Protocol):
    """Strategy that can be fitted exclusively on a training sample."""

    @classmethod
    def fit(cls, training_data: tuple[object, ...]) -> "FittableResearchStrategy":
        """Create a fitted strategy using training data only."""

    def freeze(self: T) -> T:
        """Return an immutable/frozen strategy for out-of-sample evaluation."""


def fit_and_freeze(strategy_type: type[FittableResearchStrategy], training_data: tuple[object, ...]) -> FittableResearchStrategy:
    """Fit on training data and freeze before any out-of-sample evaluation."""
    if not training_data:
        raise ValueError("training_data must not be empty")
    fitted = strategy_type.fit(training_data)
    if not isinstance(fitted, ResearchStrategy):
        raise TypeError("fit must return a ResearchStrategy")
    return fitted.freeze()
