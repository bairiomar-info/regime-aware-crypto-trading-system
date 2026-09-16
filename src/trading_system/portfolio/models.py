"""Portfolio target and position models for long-only spot research."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from trading_system.research.time import require_utc


def _finite_decimal(value: Decimal, name: str) -> None:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError(f"{name} must be a finite Decimal")


@dataclass(frozen=True)
class Position:
    symbol: str
    quantity: Decimal
    average_price: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.symbol, str) or not self.symbol or self.symbol != self.symbol.upper():
            raise ValueError("symbol must be a non-empty uppercase identifier")
        _finite_decimal(self.quantity, "quantity")
        _finite_decimal(self.average_price, "average_price")
        if self.quantity < 0:
            raise ValueError("quantity must be non-negative")
        if self.average_price <= 0:
            raise ValueError("average_price must be positive")


@dataclass(frozen=True)
class TargetPosition:
    symbol: str
    target_weight: Decimal
    as_of: datetime

    def __post_init__(self) -> None:
        require_utc(self.as_of, name="target as_of")
        if not isinstance(self.symbol, str) or not self.symbol or self.symbol != self.symbol.upper():
            raise ValueError("symbol must be a non-empty uppercase identifier")
        _finite_decimal(self.target_weight, "target_weight")
        if not Decimal("0") <= self.target_weight <= Decimal("1"):
            raise ValueError("target_weight must be within [0, 1]")


@dataclass(frozen=True)
class PortfolioSnapshot:
    as_of: datetime
    cash: Decimal
    equity: Decimal
    positions: tuple[Position, ...]

    def __post_init__(self) -> None:
        require_utc(self.as_of, name="portfolio as_of")
        _finite_decimal(self.cash, "cash")
        _finite_decimal(self.equity, "equity")
        if self.cash < 0:
            raise ValueError("cash must be non-negative")
        if self.equity <= 0:
            raise ValueError("equity must be positive")
        symbols = [position.symbol for position in self.positions]
        if len(symbols) != len(set(symbols)):
            raise ValueError("portfolio positions must have unique symbols")
