"""Deterministic walk-forward split utilities with strict temporal boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from trading_system.research.time import require_utc

from .engine import MarketBar


@dataclass(frozen=True)
class WalkForwardWindow:
    train: tuple[MarketBar, ...]
    test: tuple[MarketBar, ...]

    def __post_init__(self) -> None:
        if not self.train or not self.test:
            raise ValueError("train and test windows must not be empty")
        for bars, name in ((self.train, "train"), (self.test, "test")):
            for previous, current in zip(bars, bars[1:]):
                if current.timestamp <= previous.timestamp:
                    raise ValueError(f"{name} bars must be strictly chronological")
        if self.test[0].timestamp <= self.train[-1].timestamp:
            raise ValueError("test window must start strictly after train window")


def make_walk_forward_windows(
    bars: tuple[MarketBar, ...],
    *,
    train_size: int,
    test_size: int,
    step: int | None = None,
) -> tuple[WalkForwardWindow, ...]:
    """Create non-overlapping train/test windows without look-ahead."""
    if train_size <= 0 or test_size <= 0:
        raise ValueError("train_size and test_size must be positive")
    step = test_size if step is None else step
    if step <= 0:
        raise ValueError("step must be positive")
    for previous, current in zip(bars, bars[1:]):
        if current.timestamp <= previous.timestamp:
            raise ValueError("bars must be strictly chronological")
    windows: list[WalkForwardWindow] = []
    start = 0
    while start + train_size + test_size <= len(bars):
        windows.append(WalkForwardWindow(bars[start : start + train_size], bars[start + train_size : start + train_size + test_size]))
        start += step
    return tuple(windows)
