from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_system.execution.models import ExecutionRecord
from trading_system.portfolio.orders import OrderIntent, OrderSide


def order() -> OrderIntent:
    return OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("100"), "test")


def test_execution_record_accepts_valid_fill() -> None:
    record = ExecutionRecord(order(), datetime(2026, 1, 1, 1, tzinfo=timezone.utc), Decimal("100"), Decimal("101"), Decimal("0.99"), Decimal("1"))
    assert record.filled_quantity == Decimal("0.99")


def test_execution_record_rejects_non_positive_market_values() -> None:
    for market_price, fill_price in ((Decimal("0"), Decimal("1")), (Decimal("1"), Decimal("0")), (Decimal("-1"), Decimal("1"))):
        with pytest.raises(ValueError):
            ExecutionRecord(order(), datetime(2026, 1, 1, 1, tzinfo=timezone.utc), market_price, fill_price, Decimal("1"), Decimal("0"))


def test_execution_record_rejects_negative_fee_and_fill() -> None:
    for quantity, fee in ((Decimal("0"), Decimal("0")), (Decimal("-1"), Decimal("0")), (Decimal("1"), Decimal("-1"))):
        with pytest.raises(ValueError):
            ExecutionRecord(order(), datetime(2026, 1, 1, 1, tzinfo=timezone.utc), Decimal("1"), Decimal("1"), quantity, fee)


def test_execution_record_rejects_non_utc_timestamp() -> None:
    with pytest.raises(ValueError):
        ExecutionRecord(order(), datetime(2026, 1, 1, 1), Decimal("1"), Decimal("1"), Decimal("1"), Decimal("0"))
