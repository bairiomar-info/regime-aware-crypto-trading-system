from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from trading_system.backtest.results import EquityPoint, calculate_max_drawdown, calculate_total_return


def test_total_return() -> None:
    assert calculate_total_return(Decimal("100"), Decimal("125")) == Decimal("0.25")


def test_max_drawdown() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    curve = tuple(EquityPoint(start + timedelta(days=i), value) for i, value in enumerate((Decimal("100"), Decimal("120"), Decimal("90"), Decimal("110"))))
    assert calculate_max_drawdown(curve) == Decimal("0.25")


def test_total_return_rejects_non_positive_initial() -> None:
    with pytest.raises(ValueError):
        calculate_total_return(Decimal("0"), Decimal("1"))
