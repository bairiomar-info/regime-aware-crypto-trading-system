"""Regime-conditioned OOS stability analysis."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from .evaluation import OOSWindowResult


@dataclass(frozen=True)
class RegimeOOSResult:
    regime: str
    window_count: int
    positive_window_fraction: Decimal
    mean_return: Decimal
    worst_return: Decimal
    worst_drawdown: Decimal


def analyze_by_regime(
    windows: Iterable[tuple[str, OOSWindowResult]],
) -> tuple[RegimeOOSResult, ...]:
    """Aggregate OOS evidence by an externally assigned, point-in-time regime label."""
    grouped: dict[str, list[OOSWindowResult]] = {}
    for regime, window in windows:
        if not regime:
            raise ValueError("regime must not be empty")
        grouped.setdefault(regime, []).append(window)
    if not grouped:
        raise ValueError("windows must not be empty")

    results: list[RegimeOOSResult] = []
    for regime in sorted(grouped):
        values = grouped[regime]
        returns = tuple(item.total_return for item in values)
        positive = sum(value > 0 for value in returns)
        results.append(
            RegimeOOSResult(
                regime=regime,
                window_count=len(values),
                positive_window_fraction=Decimal(positive) / Decimal(len(values)),
                mean_return=sum(returns) / Decimal(len(returns)),
                worst_return=min(returns),
                worst_drawdown=max(item.max_drawdown for item in values),
            )
        )
    return tuple(results)
