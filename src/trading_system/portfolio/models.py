"""Portfolio target and position models for long-only spot research."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from trading_system.research.time import require_utc


@dataclass(frozen=True)
class Position:
    symbol: str
    quantity: Decimal
    average_price: Decimal

    def __post_init__(self) -> None:
        if not self.symbol or self.symbol != self.symbol.upper():
            raise ValueError("symbol must be a non-empty uppercase identifier")
        if not self.quantity.is_finite() or self.quantity < 0:
            raise ValueError("quantity must be finite and non-negative")
        if not self.average_price.is_finite() or self.average_price <= 0:
            raise ValueError("average_price must be positive and finite")


@dataclass(frozen=True)
class TargetPosition:
    symbol: str
    target_weight: Decimal
    as_of: datetime

    def __post_init__(self) -> None:
        require_utc(self.as_of, name="target as_of")
        if not self.symbol or self.symbol != self.symbol.upper():
            raise ValueError("symbol must be a non-empty uppercase identifier")
        if not self.target_weight.is_finite() or not Decimal("0") <= self.target_weight <= Decimal("1"):
            raise ValueError("target_weight must be within [0, 1]")


@dataclass(frozen=True)
class PortfolioSnapshot:
    as_of: datetime
    cash: Decimal
    equity: Decimal
    positions: tuple[Position, ...]

    def __post_init__(self) -> None:
        require_utc(self.as_of, name="portfolio as_of")
        if not self.cash.is_finite() or self.cash < 0:
            raise ValueError("cash must be finite and non-negative")
        if not self.equity.is_finite() or self.equity <= 0:
            raise ValueError("equity must be positive and finite")
        symbols = [position.symbol for position in self.positions]
        if len(symbols) != len(set(symbols)):
            raise ValueError("portfolio positions must have unique symbols")
