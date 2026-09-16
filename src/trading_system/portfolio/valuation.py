"""Point-in-time portfolio valuation helpers."""

from __future__ import annotations

from decimal import Decimal

from .models import Position


def position_value(position: Position, price: Decimal) -> Decimal:
    if not price.is_finite() or price <= 0:
        raise ValueError("price must be positive and finite")
    return position.quantity * price


def portfolio_market_value(positions: tuple[Position, ...], prices: dict[str, Decimal]) -> Decimal:
    seen: set[str] = set()
    total = Decimal("0")
    for position in positions:
        if position.symbol in seen:
            raise ValueError("duplicate position symbol")
        seen.add(position.symbol)
        if position.symbol not in prices:
            raise ValueError(f"missing price for {position.symbol}")
        total += position_value(position, prices[position.symbol])
    return total
