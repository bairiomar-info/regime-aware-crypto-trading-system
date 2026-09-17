from decimal import Decimal

import pytest

from trading_system.portfolio.orders import OrderIntent, OrderSide
from trading_system.portfolio.state import AssetBalance, PortfolioState
from trading_system.risk.limits import RiskLimits, portfolio_equity, validate_order_risk


def state(cash: str = "1000", *balances: tuple[str, str]) -> PortfolioState:
    return PortfolioState(
        Decimal(cash),
        tuple(AssetBalance(symbol, Decimal(quantity)) for symbol, quantity in balances),
    )


def order(symbol: str, side: OrderSide, notional: str) -> OrderIntent:
    return OrderIntent(symbol, side, Decimal(notional), "test")


@pytest.mark.parametrize("field", ["max_position_weight", "max_order_notional", "max_gross_exposure"])
def test_risk_limits_reject_zero(field: str) -> None:
    values = {"max_position_weight": Decimal("1"), "max_order_notional": Decimal("1"), "max_gross_exposure": Decimal("1")}
    values[field] = Decimal("0")
    with pytest.raises(ValueError, match=field):
        RiskLimits(**values)


@pytest.mark.parametrize("field", ["max_position_weight", "max_order_notional", "max_gross_exposure"])
def test_risk_limits_reject_values_above_one(field: str) -> None:
    values = {"max_position_weight": Decimal("1"), "max_order_notional": Decimal("1"), "max_gross_exposure": Decimal("1")}
    values[field] = Decimal("1.000001")
    with pytest.raises(ValueError, match=field):
        RiskLimits(**values)


@pytest.mark.parametrize("field", ["max_position_weight", "max_order_notional", "max_gross_exposure"])
def test_risk_limits_reject_non_decimal(field: str) -> None:
    values = {"max_position_weight": Decimal("1"), "max_order_notional": Decimal("1"), "max_gross_exposure": Decimal("1")}
    values[field] = 1
    with pytest.raises(ValueError, match=field):
        RiskLimits(**values)


def test_portfolio_equity_rejects_missing_mark_price() -> None:
    with pytest.raises(ValueError, match="missing or invalid price for BTCUSDT"):
        portfolio_equity(state("100", ("BTCUSDT", "1")), {})


@pytest.mark.parametrize("price", [Decimal("0"), Decimal("-1"), Decimal("NaN"), Decimal("Infinity")])
def test_portfolio_equity_rejects_invalid_mark_price(price: Decimal) -> None:
    with pytest.raises(ValueError, match="missing or invalid price for BTCUSDT"):
        portfolio_equity(state("100", ("BTCUSDT", "1")), {"BTCUSDT": price})


@pytest.mark.parametrize("price", [Decimal("0"), Decimal("-1"), Decimal("NaN"), Decimal("Infinity")])
def test_order_risk_rejects_invalid_execution_price(price: Decimal) -> None:
    with pytest.raises(ValueError, match="price must be a positive finite Decimal"):
        validate_order_risk(state(), order("BTCUSDT", OrderSide.BUY, "10"), price, RiskLimits())


def test_order_notional_exactly_at_limit_is_allowed() -> None:
    validate_order_risk(
        state(), order("BTCUSDT", OrderSide.BUY, "500"), Decimal("100"),
        RiskLimits(max_order_notional=Decimal("0.5")),
    )


def test_order_notional_one_unit_over_limit_is_rejected() -> None:
    with pytest.raises(ValueError, match="max_order_notional"):
        validate_order_risk(
            state(), order("BTCUSDT", OrderSide.BUY, "501"), Decimal("100"),
            RiskLimits(max_order_notional=Decimal("0.5")),
        )


def test_position_weight_exactly_at_limit_is_allowed() -> None:
    validate_order_risk(
        state(), order("BTCUSDT", OrderSide.BUY, "500"), Decimal("100"),
        RiskLimits(max_order_notional=Decimal("1"), max_position_weight=Decimal("0.5")),
    )


def test_position_weight_one_unit_over_limit_is_rejected() -> None:
    with pytest.raises(ValueError, match="max_position_weight"):
        validate_order_risk(
            state(), order("BTCUSDT", OrderSide.BUY, "501"), Decimal("100"),
            RiskLimits(max_order_notional=Decimal("1"), max_position_weight=Decimal("0.5")),
        )


def test_gross_exposure_exactly_at_limit_is_allowed() -> None:
    validate_order_risk(
        state(), order("BTCUSDT", OrderSide.BUY, "1000"), Decimal("100"),
        RiskLimits(max_order_notional=Decimal("1"), max_position_weight=Decimal("1"), max_gross_exposure=Decimal("1")),
    )


def test_gross_exposure_one_unit_over_limit_is_rejected() -> None:
    with pytest.raises(ValueError, match="max_gross_exposure"):
        validate_order_risk(
            state(), order("BTCUSDT", OrderSide.BUY, "1001"), Decimal("100"),
            RiskLimits(max_order_notional=Decimal("1"), max_position_weight=Decimal("1"), max_gross_exposure=Decimal("1")),
        )


def test_sell_order_reduces_existing_gross_exposure() -> None:
    validate_order_risk(
        state("0", ("BTCUSDT", "10")), order("BTCUSDT", OrderSide.SELL, "200"), Decimal("100"),
        RiskLimits(max_order_notional=Decimal("1"), max_position_weight=Decimal("1"), max_gross_exposure=Decimal("0.8")),
    )


def test_equity_includes_existing_assets_before_order_limits() -> None:
    validate_order_risk(
        state("100", ("ETHUSDT", "10")), order("BTCUSDT", OrderSide.BUY, "300"), Decimal("100"),
        RiskLimits(max_order_notional=Decimal("0.5")), prices={"ETHUSDT": Decimal("100")},
    )


def test_invalid_price_for_existing_asset_is_rejected_even_for_new_order() -> None:
    with pytest.raises(ValueError, match="missing or invalid price for ETHUSDT"):
        validate_order_risk(
            state("100", ("ETHUSDT", "10")), order("BTCUSDT", OrderSide.BUY, "10"), Decimal("100"),
            RiskLimits(), prices={"ETHUSDT": Decimal("0")},
        )
