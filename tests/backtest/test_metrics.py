from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from trading_system.backtest.metrics import max_drawdown, mean_return, sharpe_ratio, simple_returns, volatility
from trading_system.backtest.results import EquityPoint


def curve(*values: str) -> tuple[EquityPoint, ...]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return tuple(EquityPoint(start + timedelta(days=i), Decimal(value)) for i, value in enumerate(values))


def test_simple_returns() -> None:
    assert simple_returns(curve("100", "110", "99")) == (Decimal("0.1"), Decimal("-0.1"))


def test_max_drawdown_is_positive_magnitude() -> None:
    assert max_drawdown(curve("100", "120", "90", "110")) == Decimal("0.25")


def test_max_drawdown_is_zero_for_monotonic_curve() -> None:
    assert max_drawdown(curve("100", "110", "120")) == Decimal("0")


def test_mean_and_volatility() -> None:
    returns = (Decimal("0.1"), Decimal("-0.1"))
    assert mean_return(returns) == Decimal("0")
    assert volatility(returns) > 0


def test_sharpe_zero_for_zero_volatility() -> None:
    assert sharpe_ratio((Decimal("0.02"), Decimal("0.02"))) == Decimal("0")


def test_metrics_reject_empty_returns() -> None:
    with pytest.raises(ValueError):
        mean_return(())
