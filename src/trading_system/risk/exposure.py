"""Portfolio exposure calculations used by risk controls."""

from __future__ import annotations

from decimal import Decimal

from trading_system.portfolio.models import Position


def total_exposure(positions: tuple[Position, ...], prices: dict[str, Decimal], equity: Decimal) -> Decimal:
    if not equity.is_finite() or equity <= 0:
        raise ValueError("equity must be positive and finite")
    exposure = Decimal("0")
    seen: set[str] = set()
    for position in positions:
        if position.symbol in seen:
            raise ValueError("duplicate position symbol")
        seen.add(position.symbol)
        price = prices.get(position.symbol)
        if price is None or not price.is_finite() or price <= 0:
            raise ValueError(f"missing or invalid price for {position.symbol}")
        exposure += position.quantity * price / equity
    return exposure
