"""Portfolio construction constraints."""

from __future__ import annotations

from decimal import Decimal


def validate_target_weights(weights: tuple[tuple[str, Decimal], ...], *, max_total: Decimal = Decimal("1")) -> None:
    if not isinstance(max_total, Decimal) or not max_total.is_finite() or not Decimal("0") < max_total <= Decimal("1"):
        raise ValueError("max_total must be a finite Decimal within (0, 1]")
    seen: set[str] = set()
    total = Decimal("0")
    for symbol, weight in weights:
        if not isinstance(symbol, str) or not symbol or symbol != symbol.upper():
            raise ValueError("symbols must be non-empty uppercase strings")
        if symbol in seen:
            raise ValueError("duplicate target symbol")
        seen.add(symbol)
        if not isinstance(weight, Decimal) or not weight.is_finite() or not Decimal("0") <= weight <= Decimal("1"):
            raise ValueError("weights must be finite Decimals within [0, 1]")
        total += weight
    if total > max_total:
        raise ValueError("target weights exceed portfolio constraint")
