from decimal import Decimal

import pytest

from trading_system.compliance.classification import AssetCompliance
from trading_system.execution import PreTradeConfig, execute_order
from trading_system.portfolio.orders import OrderIntent, OrderSide
from trading_system.portfolio.state import PortfolioState
from trading_system.risk.limits import RiskLimits


BTC = AssetCompliance("BTCUSDT", Decimal("0.01"))


def test_execute_order_requires_compliance_evidence() -> None:
    state = PortfolioState(Decimal("1000"), ())
    order = OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("100"), "test")
    with pytest.raises(ValueError, match="evidence"):
        execute_order(state, order, market_price=Decimal("100"), fill_price=Decimal("100"), fee_rate=Decimal("0"))


def test_execute_order_applies_fill_after_gate() -> None:
    state = PortfolioState(Decimal("1000"), ())
    order = OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("400"), "test")
    next_state = execute_order(
        state,
        order,
        market_price=Decimal("100"),
        fill_price=Decimal("101"),
        fee_rate=Decimal("0.01"),
        config=PreTradeConfig(risk=RiskLimits(max_order_notional=Decimal("0.5"))),
        asset_compliance=BTC,
    )
    assert next_state.cash == Decimal("596")
    assert next_state.balances[0].quantity == Decimal("400") / Decimal("101")


def test_execute_order_rejects_before_state_mutation() -> None:
    state = PortfolioState(Decimal("1000"), ())
    order = OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("600"), "test")
    with pytest.raises(ValueError, match="max_order_notional"):
        execute_order(
            state,
            order,
            market_price=Decimal("100"),
            fill_price=Decimal("101"),
            fee_rate=Decimal("0.01"),
            config=PreTradeConfig(risk=RiskLimits(max_order_notional=Decimal("0.5"))),
            asset_compliance=BTC,
        )
    assert state.cash == Decimal("1000")
    assert state.balances == ()


def test_invalid_fill_price_cannot_mutate_state() -> None:
    state = PortfolioState(Decimal("1000"), ())
    order = OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("100"), "test")
    for fill_price in (Decimal("0"), Decimal("-1"), Decimal("NaN")):
        with pytest.raises(ValueError, match="fill_price"):
            execute_order(
                state,
                order,
                market_price=Decimal("100"),
                fill_price=fill_price,
                fee_rate=Decimal("0"),
                asset_compliance=BTC,
            )
        assert state.cash == Decimal("1000")
        assert state.balances == ()


def test_invalid_fee_cannot_mutate_state() -> None:
    state = PortfolioState(Decimal("1000"), ())
    order = OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("100"), "test")
    for fee_rate in (Decimal("-0.01"), Decimal("1"), Decimal("NaN")):
        with pytest.raises(ValueError, match="fee_rate"):
            execute_order(
                state,
                order,
                market_price=Decimal("100"),
                fill_price=Decimal("100"),
                fee_rate=fee_rate,
                asset_compliance=BTC,
            )
        assert state.cash == Decimal("1000")
        assert state.balances == ()
