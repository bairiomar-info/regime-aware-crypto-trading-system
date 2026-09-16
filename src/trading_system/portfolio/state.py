"""Immutable multi-asset spot portfolio state transitions."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .orders import OrderIntent, OrderSide


@dataclass(frozen=True)
class AssetBalance:
    symbol: str
    quantity: Decimal

    def __post_init__(self) -> None:
        if not self.symbol or self.symbol != self.symbol.upper():
            raise ValueError("symbol must be non-empty uppercase")
        if not self.quantity.is_finite() or self.quantity < 0:
            raise ValueError("quantity must be finite and non-negative")


@dataclass(frozen=True)
class PortfolioState:
    cash: Decimal
    balances: tuple[AssetBalance, ...]

    def __post_init__(self) -> None:
        if not self.cash.is_finite() or self.cash < 0:
            raise ValueError("cash must be finite and non-negative")
        symbols = [b.symbol for b in self.balances]
        if len(symbols) != len(set(symbols)):
            raise ValueError("balances must have unique symbols")


def apply_order_intent(state: PortfolioState, order: OrderIntent, *, fill_price: Decimal, fee_rate: Decimal) -> PortfolioState:
    """Apply a fully filled spot order to immutable portfolio state."""
    if not fill_price.is_finite() or fill_price <= 0:
        raise ValueError("fill_price must be positive and finite")
    if not fee_rate.is_finite() or fee_rate < 0 or fee_rate >= 1:
        raise ValueError("fee_rate must be within [0, 1)")
    balances = {balance.symbol: balance.quantity for balance in state.balances}
    quantity = order.notional / fill_price
    fee = order.notional * fee_rate
    if order.side is OrderSide.BUY:
        total_cost = order.notional + fee
        if total_cost > state.cash:
            raise ValueError("insufficient cash")
        balances[order.symbol] = balances.get(order.symbol, Decimal("0")) + quantity
        cash = state.cash - total_cost
    elif order.side is OrderSide.SELL:
        held = balances.get(order.symbol, Decimal("0"))
        if quantity > held:
            raise ValueError("insufficient asset quantity")
        balances[order.symbol] = held - quantity
        cash = state.cash + order.notional - fee
    else:
        raise ValueError("unsupported order side")
    return PortfolioState(cash, tuple(AssetBalance(symbol, qty) for symbol, qty in sorted(balances.items()) if qty > 0))
