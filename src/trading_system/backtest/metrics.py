"""Deterministic performance metrics for backtest results."""

from __future__ import annotations

from decimal import Decimal

from .results import EquityPoint


def max_drawdown(equity_curve: tuple[EquityPoint, ...]) -> Decimal:
    if not equity_curve:
        raise ValueError("equity_curve must not be empty")
    peak = equity_curve[0].equity
    worst = Decimal("0")
    for point in equity_curve:
        if point.equity > peak:
            peak = point.equity
        drawdown = point.equity / peak - Decimal("1")
        worst = min(worst, drawdown)
    return worst


def simple_returns(equity_curve: tuple[EquityPoint, ...]) -> tuple[Decimal, ...]:
    if len(equity_curve) < 2:
        return ()
    if any(current.equity <= 0 for current in equity_curve):
        raise ValueError("equity must be positive to calculate simple returns")
    return tuple(current.equity / previous.equity - Decimal("1") for previous, current in zip(equity_curve, equity_curve[1:]))
