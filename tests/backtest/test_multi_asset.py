from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_system.backtest.multi_asset import MultiAssetBar, apply_orders
from trading_system.portfolio.orders import OrderIntent, OrderSide
from trading_system.portfolio.state import PortfolioState


def test_batch_orders_apply_deterministically() -> None:
    bar = MultiAssetBar(
        datetime(2026, 1, 1, 1, tzinfo=timezone.utc),
        {"BTCUSDT": Decimal("100"), "ETHUSDT": Decimal("50")},
        {"BTCUSDT": Decimal("101"), "ETHUSDT": Decimal("51")},
    )
    state = PortfolioState(Decimal("1000"), ())
    orders = (
        OrderIntent("ETHUSDT", OrderSide.BUY, Decimal("100"), "test"),
        OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("200"), "test"),
    )
    result = apply_orders(state, orders, bar, fee_rate=Decimal("0"))
    assert result.cash == Decimal("700")
    assert [(b.symbol, b.quantity) for b in result.balances] == [
        ("BTCUSDT", Decimal("2")),
        ("ETHUSDT", Decimal("2")),
    ]


def test_unknown_execution_symbol_is_rejected() -> None:
    bar = MultiAssetBar(
        datetime(2026, 1, 1, 1, tzinfo=timezone.utc),
        {"BTCUSDT": Decimal("100")},
        {"BTCUSDT": Decimal("101")},
    )
    order = OrderIntent("ETHUSDT", OrderSide.BUY, Decimal("100"), "test")
    with pytest.raises(ValueError, match="missing execution price"):
        apply_orders(PortfolioState(Decimal("1000"), ()), (order,), bar, fee_rate=Decimal("0"))
