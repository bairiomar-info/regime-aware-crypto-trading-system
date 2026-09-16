"""Backtest result models and performance statistics."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class EquityPoint:
    timestamp: object
    equity: Decimal


@dataclass(frozen=True)
class BacktestResult:
    initial_cash: Decimal
    final_cash: Decimal
    final_quantity: Decimal
    final_equity: Decimal
    total_return: Decimal
    max_drawdown: Decimal
    equity_curve: tuple[EquityPoint, ...]

    @property
    def profit(self) -> Decimal:
        return self.final_equity - self.initial_cash
