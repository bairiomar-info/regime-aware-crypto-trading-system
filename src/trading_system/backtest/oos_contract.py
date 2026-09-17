"""Strict train/fit/freeze/OOS evaluation contract."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Generic, TypeVar

from .engine import MarketBar
from .results import BacktestResult
from .walk_forward import WalkForwardWindow

T = TypeVar("T")


@dataclass(frozen=True)
class FrozenOOSModel(Generic[T]):
    """A fitted model whose OOS evaluation input is immutable by contract."""

    parameters: T


def run_strict_oos(
    windows: Sequence[WalkForwardWindow],
    fit: Callable[[tuple[MarketBar, ...]], T],
    evaluate: Callable[[FrozenOOSModel[T], tuple[MarketBar, ...]], BacktestResult],
) -> tuple[BacktestResult, ...]:
    """Fit independently on each train window, freeze, then evaluate on its test window.

    The evaluator receives only the frozen model and the OOS test bars.  It cannot
    receive the training bars through this API, making accidental train/test
    mixing materially harder at the orchestration boundary.
    """
    if not windows:
        raise ValueError("windows must not be empty")
    results: list[BacktestResult] = []
    for window in windows:
        parameters = fit(window.train)
        frozen = FrozenOOSModel(parameters)
        results.append(evaluate(frozen, window.test))
    return tuple(results)
