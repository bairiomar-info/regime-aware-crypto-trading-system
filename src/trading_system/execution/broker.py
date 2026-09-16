"""Broker abstraction kept separate from research and portfolio logic."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from trading_system.portfolio.orders import OrderIntent


@dataclass(frozen=True)
class BrokerFill:
    order: OrderIntent
    fill_price: Decimal
    filled_quantity: Decimal
    fee: Decimal

    def __post_init__(self) -> None:
        for name, value in (("fill_price", self.fill_price), ("filled_quantity", self.filled_quantity), ("fee", self.fee)):
            if not isinstance(value, Decimal) or not value.is_finite():
                raise TypeError(f"{name} must be a finite Decimal")
        if self.fill_price <= 0 or self.filled_quantity <= 0 or self.fee < 0:
            raise ValueError("invalid broker fill")


class Broker(Protocol):
    """Minimal broker contract; implementations may be paper or exchange-backed."""

    def execute(self, order: OrderIntent) -> BrokerFill:
        """Submit an already-approved order and return its fill."""
