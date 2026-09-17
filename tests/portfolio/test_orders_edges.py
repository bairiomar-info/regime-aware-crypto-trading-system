from decimal import Decimal

import pytest

from trading_system.portfolio.orders import OrderIntent, OrderSide, order_intents


@pytest.mark.parametrize("notional", [Decimal("0"), Decimal("-1"), Decimal("NaN"), Decimal("Infinity")])
def test_order_intent_requires_positive_finite_notional(notional: Decimal) -> None:
    with pytest.raises(ValueError, match="notional"):
        OrderIntent("BTCUSDT", OrderSide.BUY, notional, "test")


@pytest.mark.parametrize("symbol", ["", "btcusdt", "BTCUSDT "])
def test_order_intent_requires_canonical_symbol(symbol: str) -> None:
    with pytest.raises(ValueError, match="symbol"):
        OrderIntent(symbol, OrderSide.BUY, Decimal("1"), "test")


def test_order_intent_requires_order_side() -> None:
    with pytest.raises(TypeError, match="OrderSide"):
        OrderIntent("BTCUSDT", "BUY", Decimal("1"), "test")  # type: ignore[arg-type]


def test_order_intent_requires_non_empty_reason() -> None:
    with pytest.raises(ValueError, match="reason"):
        OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("1"), "   ")


@pytest.mark.parametrize("equity", [Decimal("0"), Decimal("-1"), Decimal("NaN"), Decimal("Infinity")])
def test_order_intents_requires_positive_equity(equity: Decimal) -> None:
    with pytest.raises(ValueError, match="equity"):
        order_intents((("BTCUSDT", Decimal("0.1")),), equity)


def test_zero_delta_is_not_emitted() -> None:
    assert order_intents((("BTCUSDT", Decimal("0")),), Decimal("1000")) == ()


def test_positive_delta_becomes_buy_notional() -> None:
    orders = order_intents((("BTCUSDT", Decimal("0.25")),), Decimal("1000"))
    assert orders == (OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("250.00"), "rebalance_increase"),)


def test_negative_delta_becomes_sell_notional() -> None:
    orders = order_intents((("BTCUSDT", Decimal("-0.25")),), Decimal("1000"))
    assert orders == (OrderIntent("BTCUSDT", OrderSide.SELL, Decimal("250.00"), "rebalance_decrease"),)


def test_duplicate_symbols_are_rejected() -> None:
    with pytest.raises(ValueError, match="unique"):
        order_intents((("BTCUSDT", Decimal("0.1")), ("BTCUSDT", Decimal("0.2"))), Decimal("1000"))


def test_multiple_non_zero_deltas_preserve_input_order() -> None:
    orders = order_intents((("BTCUSDT", Decimal("0.1")), ("ETHUSDT", Decimal("-0.2"))), Decimal("1000"))
    assert [order.symbol for order in orders] == ["BTCUSDT", "ETHUSDT"]
    assert [order.side for order in orders] == [OrderSide.BUY, OrderSide.SELL]
