"""Immutable execution records for auditability and later broker adapters."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from trading_system.portfolio.orders import OrderIntent
from trading_system.research.time import require_utc


@dataclass(frozen=True)
class ExecutionRecord:
    order: OrderIntent
    executed_at: datetime
    market_price: Decimal
    fill_price: Decimal
    filled_quantity: Decimal
    fee: Decimal

    def __post_init__(self) -> None:
        require_utc(self.executed_at, name="executed_at")
        for name, value in (
            ("market_price", self.market_price),
            ("fill_price", self.fill_price),
            ("filled_quantity", self.filled_quantity),
            ("fee", self.fee),
        ):
            if not isinstance(value, Decimal) or not value.is_finite():
                raise TypeError(f"{name} must be a finite Decimal")
        if self.market_price <= 0 or self.fill_price <= 0:
            raise ValueError("market_price and fill_price must be positive")
        if self.filled_quantity <= 0:
            raise ValueError("filled_quantity must be positive")
        if self.fee < 0:
            raise ValueError("fee must be non-negative")
