"""Deterministic access to market bars belonging to an OOS window."""

from __future__ import annotations

from collections.abc import Sequence

from .engine import MarketBar
from .walk_forward import WalkForwardWindow


def slice_oos_bars(
    bars: Sequence[MarketBar],
    window: WalkForwardWindow,
) -> tuple[MarketBar, ...]:
    """Return the exact test bars from an existing walk-forward window."""
    if not bars:
        raise ValueError("bars must not be empty")
    ordered = tuple(bars)
    for previous, current in zip(ordered, ordered[1:]):
        if current.timestamp <= previous.timestamp:
            raise ValueError("bars must be strictly chronological")
    expected = window.test
    if not expected:
        raise ValueError("walk-forward OOS window must not be empty")
    start = expected[0].timestamp
    end = expected[-1].timestamp
    selected = tuple(bar for bar in ordered if start <= bar.timestamp <= end)
    if selected != expected:
        raise ValueError("walk-forward OOS bars do not match source bars")
    return selected
