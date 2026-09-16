"""Single mandatory pre-trade execution entry point."""

from __future__ import annotations

from decimal import Decimal

from trading_system.compliance.classification import AssetCompliance
from trading_system.portfolio.orders import OrderIntent
from trading_system.portfolio.state import PortfolioState, apply_order_intent

from .gate import PreTradeConfig, validate_pre_trade


def execute_order(
    state: PortfolioState,
    order: OrderIntent,
    *,
    market_price: Decimal,
    fill_price: Decimal,
    fee_rate: Decimal,
    config: PreTradeConfig = PreTradeConfig(),
    prices: dict[str, Decimal] | None = None,
    asset_compliance: AssetCompliance | None = None,
) -> PortfolioState:
    """Execute one fully-filled spot order only after the mandatory pre-trade gate passes."""
    validate_pre_trade(
        state,
        order,
        market_price,
        config,
        prices=prices,
        asset_compliance=asset_compliance,
    )
    return apply_order_intent(state, order, fill_price=fill_price, fee_rate=fee_rate)
