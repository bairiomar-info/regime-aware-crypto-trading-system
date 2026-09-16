"""Deterministic portfolio rebalance calculations."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .models import Position, TargetPosition


@dataclass(frozen=True)
class Rebalance:
    symbol: str
    current_weight: Decimal
    target_weight: Decimal
    delta_weight: Decimal


def calculate_rebalance(
    positions: tuple[Position, ...],
    targets: tuple[TargetPosition, ...],
    *,
    equity: Decimal,
    prices: dict[str, Decimal],
) -> tuple[Rebalance, ...]:
    """Calculate target-minus-current weights without mutating portfolio state."""
    if not isinstance(equity, Decimal) or not equity.is_finite() or equity <= 0:
        raise ValueError("equity must be a positive finite Decimal")
    current: dict[str, Decimal] = {}
    for position in positions:
        if position.symbol in current:
            raise ValueError("duplicate position symbol")
        if position.symbol not in prices:
            raise ValueError(f"missing price for {position.symbol}")
        price = prices[position.symbol]
        if not isinstance(price, Decimal) or not price.is_finite() or price <= 0:
            raise ValueError("prices must be positive finite Decimals")
        current[position.symbol] = position.quantity * price / equity

    result: list[Rebalance] = []
    seen_targets: set[str] = set()
    for target in targets:
        if target.symbol in seen_targets:
            raise ValueError("duplicate target symbol")
        seen_targets.add(target.symbol)
        current_weight = current.get(target.symbol, Decimal("0"))
        result.append(Rebalance(target.symbol, current_weight, target.target_weight, target.target_weight - current_weight))
    return tuple(result)
