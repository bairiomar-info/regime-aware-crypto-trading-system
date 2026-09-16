"""Deterministic slicing of chronological market bars into OOS windows."""

from __future__ import annotations

from collections.abc import Sequence

from .engine import MarketBar
from .walk_forward import WalkForwardWindow


def slice_oos_bars(
    bars: Sequence[MarketBar],
    window: WalkForwardWindow,
) -> tuple[MarketBar, ...]:
    """Return the bars belonging to a walk-forward window's OOS interval."""
    if not bars:
        raise ValueError("bars must not be empty")
    ordered = tuple(bars)
    for previous, current in zip(ordered, ordered[1:]):
        if current.timestamp <= previous.timestamp:
            raise ValueError("bars must be strictly chronological")
    selected = tuple(
        bar for bar in ordered if window.oos_start <= bar.timestamp < window.oos_end
    )
    if not selected:
        raise ValueError("walk-forward OOS window contains no bars")
    return selected
