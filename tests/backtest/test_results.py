from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from trading_system.backtest.results import BacktestResult, EquityPoint, calculate_max_drawdown, calculate_total_return


def test_total_return() -> None:
    assert calculate_total_return(Decimal("100"), Decimal("125")) == Decimal("0.25")


def test_max_drawdown() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    curve = tuple(EquityPoint(start + timedelta(days=i), value) for i, value in enumerate((Decimal("100"), Decimal("120"), Decimal("90"), Decimal("110"))))
    assert calculate_max_drawdown(curve) == Decimal("0.25")


def test_total_return_rejects_non_positive_initial() -> None:
    with pytest.raises(ValueError):
        calculate_total_return(Decimal("0"), Decimal("1"))


def test_equity_curve_must_be_strictly_chronological() -> None:
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    points = (EquityPoint(t, Decimal("100")), EquityPoint(t, Decimal("101")))
    with pytest.raises(ValueError, match="chronological"):
        BacktestResult(Decimal("100"), Decimal("101"), Decimal("0"), Decimal("101"), Decimal("0.01"), Decimal("0"), points)


def test_result_rejects_empty_equity_curve() -> None:
    with pytest.raises(ValueError, match="equity_curve"):
        BacktestResult(Decimal("100"), Decimal("100"), Decimal("0"), Decimal("100"), Decimal("0"), Decimal("0"), ())


def test_drawdown_never_exceeds_one() -> None:
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    curve = tuple(EquityPoint(t + timedelta(days=i), value) for i, value in enumerate((Decimal("100"), Decimal("0"), Decimal("50"))))
    assert calculate_max_drawdown(curve) == Decimal("1")


def test_total_return_allows_complete_loss() -> None:
    assert calculate_total_return(Decimal("100"), Decimal("0")) == Decimal("-1")
