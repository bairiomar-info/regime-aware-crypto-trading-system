from decimal import Decimal

import pytest

from trading_system.portfolio.orders import OrderIntent, OrderSide
from trading_system.portfolio.state import PortfolioState
from trading_system.risk.limits import RiskLimits, validate_order_risk


def test_order_limit_rejects_oversized_order() -> None:
    state = PortfolioState(Decimal("1000"), ())
    order = OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("600"), "test")
    with pytest.raises(ValueError, match="max_order_notional"):
        validate_order_risk(state, order, Decimal("100"), RiskLimits(max_order_notional=Decimal("0.5")))


def test_position_limit_rejects_oversized_target() -> None:
    state = PortfolioState(Decimal("1000"), ())
    order = OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("600"), "test")
    with pytest.raises(ValueError, match="max_position_weight"):
        validate_order_risk(state, order, Decimal("100"), RiskLimits(max_order_notional=Decimal("1"), max_position_weight=Decimal("0.5")))
