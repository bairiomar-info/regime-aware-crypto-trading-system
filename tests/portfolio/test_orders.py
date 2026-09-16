from decimal import Decimal

from trading_system.portfolio.orders import OrderSide, order_intents


def test_rebalance_delta_becomes_spot_order_intent() -> None:
    orders = order_intents((("BTCUSDT", Decimal("0.25")), ("ETHUSDT", Decimal("-0.1"))), Decimal("1000"))
    assert [(o.symbol, o.side, o.notional) for o in orders] == [
        ("BTCUSDT", OrderSide.BUY, Decimal("250")),
        ("ETHUSDT", OrderSide.SELL, Decimal("100")),
    ]


def test_zero_delta_creates_no_order() -> None:
    assert order_intents((("BTCUSDT", Decimal("0")),), Decimal("1000")) == ()
