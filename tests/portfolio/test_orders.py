from decimal import Decimal

import pytest

from trading_system.portfolio.orders import OrderSide, order_intents


def test_rebalance_delta_becomes_spot_order_intent() -> None:
    orders = order_intents((("BTCUSDT", Decimal("0.25")), ("ETHUSDT", Decimal("-0.1"))), Decimal("1000"))
    assert [(o.symbol, o.side, o.notional) for o in orders] == [
        ("BTCUSDT", OrderSide.BUY, Decimal("250")),
        ("ETHUSDT", OrderSide.SELL, Decimal("100")),
    ]


def test_zero_delta_creates_no_order() -> None:
    assert order_intents((("BTCUSDT", Decimal("0")),), Decimal("1000")) == ()


def test_duplicate_symbols_are_rejected() -> None:
    with pytest.raises(ValueError, match="unique"):
        order_intents((("BTCUSDT", Decimal("0.1")), ("BTCUSDT", Decimal("0.2"))), Decimal("1000"))


def test_invalid_equity_is_rejected() -> None:
    with pytest.raises(ValueError, match="equity"):
        order_intents((("BTCUSDT", Decimal("0.1")),), Decimal("0"))


def test_non_finite_delta_is_rejected() -> None:
    with pytest.raises(ValueError, match="finite"):
        order_intents((("BTCUSDT", Decimal("NaN")),), Decimal("1000"))


def test_negative_delta_becomes_sell_without_short_intent() -> None:
    orders = order_intents((("BTCUSDT", Decimal("-0.25")),), Decimal("1000"))
    assert orders[0].side is OrderSide.SELL
    assert orders[0].notional == Decimal("250")
