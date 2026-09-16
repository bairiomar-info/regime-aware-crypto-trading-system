"""Contracts for fitting research strategies without leaking test data."""

from __future__ import annotations

from typing import Protocol, TypeVar

T = TypeVar("T")


class FitStrategy(Protocol[T]):
    """Factory-style contract: fit on training data, then freeze the result."""

    def fit(self, training_data: T) -> T:
        """Produce frozen strategy parameters using training data only."""

    def freeze(self, fitted: T) -> T:
        """Return an immutable/frozen representation safe for OOS evaluation."""


def fit_and_freeze(strategy: FitStrategy[T], training_data: T) -> T:
    """Fit and freeze in one explicit step; test data is intentionally absent."""
    fitted = strategy.fit(training_data)
    return strategy.freeze(fitted)
