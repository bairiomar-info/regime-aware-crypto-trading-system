from decimal import Decimal

import pytest

from trading_system.portfolio.orders import OrderIntent, OrderSide
from trading_system.portfolio.state import AssetBalance, PortfolioState, apply_order_intent


def order(side: OrderSide, notional: str = "100") -> OrderIntent:
    return OrderIntent("BTCUSDT", side, Decimal(notional), "test")


def test_negative_cash_is_rejected() -> None:
    with pytest.raises(ValueError, match="cash"):
        PortfolioState(Decimal("-1"), ())


def test_duplicate_balances_are_rejected() -> None:
    with pytest.raises(ValueError, match="unique"):
        PortfolioState(Decimal("100"), (AssetBalance("BTCUSDT", Decimal("1")), AssetBalance("BTCUSDT", Decimal("2"))))

@pytest.mark.parametrize("quantity", [Decimal("-1"), Decimal("NaN"), Decimal("Infinity")])
def test_asset_balance_requires_finite_non_negative_quantity(quantity: Decimal) -> None:
    with pytest.raises(ValueError, match="quantity"):
        AssetBalance("BTCUSDT", quantity)

@pytest.mark.parametrize("price", [Decimal("0"), Decimal("-1"), Decimal("NaN"), Decimal("Infinity")])
def test_apply_order_rejects_invalid_fill_price(price: Decimal) -> None:
    with pytest.raises(ValueError, match="fill_price"):
        apply_order_intent(PortfolioState(Decimal("1000"), ()), order(OrderSide.BUY), fill_price=price, fee_rate=Decimal("0"))

@pytest.mark.parametrize("fee", [Decimal("-0.01"), Decimal("1"), Decimal("NaN"), Decimal("Infinity")])
def test_apply_order_rejects_invalid_fee_rate(fee: Decimal) -> None:
    with pytest.raises(ValueError, match="fee_rate"):
        apply_order_intent(PortfolioState(Decimal("1000"), ()), order(OrderSide.BUY), fill_price=Decimal("100"), fee_rate=fee)


def test_buy_rejects_insufficient_cash() -> None:
    with pytest.raises(ValueError, match="insufficient cash"):
        apply_order_intent(PortfolioState(Decimal("50"), ()), order(OrderSide.BUY), fill_price=Decimal("100"), fee_rate=Decimal("0"))


def test_sell_rejects_insufficient_asset_quantity() -> None:
    state = PortfolioState(Decimal("0"), (AssetBalance("BTCUSDT", Decimal("0.5")),))
    with pytest.raises(ValueError, match="insufficient asset quantity"):
        apply_order_intent(state, order(OrderSide.SELL), fill_price=Decimal("100"), fee_rate=Decimal("0"))


def test_buy_applies_fee_and_quantity() -> None:
    state = apply_order_intent(PortfolioState(Decimal("1000"), ()), order(OrderSide.BUY), fill_price=Decimal("100"), fee_rate=Decimal("0.01"))
    assert state.cash == Decimal("899")
    assert state.balances == (AssetBalance("BTCUSDT", Decimal("1")),)


def test_sell_removes_zero_balance() -> None:
    state = PortfolioState(Decimal("0"), (AssetBalance("BTCUSDT", Decimal("1")),))
    result = apply_order_intent(state, order(OrderSide.SELL), fill_price=Decimal("100"), fee_rate=Decimal("0"))
    assert result.cash == Decimal("100")
    assert result.balances == ()
