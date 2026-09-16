from decimal import Decimal
import pytest

from trading_system.portfolio.orders import OrderIntent, OrderSide
from trading_system.portfolio.state import AssetBalance, PortfolioState, apply_order_intent


def test_buy_updates_cash_and_asset() -> None:
    state = PortfolioState(Decimal("1000"), ())
    order = OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("400"), "test")
    result = apply_order_intent(state, order, fill_price=Decimal("100"), fee_rate=Decimal("0.01"))
    assert result.cash == Decimal("596")
    assert result.balances == (AssetBalance("BTCUSDT", Decimal("4")),)


def test_sell_requires_owned_quantity() -> None:
    state = PortfolioState(Decimal("100"), (AssetBalance("BTCUSDT", Decimal("1")),))
    order = OrderIntent("BTCUSDT", OrderSide.SELL, Decimal("200"), "test")
    with pytest.raises(ValueError, match="insufficient asset"):
        apply_order_intent(state, order, fill_price=Decimal("100"), fee_rate=Decimal("0"))
