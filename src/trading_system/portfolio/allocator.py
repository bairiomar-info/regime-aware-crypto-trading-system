"""Deterministic portfolio target construction."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from .models import TargetPosition


def equal_weight_targets(
    symbols: tuple[str, ...],
    *,
    as_of: datetime,
    max_weight: Decimal = Decimal("1"),
) -> tuple[TargetPosition, ...]:
    """Allocate equal long-only weights subject to a per-asset cap."""
    if not symbols:
        return ()
    if len(set(symbols)) != len(symbols):
        raise ValueError("symbols must be unique")
    if not max_weight.is_finite() or not Decimal("0") < max_weight <= Decimal("1"):
        raise ValueError("max_weight must be within (0, 1]")
    raw = Decimal("1") / Decimal(len(symbols))
    weight = min(raw, max_weight)
    return tuple(TargetPosition(symbol, weight, as_of) for symbol in symbols)
