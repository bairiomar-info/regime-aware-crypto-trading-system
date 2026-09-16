"""Cross-window stability statistics for out-of-sample research."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from statistics import mean, pstdev
from typing import Iterable

from .evaluation import OOSWindowResult


@dataclass(frozen=True)
class OOSStability:
    window_count: int
    positive_window_fraction: Decimal
    mean_return: Decimal
    return_stddev: Decimal
    worst_return: Decimal
    worst_drawdown: Decimal


def analyze_oos_stability(windows: Iterable[OOSWindowResult]) -> OOSStability:
    values = tuple(windows)
    if not values:
        raise ValueError("windows must not be empty")
    returns = tuple(window.total_return for window in values)
    positive = sum(value > 0 for value in returns)
    return OOSStability(
        window_count=len(values),
        positive_window_fraction=Decimal(positive) / Decimal(len(values)),
        mean_return=Decimal(str(mean(returns))),
        return_stddev=Decimal(str(pstdev(returns))),
        worst_return=min(returns),
        worst_drawdown=max(window.max_drawdown for window in values),
    )
