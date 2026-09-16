from decimal import Decimal

import pytest

from trading_system.execution.broker import BrokerFill
from trading_system.portfolio.orders import OrderIntent, OrderSide


def test_broker_fill_requires_positive_quantity() -> None:
    order = OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("100"), "test")
    with pytest.raises(ValueError, match="invalid"):
        BrokerFill(order, Decimal("100"), Decimal("0"), Decimal("1"))


def test_broker_fill_is_immutable() -> None:
    order = OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("100"), "test")
    fill = BrokerFill(order, Decimal("100"), Decimal("1"), Decimal("1"))
    assert fill.fee == Decimal("1")
