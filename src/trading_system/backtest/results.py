"""Backtest result models and performance statistics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from trading_system.research.time import require_utc


@dataclass(frozen=True)
class EquityPoint:
    timestamp: datetime
    equity: Decimal

    def __post_init__(self) -> None:
        require_utc(self.timestamp, name="equity timestamp")
        if not self.equity.is_finite() or self.equity < 0:
            raise ValueError("equity must be finite and non-negative")


@dataclass(frozen=True)
class BacktestResult:
    initial_cash: Decimal
    final_cash: Decimal
    final_quantity: Decimal
    final_equity: Decimal
    total_return: Decimal
    max_drawdown: Decimal
    equity_curve: tuple[EquityPoint, ...]

    def __post_init__(self) -> None:
        for name, value in (("initial_cash", self.initial_cash), ("final_cash", self.final_cash), ("final_quantity", self.final_quantity), ("final_equity", self.final_equity), ("total_return", self.total_return), ("max_drawdown", self.max_drawdown)):
            if not value.is_finite():
                raise ValueError(f"{name} must be finite")
        if self.initial_cash <= 0 or self.final_cash < 0 or self.final_quantity < 0 or self.final_equity < 0:
            raise ValueError("invalid backtest result balances")
        if not self.equity_curve:
            raise ValueError("equity_curve must not be empty")
        for previous, current in zip(self.equity_curve, self.equity_curve[1:]):
            if current.timestamp <= previous.timestamp:
                raise ValueError("equity curve must be strictly chronological")

    @property
    def profit(self) -> Decimal:
        return self.final_equity - self.initial_cash
