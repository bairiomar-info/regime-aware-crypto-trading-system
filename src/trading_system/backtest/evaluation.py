"""Deterministic aggregation of out-of-sample walk-forward results."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class OOSWindowResult:
    window_index: int
    total_return: Decimal
    max_drawdown: Decimal

    def __post_init__(self) -> None:
        if self.window_index < 0:
            raise ValueError("window_index must be non-negative")
        for name, value in (("total_return", self.total_return), ("max_drawdown", self.max_drawdown)):
            if not isinstance(value, Decimal) or not value.is_finite():
                raise ValueError(f"{name} must be a finite Decimal")
        if self.total_return <= Decimal("-1") or self.max_drawdown < 0:
            raise ValueError("invalid OOS metrics")


@dataclass(frozen=True)
class OOSSummary:
    windows: tuple[OOSWindowResult, ...]
    compounded_return: Decimal
    worst_drawdown: Decimal


def summarize_oos(windows: tuple[OOSWindowResult, ...]) -> OOSSummary:
    if not windows:
        raise ValueError("windows must not be empty")
    for previous, current in zip(windows, windows[1:]):
        if current.window_index <= previous.window_index:
            raise ValueError("window indices must be strictly increasing")
    compounded = Decimal("1")
    worst = Decimal("0")
    for window in windows:
        compounded *= Decimal("1") + window.total_return
        worst = max(worst, window.max_drawdown)
    return OOSSummary(windows, compounded - Decimal("1"), worst)
