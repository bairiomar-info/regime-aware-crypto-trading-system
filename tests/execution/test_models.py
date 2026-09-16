from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_system.execution.models import ExecutionRecord
from trading_system.portfolio.orders import OrderIntent, OrderSide


def test_execution_record_requires_utc_and_positive_fill() -> None:
    order = OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("100"), "test")
    record = ExecutionRecord(order, datetime(2026, 1, 1, tzinfo=timezone.utc), Decimal("100"), Decimal("101"), Decimal("0.99"), Decimal("1"))
    assert record.fill_price == Decimal("101")


def test_execution_record_rejects_negative_fee() -> None:
    order = OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("100"), "test")
    with pytest.raises(ValueError, match="fee"):
        ExecutionRecord(order, datetime(2026, 1, 1, tzinfo=timezone.utc), Decimal("100"), Decimal("101"), Decimal("0.99"), Decimal("-1"))
