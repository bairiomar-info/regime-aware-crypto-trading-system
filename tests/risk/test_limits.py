from decimal import Decimal

import pytest

from trading_system.portfolio.orders import OrderIntent, OrderSide
from trading_system.portfolio.state import AssetBalance, PortfolioState
from trading_system.risk.limits import RiskLimits, portfolio_equity, validate_order_risk


def test_portfolio_equity_marks_all_assets() -> None:
    state = PortfolioState(Decimal("100"), (AssetBalance("BTCUSDT", Decimal("2")), AssetBalance("ETHUSDT", Decimal("4"))))
    assert portfolio_equity(state, {"BTCUSDT": Decimal("100"), "ETHUSDT": Decimal("50")}) == Decimal("500")


def test_order_limit_uses_total_equity() -> None:
    state = PortfolioState(Decimal("100"), (AssetBalance("ETHUSDT", Decimal("8")),))
    order = OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("250"), "test")
    validate_order_risk(state, order, Decimal("100"), RiskLimits(max_order_notional=Decimal("0.5")), prices={"ETHUSDT": Decimal("50")})


def test_position_limit_rejects_oversized_target() -> None:
    state = PortfolioState(Decimal("1000"), ())
    order = OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("600"), "test")
    with pytest.raises(ValueError, match="max_position_weight"):
        validate_order_risk(state, order, Decimal("100"), RiskLimits(max_order_notional=Decimal("1"), max_position_weight=Decimal("0.5")))


def test_sell_limit_rejects_shortfall() -> None:
    state = PortfolioState(Decimal("1000"), (AssetBalance("BTCUSDT", Decimal("2")),))
    order = OrderIntent("BTCUSDT", OrderSide.SELL, Decimal("300"), "test")
    with pytest.raises(ValueError, match="available spot position"):
        validate_order_risk(state, order, Decimal("100"), RiskLimits())


def test_sell_at_exact_holdings_is_allowed() -> None:
    state = PortfolioState(Decimal("1000"), (AssetBalance("BTCUSDT", Decimal("2")),))
    order = OrderIntent("BTCUSDT", OrderSide.SELL, Decimal("200"), "test")
    validate_order_risk(state, order, Decimal("100"), RiskLimits())


def test_invalid_order_notional_is_rejected() -> None:
    state = PortfolioState(Decimal("1000"), ())
    for notional in (Decimal("0"), Decimal("-1"), Decimal("NaN")):
        order = OrderIntent("BTCUSDT", OrderSide.BUY, notional, "test")
        with pytest.raises(ValueError, match="notional"):
            validate_order_risk(state, order, Decimal("100"), RiskLimits())
