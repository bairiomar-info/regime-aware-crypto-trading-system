"""Chronological multi-asset spot portfolio replay."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from trading_system.portfolio.orders import OrderIntent
from trading_system.portfolio.state import PortfolioState, apply_order_intent
from trading_system.research.time import require_utc


@dataclass(frozen=True)
class MultiAssetBar:
    timestamp: datetime
    opens: dict[str, Decimal]
    closes: dict[str, Decimal]

    def __post_init__(self) -> None:
        require_utc(self.timestamp, name="bar timestamp")
        if not self.opens:
            raise ValueError("bar must contain at least one symbol")
        if set(self.opens) != set(self.closes):
            raise ValueError("opens and closes must contain the same symbols")
        for symbol, price in self.opens.items():
            if not symbol or symbol != symbol.upper():
                raise ValueError("symbols must be uppercase")
            if not price.is_finite() or price <= 0:
                raise ValueError("open prices must be positive and finite")
            close = self.closes[symbol]
            if not close.is_finite() or close <= 0:
                raise ValueError("close prices must be positive and finite")


def apply_orders(state: PortfolioState, orders: tuple[OrderIntent, ...], bar: MultiAssetBar, *, fee_rate: Decimal) -> PortfolioState:
    """Apply a batch deterministically in symbol/side order."""
    if not fee_rate.is_finite() or fee_rate < 0 or fee_rate >= 1:
        raise ValueError("fee_rate must be within [0, 1)")
    current = state
    for order in sorted(orders, key=lambda item: (item.symbol, item.side.value)):
        if order.symbol not in bar.opens:
            raise ValueError(f"missing execution price for {order.symbol}")
        current = apply_order_intent(current, order, fill_price=bar.opens[order.symbol], fee_rate=fee_rate)
    return current
