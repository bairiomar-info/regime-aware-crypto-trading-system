from decimal import Decimal

import pytest

from trading_system.compliance.classification import AssetCompliance
from trading_system.execution.gate import PreTradeConfig, validate_pre_trade
from trading_system.portfolio.orders import OrderIntent, OrderSide
from trading_system.portfolio.state import PortfolioState
from trading_system.risk.limits import RiskLimits


COMPLIANT_BTC = AssetCompliance("BTCUSDT", Decimal("0.01"))


def test_pre_trade_gate_rejects_forbidden_symbol() -> None:
    state = PortfolioState(Decimal("1000"), ())
    order = OrderIntent("USDT", OrderSide.BUY, Decimal("100"), "test")
    with pytest.raises(ValueError, match="blocked"):
        validate_pre_trade(state, order, Decimal("1"))


def test_pre_trade_gate_rejects_missing_compliance_evidence() -> None:
    state = PortfolioState(Decimal("1000"), ())
    order = OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("100"), "test")
    with pytest.raises(ValueError, match="evidence"):
        validate_pre_trade(state, order, Decimal("100"))


def test_pre_trade_gate_rejects_oversized_order() -> None:
    state = PortfolioState(Decimal("1000"), ())
    order = OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("600"), "test")
    config = PreTradeConfig(risk=RiskLimits(max_order_notional=Decimal("0.5")))
    with pytest.raises(ValueError, match="max_order_notional"):
        validate_pre_trade(state, order, Decimal("100"), config, asset_compliance=COMPLIANT_BTC)


def test_pre_trade_gate_allows_valid_order() -> None:
    state = PortfolioState(Decimal("1000"), ())
    order = OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("400"), "test")
    validate_pre_trade(state, order, Decimal("100"), PreTradeConfig(risk=RiskLimits(max_order_notional=Decimal("0.5"))), asset_compliance=COMPLIANT_BTC)


def test_pre_trade_gate_rejects_mismatched_evidence() -> None:
    state = PortfolioState(Decimal("1000"), ())
    order = OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("100"), "test")
    with pytest.raises(ValueError, match="match"):
        validate_pre_trade(state, order, Decimal("100"), asset_compliance=AssetCompliance("ETHUSDT", Decimal("0.01")))
