"""Centralized portfolio risk limits for spot order intents."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from trading_system.portfolio.orders import OrderIntent, OrderSide
from trading_system.portfolio.state import PortfolioState


@dataclass(frozen=True)
class RiskLimits:
    max_position_weight: Decimal = Decimal("1")
    max_order_notional: Decimal = Decimal("1")
    max_gross_exposure: Decimal = Decimal("1")

    def __post_init__(self) -> None:
        for name, value in (("max_position_weight", self.max_position_weight), ("max_order_notional", self.max_order_notional), ("max_gross_exposure", self.max_gross_exposure)):
            if not value.is_finite() or value <= 0 or value > 1:
                raise ValueError(f"{name} must be within (0, 1]")


def portfolio_equity(state: PortfolioState, prices: dict[str, Decimal]) -> Decimal:
    equity = state.cash
    for balance in state.balances:
        price = prices.get(balance.symbol)
        if price is None or not price.is_finite() or price <= 0:
            raise ValueError(f"missing or invalid price for {balance.symbol}")
        equity += balance.quantity * price
    return equity


def validate_order_risk(state: PortfolioState, order: OrderIntent, price: Decimal, limits: RiskLimits, *, prices: dict[str, Decimal] | None = None) -> None:
    if not price.is_finite() or price <= 0:
        raise ValueError("price must be positive and finite")
    mark_prices = dict(prices or {})
    mark_prices[order.symbol] = price
    equity = portfolio_equity(state, mark_prices)
    if equity <= 0:
        raise ValueError("portfolio equity must be positive")
    if order.notional > equity * limits.max_order_notional:
        raise ValueError("order exceeds max_order_notional")
    held = next((b.quantity for b in state.balances if b.symbol == order.symbol), Decimal("0"))
    projected = held + order.notional / price if order.side is OrderSide.BUY else max(Decimal("0"), held - order.notional / price)
    if projected * price > equity * limits.max_position_weight:
        raise ValueError("order exceeds max_position_weight")
    current_gross = sum((b.quantity * mark_prices[b.symbol] for b in state.balances), Decimal("0"))
    projected_gross = current_gross + order.notional if order.side is OrderSide.BUY else max(Decimal("0"), current_gross - order.notional)
    if projected_gross > equity * limits.max_gross_exposure:
        raise ValueError("order exceeds max_gross_exposure")
