"""Portfolio construction constraints."""

from __future__ import annotations

from decimal import Decimal


def validate_target_weights(weights: tuple[tuple[str, Decimal], ...], *, max_total: Decimal = Decimal("1")) -> None:
    if not max_total.is_finite() or not Decimal("0") < max_total <= Decimal("1"):
        raise ValueError("max_total must be within (0, 1]")
    seen: set[str] = set()
    total = Decimal("0")
    for symbol, weight in weights:
        if symbol in seen:
            raise ValueError("duplicate target symbol")
        seen.add(symbol)
        if not symbol or symbol != symbol.upper():
            raise ValueError("symbols must be uppercase")
        if not weight.is_finite() or not Decimal("0") <= weight <= Decimal("1"):
            raise ValueError("weights must be within [0, 1]")
        total += weight
    if total > max_total:
        raise ValueError("target weights exceed portfolio constraint")
