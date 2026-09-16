"""Backtest result models and deterministic performance statistics."""

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
        if not isinstance(self.equity, Decimal) or not self.equity.is_finite() or self.equity < 0:
            raise ValueError("equity must be a finite non-negative Decimal")


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
            if not isinstance(value, Decimal) or not value.is_finite():
                raise ValueError(f"{name} must be a finite Decimal")
        if self.initial_cash <= 0 or self.final_cash < 0 or self.final_quantity < 0 or self.final_equity < 0:
            raise ValueError("invalid backtest result balances")
        if self.max_drawdown < 0 or self.total_return <= Decimal("-1"):
            raise ValueError("invalid return/drawdown values")
        if not self.equity_curve:
            raise ValueError("equity_curve must not be empty")
        for previous, current in zip(self.equity_curve, self.equity_curve[1:]):
            if current.timestamp <= previous.timestamp:
                raise ValueError("equity curve must be strictly chronological")

    @property
    def profit(self) -> Decimal:
        return self.final_equity - self.initial_cash


def calculate_total_return(initial_cash: Decimal, final_equity: Decimal) -> Decimal:
    if not isinstance(initial_cash, Decimal) or not initial_cash.is_finite() or initial_cash <= 0:
        raise ValueError("initial_cash must be positive and finite")
    if not isinstance(final_equity, Decimal) or not final_equity.is_finite() or final_equity < 0:
        raise ValueError("final_equity must be non-negative and finite")
    return final_equity / initial_cash - Decimal("1")


def calculate_max_drawdown(equity_curve: tuple[EquityPoint, ...]) -> Decimal:
    if not equity_curve:
        raise ValueError("equity_curve must not be empty")
    peak = equity_curve[0].equity
    maximum = Decimal("0")
    for point in equity_curve:
        if point.equity > peak:
            peak = point.equity
        if peak > 0:
            drawdown = (peak - point.equity) / peak
            if drawdown > maximum:
                maximum = drawdown
    return maximum
