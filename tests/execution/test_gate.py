from decimal import Decimal

import pytest

from trading_system.compliance.spot import SpotComplianceConfig
from trading_system.execution.gate import PreTradeConfig, validate_pre_trade
from trading_system.portfolio.orders import OrderIntent, OrderSide
from trading_system.portfolio.state import PortfolioState
from trading_system.risk.limits import RiskLimits


def test_pre_trade_gate_rejects_forbidden_symbol() -> None:
    state = PortfolioState(Decimal("1000"), ())
    order = OrderIntent("USDT", OrderSide.BUY, Decimal("100"), "test")
    with pytest.raises(ValueError, match="blocked"):
        validate_pre_trade(state, order, Decimal("1"))


def test_pre_trade_gate_rejects_oversized_order() -> None:
    state = PortfolioState(Decimal("1000"), ())
    order = OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("600"), "test")
    config = PreTradeConfig(risk=RiskLimits(max_order_notional=Decimal("0.5")))
    with pytest.raises(ValueError, match="max_order_notional"):
        validate_pre_trade(state, order, Decimal("100"), config)


def test_pre_trade_gate_allows_valid_order() -> None:
    state = PortfolioState(Decimal("1000"), ())
    order = OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("400"), "test")
    validate_pre_trade(state, order, Decimal("100"), PreTradeConfig(risk=RiskLimits(max_order_notional=Decimal("0.5"))))
