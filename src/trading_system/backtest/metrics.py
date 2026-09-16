"""Deterministic Decimal-native performance metrics for research."""

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


def mean_return(returns: tuple[Decimal, ...]) -> Decimal:
    if not returns:
        raise ValueError("returns must not be empty")
    if any(not isinstance(value, Decimal) or not value.is_finite() for value in returns):
        raise ValueError("returns must contain only finite Decimals")
    return sum(returns, Decimal("0")) / Decimal(len(returns))


def volatility(returns: tuple[Decimal, ...]) -> Decimal:
    if not returns:
        raise ValueError("returns must not be empty")
    if len(returns) < 2:
        return Decimal("0")
    mean = mean_return(returns)
    variance = sum((value - mean) ** 2 for value in returns) / Decimal(len(returns) - 1)
    return variance.sqrt()


def sharpe_ratio(returns: tuple[Decimal, ...], risk_free_return: Decimal = Decimal("0")) -> Decimal:
    if not isinstance(risk_free_return, Decimal) or not risk_free_return.is_finite():
        raise ValueError("risk_free_return must be a finite Decimal")
    excess = tuple(value - risk_free_return for value in returns)
    sigma = volatility(excess)
    if sigma == 0:
        return Decimal("0")
    return mean_return(excess) / sigma
